from typing import Callable, Optional
from functools import wraps
from flask import Request, Response, request, jsonify
from pydantic import ValidationError
from loguru import logger

from flowbridge.core.context import RequestContext
from flowbridge.utils.errors import InvalidRequestError

def validate_json_request(f: Callable) -> Callable:
    """Decorator to validate JSON requests and setup request context."""
    @wraps(f)
    def decorated(*args, **kwargs) -> Response:
        # Validate content type for POST/PUT/PATCH requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                error_response = {
                    "error": "InvalidRequestError",
                    "message": "Content-Type must be application/json",
                    "request_id": str(getattr(request, 'ctx', RequestContext()).request_id)
                }
                return jsonify(error_response), 400
            
            # Validate that JSON can be parsed
            try:
                _ = request.get_json()
            except Exception as e:
                error_response = {
                    "error": "InvalidRequestError",
                    "message": f"Invalid JSON format: {str(e)}",
                    "request_id": str(getattr(request, 'ctx', RequestContext()).request_id)
                }
                return jsonify(error_response), 400

        return f(*args, **kwargs)
    return decorated

class RequestPreprocessor:
    """Middleware class for request preprocessing."""
    
    def __init__(self, app):
        self.app = app
        self.context: Optional[RequestContext] = None

    def __call__(self, environ, start_response):
        # Create request context before each request
        self.context = RequestContext()
        
        # Add request ID to response headers
        def custom_start_response(status, headers, exc_info=None):
            headers.append(('X-Request-ID', str(self.context.request_id)))
            return start_response(status, headers, exc_info)

        logger.debug(
            "Processing request",
            request_id=str(self.context.request_id)
        )
        
        return self.app(environ, custom_start_response)
