import os
from pathlib import Path
from typing import Any, Dict, Union

import yaml
from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from ..utils.errors import ConfigurationError, ValidationError
from .models import ConfigModel


def validate_config_path(config_path: Union[str, Path]) -> Path:
    """
    Validate configuration file path.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Path: Validated Path object
        
    Raises:
        ConfigurationError: If path is invalid or file doesn't exist
    """
    try:
        path = Path(config_path).resolve()
        if not path.is_file():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                context={"path": str(config_path)}
            )
        return path
    except Exception as e:
        raise ConfigurationError(
            f"Invalid configuration path: {config_path}",
            context={"path": str(config_path)},
            original_error=e
        )


def load_yaml_safely(config_path: Path) -> Dict[str, Any]:
    """
    Load YAML configuration file using safe_load.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict[str, Any]: Loaded configuration dictionary
        
    Raises:
        ConfigurationError: If YAML parsing fails
    """
    try:
        with config_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse YAML configuration: {e}",
            context={"path": str(config_path)},
            original_error=e
        )
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read configuration file: {config_path}",
            context={"path": str(config_path)},
            original_error=e
        )


def load_config(config_path: Union[str, Path]) -> ConfigModel:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        ConfigModel: Validated configuration object
        
    Raises:
        ConfigurationError: If configuration loading fails
        ValidationError: If configuration validation fails
    """
    logger.info(f"Loading configuration from {config_path}")
    
    # Validate path
    path = validate_config_path(config_path)
    
    # Load YAML
    config_dict = load_yaml_safely(path)
    
    # Validate configuration
    try:
        config = ConfigModel.model_validate(config_dict)
        logger.info("Configuration loaded and validated successfully")
        return config
    except PydanticValidationError as e:
        raise ValidationError(
            "Configuration validation failed",
            context={
                "path": str(path),
                "errors": e.errors()
            },
            original_error=e
        )
