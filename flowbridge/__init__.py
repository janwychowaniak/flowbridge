"""
FlowBridge - Content-aware HTTP JSON traffic router.

This package provides functionality for routing webhook events based on
content-aware rules and configurations.
"""

__version__ = "0.1.0"
__author__ = "Jan Wychowaniak"

from .utils.errors import (
    FlowBridgeError,
    ConfigurationError,
    ValidationError,
    EnvironmentVariableError,
    InvalidRequestError,
)
from .config.models import (
    GeneralConfig,
    ServerConfig,
    FilterOperator,
    LogicOperator,
    FilterCondition,
    FilteringConfig,
    RouteMapping,
    ConfigModel
)
from .config.loader import load_config
from .core.context import RequestContext
from .app import create_app
from .api.handlers import bp
from .api.middleware import RequestPreprocessor, validate_json_request

__all__ = [
    "FlowBridgeError",
    "ConfigurationError",
    "ValidationError",
    "EnvironmentVariableError",
    "GeneralConfig",
    "ServerConfig",
    "FilterOperator",
    "LogicOperator",
    "FilterCondition",
    "FilteringConfig",
    "RouteMapping",
    "ConfigModel",
    "load_config",
    "InvalidRequestError",
    "RequestContext",
    "create_app",
    "bp",
    "RequestPreprocessor",
    "validate_json_request",
]