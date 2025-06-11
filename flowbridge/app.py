from typing import Optional

from flask import Flask, jsonify, request
from loguru import logger
from pydantic import BaseModel
from werkzeug.exceptions import MethodNotAllowed

from flowbridge.core.context import RequestContext
from flowbridge.utils.errors import FlowBridgeError
from flowbridge.api.handlers import bp as api_bp

def create_app(config: Optional[BaseModel] = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Store config for access in routes
    app.config["FLOWBRIDGE_CONFIG"] = config
    
    # Also store individual config sections for backward compatibility
    if config:
        app.config["GENERAL_CONFIG"] = config.general
        app.config["SERVER_CONFIG"] = config.server

    @app.before_request
    def before_request() -> None:
        """Create request context before processing request."""
        ctx = RequestContext()
        # Store in Flask g object for access during request
        request.ctx = ctx
        logger.debug(f"Request started: {ctx.to_dict()}")

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        response = {
            "error": "NotFound",
            "message": "The requested URL was not found on the server",
            "request_id": str(getattr(request, "ctx", RequestContext()).request_id)
        }
        return jsonify(response), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error: MethodNotAllowed):
        """Handle 405 Method Not Allowed errors."""
        response = {
            "error": "MethodNotAllowed",
            "message": f"The method {request.method} is not allowed for the requested URL",
            "request_id": str(getattr(request, "ctx", RequestContext()).request_id)
        }
        return jsonify(response), 405

    @app.errorhandler(FlowBridgeError)
    def handle_flowbridge_error(error: FlowBridgeError):
        """Handle application-specific errors."""
        response = {
            "error": error.__class__.__name__,
            "message": str(error),
            "request_id": str(getattr(request, "ctx", RequestContext()).request_id)
        }
        return jsonify(response), error.status_code

    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception):
        """Handle unexpected errors."""
        logger.exception("Unexpected error occurred")
        response = {
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "request_id": str(getattr(request, "ctx", RequestContext()).request_id)
        }
        return jsonify(response), 500

    # Register blueprints
    app.register_blueprint(api_bp)

    return app
