from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from uuid import UUID, uuid4

from .filters import FilterResult
from .router import RoutingResult
from .forwarder import ForwardingResult


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stage-specific Context Dataclasses
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@dataclass
class FilteringContext:
    """Tracks filtering results for a request."""
    passed: bool = False
    rules_evaluated: int = 0
    rule_results: List[Dict[str, Any]] = field(default_factory=list)
    default_action_applied: bool = False
    error_message: Optional[str] = None

    @classmethod
    def from_filter_result(cls, result: FilterResult) -> 'FilteringContext':
        """Create FilteringContext from FilterResult."""
        return cls(
            passed=result.passed,
            rules_evaluated=result.rules_evaluated,
            rule_results=result.rule_results,
            default_action_applied=result.default_action_applied,
            error_message=result.error_message
        )

@dataclass
class RoutingContext:
    """Tracks routing results for a request."""
    destination_url: Optional[str] = None
    matched_value: Optional[str] = None
    field_path: Optional[str] = None
    rule_index: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    total_rules: int = 0
    evaluated_rules: int = 0

    @classmethod
    def from_routing_result(cls, result: RoutingResult, total_rules: int = 0) -> 'RoutingContext':
        """Create RoutingContext from RoutingResult.
        
        Args:
            result: RoutingResult instance from router.py
            total_rules: Total number of routing rules configured
            
        Returns:
            RoutingContext instance
        """
        return cls(
            destination_url=result.destination_url,
            matched_value=result.matched_value,
            field_path=result.field_path,
            rule_index=result.rule_index,
            success=result.success,
            error_message=result.error_message,
            total_rules=total_rules,
            evaluated_rules=result.rule_index + 1 if result.rule_index is not None else total_rules
        )

@dataclass
class ForwardingContext:
    """Tracks forwarding results for a request."""
    destination_url: Optional[str] = None
    success: bool = False
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    content_length: Optional[int] = None

    @classmethod
    def from_forwarding_result(cls, result: ForwardingResult) -> 'ForwardingContext':
        """Create ForwardingContext from ForwardingResult.
        
        Args:
            result: ForwardingResult instance from forwarder.py
            
        Returns:
            ForwardingContext instance
        """
        content_length = None
        if result.content:
            content_length = len(result.content)
            
        return cls(
            destination_url=result.destination_url,
            success=result.success,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
            error_message=result.error_message,
            error_type=result.error_type,
            content_length=content_length
        )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Full Request Context Dataclass
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@dataclass
class RequestContext:
    """
    Tracks request processing through the system.
    
    Attributes:
        request_id: Unique identifier for the request
        timestamp: When the request was received
        metadata: Additional request-specific data
        processing_stages: Track which stages have processed the request
    """
    request_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_stages: Dict[str, datetime] = field(default_factory=dict)
    filtering: FilteringContext = field(default_factory=FilteringContext)
    routing: RoutingContext = field(default_factory=RoutingContext)
    forwarding: ForwardingContext = field(default_factory=ForwardingContext)

    def mark_stage(self, stage_name: str) -> None:
        """Mark a processing stage as completed."""
        self.processing_stages[stage_name] = datetime.now(timezone.utc)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the request context."""
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "request_id": str(self.request_id),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "processing_stages": {
                k: v.isoformat() for k, v in self.processing_stages.items()
            },
            "filtering": {
                "passed": self.filtering.passed,
                "rules_evaluated": self.filtering.rules_evaluated,
                "rule_results": self.filtering.rule_results,
                "default_action_applied": self.filtering.default_action_applied,
                "error_message": self.filtering.error_message
            },
            "routing": {
                "destination_url": self.routing.destination_url,
                "matched_value": self.routing.matched_value,
                "field_path": self.routing.field_path,
                "rule_index": self.routing.rule_index,
                "success": self.routing.success,
                "error_message": self.routing.error_message,
                "total_rules": self.routing.total_rules,
                "evaluated_rules": self.routing.evaluated_rules
            },
            "forwarding": {
                "destination_url": self.forwarding.destination_url,
                "success": self.forwarding.success,
                "status_code": self.forwarding.status_code,
                "response_time_ms": self.forwarding.response_time_ms,
                "error_message": self.forwarding.error_message,
                "error_type": self.forwarding.error_type,
                "content_length": self.forwarding.content_length
            }
        }
