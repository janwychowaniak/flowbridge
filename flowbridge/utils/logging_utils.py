import sys
from pathlib import Path
from typing import Optional, Union

from loguru import logger

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    rotation: str = "200 MB"
) -> None:
    """Configure logging for the FlowBridge application.
    
    Args:
        log_level: The minimum log level to record
        log_file: Optional path to log file. If None, logs to stderr
        rotation: Log rotation size (e.g., "200 MB", "1 GB")
    """
    # Remove default logger
    logger.remove()
    
    # Add stderr handler with extra data support
    logger.add(
        sys.stderr,
        format="{time} | {level: <8} | {message} | {extra}",
        level=log_level,
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        logger.add(
            str(log_file),
            format="{time} | {level} | {message} | {extra}",
            level=log_level,
            rotation=rotation,
            serialize=True  # This enables JSON output
        )
    
    logger.info(f"Logging configured with level: {log_level}")

def log_config_loaded(config_path: Union[str, Path], sections: list[str]) -> None:
    """Log successful configuration loading.
    
    Args:
        config_path: Path to the loaded configuration file
        sections: List of successfully loaded configuration sections
    """
    logger.info(
        f"Configuration loaded from {config_path}",
        extra={"sections": sections}
    )

def log_config_error(
    error_type: str,
    message: str,
    context: Optional[dict] = None
) -> None:
    """Log configuration error with context.
    
    Args:
        error_type: Type of configuration error
        message: Error message
        context: Optional additional context information
    """
    logger.error(
        f"Configuration error: {message}",
        extra={
            "error_type": error_type,
            "context": context or {}
        }
    )
