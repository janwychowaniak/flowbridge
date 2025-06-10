from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List, Optional
import sys

from loguru import logger
from pydantic import ValidationError

from flowbridge.config.loader import load_config
from flowbridge.utils.errors import FlowBridgeError
from flowbridge.utils.logging_utils import setup_logging

__version__ = "0.1.0"

def create_argument_parser() -> ArgumentParser:
    """Create and configure the argument parser for FlowBridge CLI.
    
    Returns:
        ArgumentParser: Configured argument parser instance
    """
    parser = ArgumentParser(
        prog="flowbridge",
        description="FlowBridge - Content-aware HTTP JSON traffic router"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="Path to the YAML configuration file"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate configuration without starting the application"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Override log level from configuration"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"FlowBridge v{__version__}"
    )
    
    return parser

def validate_config_path(config_path: str) -> Path:
    """Validate that the configuration file exists and is readable.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Path: Validated Path object
        
    Raises:
        FlowBridgeError: If the file doesn't exist or isn't readable
    """
    path = Path(config_path)
    if not path.exists():
        raise FlowBridgeError(f"Configuration file not found: {config_path}")
    if not path.is_file():
        raise FlowBridgeError(f"Configuration path is not a file: {config_path}")
    return path

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the FlowBridge application.
    
    Args:
        args: Optional list of command line arguments
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)
    
    try:
        config_path = validate_config_path(parsed_args.config)
        
        # Setup logging first
        log_level = parsed_args.log_level or "INFO"
        setup_logging(log_level)
        
        # Load and validate configuration
        config = load_config(str(config_path))
        logger.info(f"Configuration loaded successfully from {config_path}")
        
        if parsed_args.validate_only:
            logger.info("Configuration validation successful")
            return 0
            
        # TODO: Start application server here in future stages
        return 0
        
    except (FlowBridgeError, ValidationError) as e:
        logger.error(f"Configuration error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception("Unexpected error occurred")
        return 1

if __name__ == "__main__":
    sys.exit(main())
