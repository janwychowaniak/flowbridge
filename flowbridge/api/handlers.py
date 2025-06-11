from datetime import datetime, timezone
from typing import Dict, Any

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("api", __name__)

@bp.route("/health", methods=["GET"])
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status information
    """
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": str(request.ctx.request_id)
    }
    return jsonify(response)

@bp.route("/config", methods=["GET"])
def get_config() -> Dict[str, Any]:
    """
    Get current configuration.
    
    Returns:
        Current application configuration
    """
    config = current_app.config["FLOWBRIDGE_CONFIG"]
    response = {
        "config": config.model_dump(mode='json') if config else {},
        "request_id": str(request.ctx.request_id)
    }
    return jsonify(response)
