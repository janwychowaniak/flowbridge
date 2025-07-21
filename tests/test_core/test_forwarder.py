import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError, RequestException

from flowbridge.core.forwarder import RequestForwarder, ForwardingResult
from flowbridge.utils.errors import ForwardingError


class TestRequestForwarder:
    """Test suite for RequestForwarder component."""

    @pytest.fixture
    def forwarder(self):
        """Create RequestForwarder instance with default timeout."""
        return RequestForwarder(timeout=2)

    @pytest.fixture
    def custom_timeout_forwarder(self):
        """Create RequestForwarder instance with custom timeout."""
        return RequestForwarder(timeout=5)

    @pytest.fixture
    def sample_payload(self):
        """Create sample JSON payload for testing."""
        return {
            "objectType": "alert",
            "operation": "Creation",
            "object": {
                "title": "virus-detected",
                "severity": 8,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

    @pytest.fixture
    def sample_headers(self):
        """Create sample request headers."""
        return {
            "Content-Type": "application/json",
            "X-Request-ID": "test-request-123",
            "X-Correlation-ID": "correlation-456",
            "User-Agent": "TestClient/1.0",
            "Host": "flowbridge.local"
        }

    def test_forwarder_initialization_default_timeout(self):
        """Test RequestForwarder initialization with default timeout."""
        forwarder = RequestForwarder()
        assert forwarder.timeout == 2
        assert forwarder.session is not None

    def test_forwarder_initialization_custom_timeout(self):
        """Test RequestForwarder initialization with custom timeout."""
        forwarder = RequestForwarder(timeout=10)
        assert forwarder.timeout == 10
        assert forwarder.session is not None

    def test_session_adapter_configuration(self, forwarder):
        """Test that HTTP session adapters are properly configured."""
        assert forwarder.session.adapters['http://'] is not None
        assert forwarder.session.adapters['https://'] is not None

    @patch('requests.Session.post')
    def test_successful_http_forwarding(self, mock_post, forwarder, sample_payload):
        """Test successful HTTP request forwarding."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"status": "success"}'
        mock_post.return_value = mock_response

        url = "http://destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert result.success
        assert result.status_code == 200
        assert result.headers == {'Content-Type': 'application/json'}
        assert result.content == b'{"status": "success"}'
        assert result.destination_url == url
        assert result.error_message is None
        assert result.error_type is None
        assert result.response_time_ms is not None
        assert result.response_time_ms > 0

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json'] == sample_payload
        assert call_args[1]['timeout'] == (2, 2)
        assert call_args[1]['allow_redirects'] is False
        assert call_args[1]['stream'] is False

    @patch('requests.Session.post')
    def test_successful_forwarding_with_headers(self, mock_post, forwarder, sample_payload, sample_headers):
        """Test successful forwarding with header preservation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {'Content-Type': 'application/json', 'X-Response-ID': 'resp-123'}
        mock_response.content = b'{"id": "created-123"}'
        mock_post.return_value = mock_response

        url = "https://secure-destination.com/api/alerts"
        result = forwarder.forward_request(url, sample_payload, sample_headers)

        assert result.success
        assert result.status_code == 201
        assert 'X-Response-ID' in result.headers
        assert result.content == b'{"id": "created-123"}'

        # Verify headers were prepared correctly
        call_args = mock_post.call_args
        forwarded_headers = call_args[1]['headers']
        assert forwarded_headers['Content-Type'] == 'application/json'
        assert forwarded_headers['User-Agent'] == 'FlowBridge/1.0'
        assert forwarded_headers['x-request-id'] == 'test-request-123'
        assert forwarded_headers['x-correlation-id'] == 'correlation-456'

    @patch('requests.Session.post')
    def test_connection_timeout_error(self, mock_post, forwarder, sample_payload):
        """Test handling of connection timeout errors."""
        mock_post.side_effect = ConnectTimeout("Connection timeout")

        url = "http://slow-destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert not result.success
        assert result.status_code is None
        assert result.headers is None
        assert result.content is None
        assert result.destination_url == url
        assert "Connection timeout after 2 seconds" in result.error_message
        assert result.error_type == "CONNECTION_TIMEOUT"
        assert result.response_time_ms is not None

    @patch('requests.Session.post')
    def test_read_timeout_error(self, mock_post, forwarder, sample_payload):
        """Test handling of read timeout errors."""
        mock_post.side_effect = ReadTimeout("Read timeout")

        url = "http://slow-response.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert not result.success
        assert result.status_code is None
        assert result.headers is None
        assert result.content is None
        assert result.destination_url == url
        assert "Read timeout after 2 seconds" in result.error_message
        assert result.error_type == "READ_TIMEOUT"
        assert result.response_time_ms is not None

    @patch('requests.Session.post')
    def test_connection_error(self, mock_post, forwarder, sample_payload):
        """Test handling of network connection errors."""
        mock_post.side_effect = ConnectionError("Connection refused")

        url = "http://unreachable.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert not result.success
        assert result.status_code is None
        assert result.headers is None
        assert result.content is None
        assert result.destination_url == url
        assert "Connection error: Connection refused" in result.error_message
        assert result.error_type == "CONNECTION_ERROR"
        assert result.response_time_ms is not None

    @patch('requests.Session.post')
    def test_generic_request_exception(self, mock_post, forwarder, sample_payload):
        """Test handling of generic request exceptions."""
        mock_post.side_effect = RequestException("Generic request error")

        url = "http://error-destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert not result.success
        assert result.status_code is None
        assert result.headers is None
        assert result.content is None
        assert result.destination_url == url
        assert "Request error: Generic request error" in result.error_message
        assert result.error_type == "REQUEST_ERROR"
        assert result.response_time_ms is not None

    @patch('requests.Session.post')
    def test_unexpected_exception(self, mock_post, forwarder, sample_payload):
        """Test handling of unexpected exceptions."""
        mock_post.side_effect = ValueError("Unexpected error")

        url = "http://destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert not result.success
        assert result.status_code is None
        assert result.headers is None
        assert result.content is None
        assert result.destination_url == url
        assert "Unexpected error: Unexpected error" in result.error_message
        assert result.error_type == "UNEXPECTED_ERROR"
        assert result.response_time_ms is not None

    @patch('requests.Session.post')
    def test_destination_server_error_responses(self, mock_post, forwarder, sample_payload):
        """Test handling of various HTTP error responses from destination."""
        error_scenarios = [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (502, "Bad Gateway"),
            (503, "Service Unavailable")
        ]

        for status_code, status_text in error_scenarios:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.content = status_text.encode()
            mock_post.return_value = mock_response

            url = "http://destination.com/webhook/"
            result = forwarder.forward_request(url, sample_payload)

            # Even error responses are considered "successful" forwarding
            assert result.success
            assert result.status_code == status_code
            assert result.content == status_text.encode()
            assert result.destination_url == url
            assert result.error_message is None
            assert result.error_type is None

    def test_prepare_forwarding_headers_basic(self, forwarder):
        """Test header preparation with basic scenario."""
        result = forwarder._prepare_forwarding_headers(None)
        
        assert result['Content-Type'] == 'application/json'
        assert result['User-Agent'] == 'FlowBridge/1.0'
        assert len(result) == 2

    def test_prepare_forwarding_headers_with_correlation(self, forwarder):
        """Test header preparation with correlation headers."""
        original_headers = {
            'Content-Type': 'text/plain',  # Should be overridden
            'X-Request-ID': 'req-123',
            'X-Correlation-ID': 'corr-456',
            'X-Trace-ID': 'trace-789',
            'Authorization': 'Bearer token',  # Should be filtered out
            'Host': 'original-host'  # Should be filtered out
        }

        result = forwarder._prepare_forwarding_headers(original_headers)

        assert result['Content-Type'] == 'application/json'
        assert result['User-Agent'] == 'FlowBridge/1.0'
        assert result['x-request-id'] == 'req-123'
        assert result['x-correlation-id'] == 'corr-456'
        assert result['x-trace-id'] == 'trace-789'
        assert 'Authorization' not in result
        assert 'Host' not in result

    def test_prepare_forwarding_headers_case_insensitive(self, forwarder):
        """Test header preparation with case-insensitive correlation headers."""
        original_headers = {
            'X-REQUEST-ID': 'req-123',  # Different case
            'x-correlation-id': 'corr-456',  # Different case
            'X-Trace-Id': 'trace-789'  # Mixed case
        }

        result = forwarder._prepare_forwarding_headers(original_headers)

        assert result['x-request-id'] == 'req-123'
        assert result['x-correlation-id'] == 'corr-456'
        assert result['x-trace-id'] == 'trace-789'

    @patch('requests.Session.post')
    def test_custom_timeout_usage(self, mock_post, custom_timeout_forwarder, sample_payload):
        """Test that custom timeout is used in requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'{"status": "ok"}'
        mock_post.return_value = mock_response

        url = "http://destination.com/webhook"
        result = custom_timeout_forwarder.forward_request(url, sample_payload)

        assert result.success
        # Verify custom timeout was used
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == (5, 5)

    @patch('requests.Session.post')
    def test_large_payload_handling(self, mock_post, forwarder):
        """Test forwarding of large JSON payloads."""
        # Create a large payload
        large_payload = {
            "large_data": "x" * 10000,  # 10KB string
            "nested": {
                "arrays": [{"item": i} for i in range(1000)]
            }
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.content = b'{"processed": true}'
        mock_post.return_value = mock_response

        url = "http://destination.com/large-webhook"
        result = forwarder.forward_request(url, large_payload)

        assert result.success
        assert result.status_code == 200
        
        # Verify the large payload was sent
        call_args = mock_post.call_args
        assert call_args[1]['json'] == large_payload

    @patch('requests.Session.post')
    def test_large_response_handling(self, mock_post, forwarder, sample_payload):
        """Test handling of large responses from destination."""
        # Mock large response
        large_content = b'{"data": "' + b'x' * 50000 + b'"}'  # ~50KB response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json', 'Content-Length': str(len(large_content))}
        mock_response.content = large_content
        mock_post.return_value = mock_response

        url = "http://destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert result.success
        assert result.status_code == 200
        assert len(result.content) > 50000
        assert result.content == large_content

    @patch('requests.Session.post')
    def test_response_time_measurement(self, mock_post, forwarder, sample_payload):
        """Test that response time is measured accurately."""
        # Mock a response with simulated delay
        def slow_response(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {}
            mock_response.content = b'{"status": "ok"}'
            return mock_response

        mock_post.side_effect = slow_response

        url = "http://destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert result.success
        assert result.response_time_ms is not None
        assert result.response_time_ms >= 100  # At least 100ms due to sleep
        assert result.response_time_ms < 1000  # But not too high (reasonable upper bound)

    def test_context_manager_usage(self):
        """Test RequestForwarder as context manager."""
        with RequestForwarder(timeout=3) as forwarder:
            assert forwarder.timeout == 3
            assert forwarder.session is not None

        # Session should be closed after context exit
        # Note: We can't easily test if session is actually closed without
        # accessing private attributes, but we can test the method exists

    def test_manual_close(self, forwarder):
        """Test manual cleanup of forwarder resources."""
        session = forwarder.session
        forwarder.close()
        # Verify close doesn't throw an error
        # Session close behavior is internal to requests library

    @patch('requests.Session.post')
    @patch('flowbridge.core.forwarder.logger')
    def test_logging_on_successful_forwarding(self, mock_logger, mock_post, forwarder, sample_payload):
        """Test logging behavior on successful forwarding."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'{"result": "ok"}'
        mock_post.return_value = mock_response

        url = "http://destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert result.success
        # Verify logging calls
        assert mock_logger.info.call_count >= 2  # Should log start and success
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Forwarding request to destination" in call for call in log_calls)
        assert any("Request forwarded successfully" in call for call in log_calls)

    @patch('requests.Session.post')
    @patch('flowbridge.core.forwarder.logger')
    def test_logging_on_timeout_error(self, mock_logger, mock_post, forwarder, sample_payload):
        """Test logging behavior on timeout errors."""
        mock_post.side_effect = ConnectTimeout("Connection timeout")

        url = "http://slow-destination.com/webhook"
        result = forwarder.forward_request(url, sample_payload)

        assert not result.success
        # Verify warning log for timeout
        mock_logger.warning.assert_called()
        log_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("connection timeout" in call for call in log_calls)

    def test_forwarding_result_dataclass_structure(self):
        """Test ForwardingResult dataclass structure and fields."""
        result = ForwardingResult(
            success=True,
            status_code=200,
            headers={'Content-Type': 'application/json'},
            content=b'{"data": "test"}',
            error_message=None,
            error_type=None,
            destination_url="http://test.com",
            response_time_ms=150.5
        )

        assert result.success
        assert result.status_code == 200
        assert result.headers == {'Content-Type': 'application/json'}
        assert result.content == b'{"data": "test"}'
        assert result.error_message is None
        assert result.error_type is None
        assert result.destination_url == "http://test.com"
        assert result.response_time_ms == 150.5

    def test_forwarding_result_error_structure(self):
        """Test ForwardingResult structure for error cases."""
        result = ForwardingResult(
            success=False,
            status_code=None,
            headers=None,
            content=None,
            error_message="Connection failed",
            error_type="CONNECTION_ERROR",
            destination_url="http://failed.com",
            response_time_ms=2000.0
        )

        assert not result.success
        assert result.status_code is None
        assert result.headers is None
        assert result.content is None
        assert result.error_message == "Connection failed"
        assert result.error_type == "CONNECTION_ERROR"
        assert result.destination_url == "http://failed.com"
        assert result.response_time_ms == 2000.0

    @patch('requests.Session.post')
    def test_url_schemes_handling(self, mock_post, forwarder, sample_payload):
        """Test forwarding to both HTTP and HTTPS URLs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'{"status": "ok"}'
        mock_post.return_value = mock_response

        urls = [
            "http://insecure-destination.com/webhook",
            "https://secure-destination.com/webhook"
        ]

        for url in urls:
            result = forwarder.forward_request(url, sample_payload)
            assert result.success
            assert result.destination_url == url

    @patch('requests.Session.post')
    def test_json_serialization_edge_cases(self, mock_post, forwarder):
        """Test JSON serialization of edge case payloads."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b'{"received": true}'
        mock_post.return_value = mock_response

        edge_case_payloads = [
            {},  # Empty payload
            {"unicode": "测试数据"},  # Unicode content
            {"special_chars": "!@#$%^&*()"},  # Special characters
            {"numbers": [1, 2.5, -3, 0]},  # Various number types
            {"booleans": [True, False, None]},  # Boolean and null values
        ]

        url = "http://destination.com/webhook"
        for payload in edge_case_payloads:
            result = forwarder.forward_request(url, payload)
            assert result.success
            # Verify the payload was properly JSON-serialized
            call_args = mock_post.call_args
            assert call_args[1]['json'] == payload 