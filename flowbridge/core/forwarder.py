# flowbridge/core/forwarder.py

"""
HTTP request forwarder for FlowBridge - forwards HTTP requests to destination URLs
with timeout handling and response pass-through.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, RequestException
from loguru import logger

from flowbridge.utils.errors import ForwardingError


@dataclass
class ForwardingResult:
    """Result of HTTP request forwarding operation."""
    success: bool
    status_code: Optional[int]
    headers: Optional[Dict[str, str]]
    content: Optional[bytes]
    error_message: Optional[str]
    error_type: Optional[str]
    destination_url: str
    response_time_ms: Optional[float]


class RequestForwarder:
    """
    Handles HTTP request forwarding to destination URLs with timeout management
    and response pass-through capabilities.
    """
    
    def __init__(self, timeout: int = 2):
        """
        Initialize request forwarder with timeout configuration.
        
        Args:
            timeout: Request timeout in seconds (both connection and read)
        """
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure connection adapter for better performance
        adapter = HTTPAdapter(
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Maximum number of connections in pool
            max_retries=0         # No retries for MVP
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def forward_request(
        self,
        url: str,
        payload: Dict[str, Any],
        original_headers: Optional[Dict[str, str]] = None
    ) -> ForwardingResult:
        """
        Forward HTTP POST request to destination URL.
        
        Args:
            url: Destination URL
            payload: JSON payload to forward
            original_headers: Original request headers
            
        Returns:
            ForwardingResult with response or error information
        """
        import time
        start_time = time.time()
        
        try:
            # Prepare headers for forwarding
            forwarding_headers = self._prepare_forwarding_headers(original_headers)
            
            logger.info(
                "Forwarding request to destination",
                destination_url=url,
                timeout=self.timeout,
                payload_size=len(str(payload))
            )
            
            # Make the request with timeout
            response = self.session.post(
                url,
                json=payload,
                headers=forwarding_headers,
                timeout=(self.timeout, self.timeout),  # (connection_timeout, read_timeout)
                allow_redirects=False,  # Don't follow redirects
                stream=False  # Load full response for MVP
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Convert response headers to dict
            response_headers = dict(response.headers)
            
            logger.info(
                "Request forwarded successfully",
                destination_url=url,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                content_length=len(response.content)
            )
            
            return ForwardingResult(
                success=True,
                status_code=response.status_code,
                headers=response_headers,
                content=response.content,
                error_message=None,
                error_type=None,
                destination_url=url,
                response_time_ms=response_time_ms
            )
            
        except ConnectTimeout as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(
                "Request forwarding failed - connection timeout",
                destination_url=url,
                timeout=self.timeout,
                response_time_ms=response_time_ms,
                error=str(e)
            )
            return ForwardingResult(
                success=False,
                status_code=None,
                headers=None,
                content=None,
                error_message=f"Connection timeout after {self.timeout} seconds",
                error_type="CONNECTION_TIMEOUT",
                destination_url=url,
                response_time_ms=response_time_ms
            )
            
        except ReadTimeout as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(
                "Request forwarding failed - read timeout",
                destination_url=url,
                timeout=self.timeout,
                response_time_ms=response_time_ms,
                error=str(e)
            )
            return ForwardingResult(
                success=False,
                status_code=None,
                headers=None,
                content=None,
                error_message=f"Read timeout after {self.timeout} seconds",
                error_type="READ_TIMEOUT",
                destination_url=url,
                response_time_ms=response_time_ms
            )
            
        except ConnectionError as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(
                "Request forwarding failed - connection error",
                destination_url=url,
                response_time_ms=response_time_ms,
                error=str(e)
            )
            return ForwardingResult(
                success=False,
                status_code=None,
                headers=None,
                content=None,
                error_message=f"Connection error: {str(e)}",
                error_type="CONNECTION_ERROR",
                destination_url=url,
                response_time_ms=response_time_ms
            )
            
        except RequestException as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(
                "Request forwarding failed - request error",
                destination_url=url,
                response_time_ms=response_time_ms,
                error=str(e)
            )
            return ForwardingResult(
                success=False,
                status_code=None,
                headers=None,
                content=None,
                error_message=f"Request error: {str(e)}",
                error_type="REQUEST_ERROR",
                destination_url=url,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "Request forwarding failed - unexpected error",
                destination_url=url,
                response_time_ms=response_time_ms,
                error=str(e)
            )
            return ForwardingResult(
                success=False,
                status_code=None,
                headers=None,
                content=None,
                error_message=f"Unexpected error: {str(e)}",
                error_type="UNEXPECTED_ERROR",
                destination_url=url,
                response_time_ms=response_time_ms
            )
    
    def _prepare_forwarding_headers(self, original_headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        Prepare headers for forwarding request to destination.
        
        Args:
            original_headers: Original request headers
            
        Returns:
            Headers suitable for forwarding
        """
        forwarding_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'FlowBridge/1.0'
        }
        
        if original_headers:
            # Preserve correlation headers
            correlation_headers = [
                'x-request-id',
                'x-correlation-id',
                'x-trace-id'
            ]
            
            for header_name in correlation_headers:
                if header_name in original_headers:
                    forwarding_headers[header_name] = original_headers[header_name]
                # Also check lowercase and case-insensitive versions
                for orig_key, orig_value in original_headers.items():
                    if orig_key.lower() == header_name.lower():
                        forwarding_headers[header_name] = orig_value
                        break
        
        return forwarding_headers
    
    def close(self):
        """Close the HTTP session and clean up resources."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
