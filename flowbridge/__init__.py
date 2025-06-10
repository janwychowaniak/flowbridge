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
    EnvironmentVariableError
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
]