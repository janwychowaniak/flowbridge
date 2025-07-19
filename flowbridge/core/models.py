from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .context import FilteringContext, RoutingContext, ForwardingContext
from .forwarder import ForwardingResult


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ProcessingStage(Enum):
    """Enum representing different stages of request processing."""
    VALIDATION = auto()
    FILTERING = auto()
    ROUTING = auto()
    COMPLETE = auto()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stage-specific Summary Models
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    def from_filtering_context(cls, filtering_context: FilteringContext) -> 'FilteringSummary':
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


class RoutingSummary(BaseModel):
    """Summary of routing decision for HTTP responses."""
    
    field_path: Optional[str] = Field(None, description="Field path used for routing")
    matched_value: Optional[str] = Field(None, description="Value that matched routing rule")
    destination_url: Optional[str] = Field(None, description="Destination URL determined by routing")
    rule_index: Optional[int] = Field(None, description="Index of matched routing rule")
    total_rules: int = Field(0, description="Total number of routing rules evaluated")
    success: bool = Field(False, description="Whether routing was successful")
    
    @classmethod
    def from_routing_context(cls, routing_context: RoutingContext) -> 'RoutingSummary':
        """Create RoutingSummary from RoutingContext for HTTP responses.
        
        Args:
            routing_context: RoutingContext instance
            
        Returns:
            RoutingSummary for HTTP response
        """
        return cls(
            field_path=routing_context.field_path,
            matched_value=routing_context.matched_value,
            destination_url=routing_context.destination_url,
            rule_index=routing_context.rule_index,
            total_rules=routing_context.total_rules,
            success=routing_context.success
        )


class ForwardingSummary(BaseModel):
    """Summary of forwarding operation for HTTP responses."""
    
    destination_url: Optional[str] = Field(None, description="URL that was called")
    success: bool = Field(False, description="Whether forwarding was successful")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error_type: Optional[str] = Field(None, description="Type of forwarding error if failed")
    status_code: Optional[int] = Field(None, description="HTTP status code from destination")
    content_length: Optional[int] = Field(None, description="Size of response content in bytes")
    
    @classmethod
    def from_forwarding_context(cls, forwarding_context: ForwardingContext) -> 'ForwardingSummary':
        """Create ForwardingSummary from ForwardingContext for HTTP responses.
        
        Args:
            forwarding_context: ForwardingContext instance
            
        Returns:
            ForwardingSummary for HTTP response
        """
        return cls(
            destination_url=forwarding_context.destination_url,
            success=forwarding_context.success,
            response_time_ms=forwarding_context.response_time_ms,
            error_type=forwarding_context.error_type,
            status_code=forwarding_context.status_code,
            content_length=forwarding_context.content_length
        )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Response Models
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class DestinationResponse(BaseModel):
    """Data structure representing response from destination URL."""
    
    status_code: int = Field(..., description="HTTP status code from destination")
    headers: Dict[str, str] = Field(..., description="Response headers from destination")
    content: Optional[str] = Field(None, description="Response body from destination")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    destination_url: str = Field(..., description="URL that was called")
    
    @classmethod
    def from_forwarding_result(cls, forwarding_result: ForwardingResult) -> 'DestinationResponse':
        """Create DestinationResponse from ForwardingResult.
        
        Args:
            forwarding_result: ForwardingResult instance
            
        Returns:
            DestinationResponse containing destination's response data
        """
        # Convert bytes content to string if available
        content = None
        if forwarding_result.content:
            try:
                content = forwarding_result.content.decode('utf-8')
            except UnicodeDecodeError:
                content = "<binary content>"
        
        return cls(
            status_code=forwarding_result.status_code,
            headers=forwarding_result.headers or {},
            content=content,
            response_time_ms=forwarding_result.response_time_ms,
            destination_url=forwarding_result.destination_url
        )


class DroppedResponse(BaseModel):
    """Response for requests dropped by filtering rules."""
    
    status: str = Field("processed", description="Processing status")
    result: str = Field("dropped", description="Processing result") 
    request_id: str = Field(..., description="Request correlation ID")
    filtering_summary: FilteringSummary = Field(..., description="Summary of filtering decision")


