from pathlib import Path
import sys

import click
from loguru import logger
from pydantic import ValidationError

from flowbridge.config.loader import load_config
from flowbridge.utils.errors import FlowBridgeError
from flowbridge.utils.logging_utils import setup_logging
from flowbridge.app import create_app

__version__ = "0.1.0"

@click.group()
def cli() -> None:
    """FlowBridge - HTTP JSON Traffic Router"""
    pass

@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
        required=True,
    help="Path to configuration file",
)
@click.option(
        "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set logging level",
)
@click.option(
    "--validate-only",
    is_flag=True,
    help="Validate configuration without starting the application",
)
def serve(config: str, log_level: str, validate_only: bool) -> None:
    """Start the FlowBridge server."""
    try:
        # Setup logging
        setup_logging(log_level)
        
        # Load and validate configuration
        logger.info(f"Loading configuration from: {config}")
        app_config = load_config(config)
        
        if validate_only:
            logger.info("Configuration validation successful")
            sys.exit(0)
        
        logger.info("Starting FlowBridge server")
        app = create_app(app_config)
        
        # Extract server config
        server_config = app_config.server
        logger.info(f"Server will listen on {server_config.host}:{server_config.port}")
        
        # Run the Flask app
        app.run(
            host=server_config.host,
            port=server_config.port,
            debug=log_level.upper() == "DEBUG"
        )
    except FlowBridgeError as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Configuration validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error while starting server")
        sys.exit(1)

@cli.command()
def version() -> None:
    """Show FlowBridge version."""
    click.echo(f"FlowBridge v{__version__}")

if __name__ == "__main__":
    cli()
