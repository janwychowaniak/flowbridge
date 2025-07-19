from datetime import datetime, timezone
from typing import Dict, Any

from flask import Blueprint, current_app, jsonify, request
from loguru import logger

from .middleware import validate_json_request
from ..core.processor import ProcessingPipeline
from ..utils.errors import ValidationError, ConfigurationError


bp = Blueprint("api", __name__)

# Initialize processing pipeline (will be set by app factory)
_processing_pipeline: ProcessingPipeline = None


def init_handlers(config):
    """Initialize handlers with configuration.
    
    Args:
        config: Application configuration
    """
    global _processing_pipeline
    _processing_pipeline = ProcessingPipeline(config)


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


@bp.route("/webhook", methods=["POST"])
@validate_json_request  # Uses existing middleware for JSON validation
def webhook_handler() -> Dict[str, Any]:
    """
    Main webhook endpoint for JSON payload processing.
    
    Processes incoming JSON payloads through the filtering pipeline.
    Dropped requests receive immediate responses.
    Passed requests are prepared for routing (Stage 5).
    
    Returns:
        JSON response with processing result
    """
    try:
        # Get JSON payload (already validated by middleware)
        payload = request.get_json()
        
        # Process through pipeline using existing RequestContext from middleware
        result = _processing_pipeline.process_webhook_request(payload)
        
        # Convert result to HTTP response
        response_data = result.to_response()
        
        if result.is_dropped:
            # Request was dropped by filtering
            logger.info(
                "Webhook request processed - dropped",
                request_id=str(request.ctx.request_id),
                result="dropped"
            )
            # Convert Pydantic model to dict for JSON serialization
            response_dict = response_data.model_dump() if hasattr(response_data, 'model_dump') else response_data
            return jsonify(response_dict), 200
            
        elif hasattr(response_data, 'model_dump'):
            # Pydantic model response (RoutingFailureResponse, ForwardingFailureResponse, RoutedResponse)
            response_dict = response_data.model_dump()
            
            # Determine appropriate HTTP status code based on response type
            if hasattr(response_data, 'result'):
                if response_data.result == "routing_failed":
                    logger.info(
                        "Webhook request processed - routing failed",
                        request_id=str(request.ctx.request_id),
                        result="routing_failed"
                    )
                    return jsonify(response_dict), 404  # No matching routing rule
                elif response_data.result == "forwarding_failed":
                    logger.info(
                        "Webhook request processed - forwarding failed",
                        request_id=str(request.ctx.request_id),
                        result="forwarding_failed"
                    )
                    return jsonify(response_dict), 502  # Gateway error
                elif response_data.result == "success":
                    logger.info(
                        "Webhook request processed - success",
                        request_id=str(request.ctx.request_id),
                        result="success"
                    )
                    return jsonify(response_dict), 200  # Success
            
            # Fallback for unknown Pydantic response types
            return jsonify(response_dict), 200
            
        else:
            # Dict response (fallback case)
            logger.info(
                "Webhook request processed - passed filtering",
                request_id=str(request.ctx.request_id),
                result="passed"
            )
            return jsonify(response_data), 200
            
    except ValidationError as e:
        error_response = {
            "error": "InvalidRequestError", 
            "message": str(e),
            "request_id": str(request.ctx.request_id)
        }
        logger.warning(
            "Webhook request validation failed",
            request_id=str(request.ctx.request_id),
            error=str(e)
        )
        return jsonify(error_response), 400
        
    except Exception as e:
        error_response = {
            "error": "InternalServerError",
            "message": "An unexpected error occurred during processing",
            "request_id": str(request.ctx.request_id)
        }
        logger.error(
            "Webhook request processing failed",
            request_id=str(request.ctx.request_id),
            error=str(e),
            error_type=type(e).__name__
        )
        return jsonify(error_response), 500


@bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors with consistent format."""
    return jsonify({
        "error": "NotFoundError",
        "message": "The requested resource was not found",
        "request_id": str(getattr(request, 'ctx', {}).get('request_id', 'unknown'))
    }), 404


@bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors with consistent format."""
    return jsonify({
        "error": "MethodNotAllowedError", 
        "message": f"Method {request.method} not allowed for this endpoint",
        "request_id": str(getattr(request, 'ctx', {}).get('request_id', 'unknown'))
    }), 405