class RoutingFailureResponse(BaseModel):
    """Response for requests that failed during routing stage."""
    
    status: str = Field("failed", description="Processing status")
    result: str = Field("routing_failed", description="Processing result")
    request_id: str = Field(..., description="Request correlation ID")
    filtering_summary: FilteringSummary = Field(..., description="Summary of filtering decision")
    routing_summary: RoutingSummary = Field(..., description="Summary of routing decision")
    error_message: str = Field(..., description="Error message describing routing failure")


class ForwardingFailureResponse(BaseModel):
    """Response for requests that failed during forwarding stage."""
    
    status: str = Field("failed", description="Processing status")
    result: str = Field("forwarding_failed", description="Processing result")
    request_id: str = Field(..., description="Request correlation ID")
    filtering_summary: FilteringSummary = Field(..., description="Summary of filtering decision")
    routing_summary: RoutingSummary = Field(..., description="Summary of routing decision")
    forwarding_summary: ForwardingSummary = Field(..., description="Summary of forwarding attempt")


class RoutedResponse(BaseModel):
    """Response for requests successfully routed and forwarded."""
    
    status: str = Field("forwarded", description="Processing status")
    result: str = Field("success", description="Processing result")
    request_id: str = Field(..., description="Request correlation ID")
    filtering_summary: FilteringSummary = Field(..., description="Summary of filtering decision")
    routing_summary: RoutingSummary = Field(..., description="Summary of routing decision")
    forwarding_summary: ForwardingSummary = Field(..., description="Summary of forwarding operation")
    destination_response: DestinationResponse = Field(..., description="Response from destination URL")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Processing Result Model
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ProcessingResult:
    """Result of request processing through the pipeline."""
    
    def __init__(
        self,
        request_context,  # RequestContext from context.py
        is_dropped: bool = False,
        filtering_summary: Optional[FilteringSummary] = None,
        routing_summary: Optional[RoutingSummary] = None,
        destination_response: Optional[DestinationResponse] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        stage: ProcessingStage = ProcessingStage.COMPLETE
    ):
        """Initialize processing result.
        
        Args:
            request_context: RequestContext instance from context.py
            is_dropped: Whether request was dropped by filtering
            filtering_summary: Summary of filtering decision if available
            routing_summary: Summary of routing decision if available  
            destination_response: Response data from destination if forwarding successful
            error_message: Error message if processing failed
            error_type: Type of error if processing failed
            stage: Processing stage where result was generated
        """
        self.request_context = request_context
        self.is_dropped = is_dropped
        self.filtering_summary = filtering_summary
        self.routing_summary = routing_summary
        self.destination_response = destination_response
        self.error_message = error_message
        self.error_type = error_type
        self.stage = stage
    
    def to_response(self) -> Union[DroppedResponse, RoutedResponse, RoutingFailureResponse, ForwardingFailureResponse, Dict[str, Any]]:
        """Convert processing result to HTTP response.
        
        Returns:
            Appropriate response model based on processing outcome
        """
        request_id = str(self.request_context.request_id)
        
        # Request was dropped by filtering
        if self.is_dropped and self.filtering_summary:
            return DroppedResponse(
                request_id=request_id,
                filtering_summary=self.filtering_summary
            )
        
        # Successful routing and forwarding
        if (self.routing_summary and self.routing_summary.success and 
            self.destination_response and self.filtering_summary):
            return RoutedResponse(
                request_id=request_id,
                filtering_summary=self.filtering_summary,
                routing_summary=self.routing_summary,
                forwarding_summary=ForwardingSummary.from_forwarding_context(self.request_context.forwarding),
                destination_response=self.destination_response
            )
        
        # Routing failed (no matching rules, field extraction errors)
        if (self.routing_summary and not self.routing_summary.success and 
            self.error_message and self.filtering_summary):
            return RoutingFailureResponse(
                request_id=request_id,
                filtering_summary=self.filtering_summary,
                routing_summary=self.routing_summary,
                error_message=self.error_message
            )
        
        # Forwarding failed (network errors, timeouts)
        if (self.routing_summary and self.routing_summary.success and 
            self.error_message and self.error_type and self.filtering_summary):
            return ForwardingFailureResponse(
                request_id=request_id,
                filtering_summary=self.filtering_summary,
                routing_summary=self.routing_summary,
                forwarding_summary=ForwardingSummary.from_forwarding_context(self.request_context.forwarding)
            )
        
        # Fallback for unknown states (should not happen in normal operation)
        return {
            "status": "processing",
            "request_id": request_id,
            "message": "Request processed but response type unclear",
            "stage": self.stage.name
        }
