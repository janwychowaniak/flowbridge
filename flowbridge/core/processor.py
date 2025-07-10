from typing import Dict, Any
from loguru import logger
from flask import request

from .models import (
    ProcessingResult,
    ProcessingStage,
    FilteringSummary,
)
from .context import FilteringContext
from .filters import FilterEngine
from ..config.models import ConfigModel
from ..utils.errors import ValidationError as AppValidationError



class ProcessingPipeline:
    """Main orchestrator for request processing flow."""


    def __init__(self, config: ConfigModel):
        """Initialize the processing pipeline.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.filter_engine = FilterEngine(config.filtering)


    def validate_request_payload(
        self, 
        payload: Any
    ) -> Dict[str, Any]:
        """Validate incoming webhook request payload.
        
        Args:
            payload: Raw JSON payload (any valid JSON)
            
        Returns:
            Dict[str, Any]: Validated payload as dictionary
            
        Raises:
            ValidationError: If payload is not valid JSON or not a dictionary
        """
        # Accept any valid JSON, but require it to be a dictionary for filtering
        if not isinstance(payload, dict):
            raise AppValidationError(
                "Payload must be a JSON object (dictionary)",
                context={"payload_type": type(payload).__name__}
            )
        
        # No schema validation - accept any dictionary structure
        return payload


    def process_webhook_request(
        self, 
        payload: Any,
        request_context=None
    ) -> ProcessingResult:
        """Process a webhook request through the pipeline.
        
        Args:
            payload: Raw JSON payload from request (any valid JSON)
            request_context: Optional RequestContext (uses Flask request.ctx if None)
            
        Returns:
            ProcessingResult: Result of request processing
        """
        # Use existing RequestContext from middleware if available
        if request_context is None:
            request_context = getattr(request, 'ctx', None)
            if request_context is None:
                raise RuntimeError("RequestContext not available - middleware not properly configured")
        
        # Add payload to request metadata
        request_context.add_metadata("payload", payload)
        
        try:
            # Stage 1: Validation (minimal - just ensure it's a dict)
            logger.info(
                "Starting request processing",
                request_id=str(request_context.request_id),
                stage=ProcessingStage.VALIDATION.name
            )
            request_context.mark_stage("validation")
            validated_payload = self.validate_request_payload(payload)
            
            # Stage 2: Filtering
            logger.info(
                "Request validation successful, proceeding to filtering",
                request_id=str(request_context.request_id),
                stage=ProcessingStage.FILTERING.name
            )
            request_context.mark_stage("filtering")
            filter_result = self.filter_engine.evaluate_payload(validated_payload)
            
            # Update filtering context using existing method
            request_context.filtering = FilteringContext.from_filter_result(filter_result)
            
            # Create filtering summary for HTTP response
            filtering_summary = FilteringSummary.from_filtering_context(
                request_context.filtering
            )
            
            # Determine if request should be dropped
            is_dropped = not filter_result.passed
            
            if is_dropped:
                logger.info(
                    "Request dropped by filtering rules",
                    request_id=str(request_context.request_id),
                    rules_evaluated=filter_result.rules_evaluated,
                    default_action_applied=filter_result.default_action_applied
                )
                return ProcessingResult(
                    request_context=request_context,
                    is_dropped=True,
                    filtering_summary=filtering_summary
                )
            
            # Request passed filtering
            logger.info(
                "Request passed filtering rules, proceeding to routing",
                request_id=str(request_context.request_id),
                rules_evaluated=filter_result.rules_evaluated,
                matched_rules=filtering_summary.matched_rules
            )
            request_context.mark_stage("routing_preparation")
            return ProcessingResult(
                request_context=request_context,
                is_dropped=False,
                filtering_summary=filtering_summary
            )
            
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
            request_context.add_metadata("error", error_details)
            logger.error(
                "Error processing webhook request",
                request_id=str(request_context.request_id),
                **error_details
            )
            raise
