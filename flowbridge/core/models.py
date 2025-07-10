from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ProcessingStage(Enum):
    """Enum representing different stages of request processing."""
    VALIDATION = auto()
    FILTERING = auto()
    ROUTING = auto()
    COMPLETE = auto()


class FilteringSummary(BaseModel):
    """Summary of filtering decision for HTTP responses."""
    
    rules_evaluated: int = Field(..., description="Number of rules evaluated")
    default_action_applied: bool = Field(
        ..., description="Whether default action was applied"
    )
    matched_rules: Optional[List[str]] = Field(
        None, description="List of rules that matched"
    )
    
    @classmethod
    def from_filtering_context(cls, filtering_context) -> 'FilteringSummary':
        """Create FilteringSummary from FilteringContext for HTTP responses.
        
        Args:
            filtering_context: FilteringContext instance
            
        Returns:
            FilteringSummary for HTTP response
        """
        matched_rules = [
            result["field"] 
            for result in filtering_context.rule_results 
            if result.get("passed", False)
        ]
        
        return cls(
            rules_evaluated=filtering_context.rules_evaluated,
            default_action_applied=filtering_context.default_action_applied,
            matched_rules=matched_rules if matched_rules else None
        )


class DroppedResponse(BaseModel):
    """Response model for dropped requests."""
    
    status: str = Field("processed", description="Processing status")
    result: str = Field("dropped", description="Processing result")
    request_id: str = Field(..., description="Request correlation ID")
    filtering_summary: FilteringSummary = Field(
        ..., description="Summary of filtering decision"
    )


class ProcessingResult:
    """Result of request processing through the pipeline."""
    
    def __init__(
        self,
        request_context,  # RequestContext from context.py
        is_dropped: bool,
        filtering_summary: Optional[FilteringSummary] = None
    ):
        """Initialize processing result.
        
        Args:
            request_context: RequestContext instance from context.py
            is_dropped: Whether request was dropped by filtering
            filtering_summary: Summary of filtering decision if available
        """
        self.request_context = request_context
        self.is_dropped = is_dropped
        self.filtering_summary = filtering_summary
    
    def to_response(self) -> Union[DroppedResponse, Dict[str, Any]]:
        """Convert processing result to HTTP response.
        
        Returns:
            Response model for dropped requests or dict for passed requests
        """
        if self.is_dropped and self.filtering_summary:
            return DroppedResponse(
                request_id=str(self.request_context.request_id),
                filtering_summary=self.filtering_summary
            )
        
        # For passed requests, we'll handle the response in Stage 5
        return {
            "status": "processing",
            "request_id": str(self.request_context.request_id),
            "message": "Request passed filtering, proceeding to routing"
        }
