from typing import Any, Dict, Optional
from loguru import logger

class FlowBridgeError(Exception):
    """Base exception class for FlowBridge application."""
    
    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize FlowBridge error with context and original error.
        
        Args:
            message: Error description
            context: Additional error context
            original_error: Original exception if this is a wrapper
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.original_error = original_error
        
        # Log the error with context
        logger.error(
            self.message,
            error_type=self.__class__.__name__,
            **self.context
        )

class ConfigurationError(FlowBridgeError):
    """Raised when configuration loading or validation fails."""
    pass

class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass

class EnvironmentVariableError(ConfigurationError):
    """Raised when required environment variables are missing."""
    pass

class InvalidRequestError(FlowBridgeError):
    """Raised when request validation fails."""
    pass

class RoutingError(FlowBridgeError):
    """Raised when routing operations fail."""
    pass

class ForwardingError(FlowBridgeError):
    """Raised when request forwarding fails."""
    pass