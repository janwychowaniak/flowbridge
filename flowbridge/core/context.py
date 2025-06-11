from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

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
            }
        }
