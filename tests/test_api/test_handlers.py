import json
from unittest.mock import patch

from flowbridge.app import create_app
from flowbridge.core.processor import ProcessingResult
from flowbridge.core.filters import FilterResult
from flowbridge.utils.errors import ValidationError



class TestWebhookHandlers:
    """Test suite for webhook API handlers."""
    

    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create test app with configuration
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def teardown_method(self):
        """Clean up after each test method."""
        self.app_context.pop()
        

    def test_webhook_endpoint_dropped_request(self):
        """Test webhook endpoint with request that gets dropped."""
        # Mock processing pipeline to return dropped result
        # Rules failed, default_action="drop" → passed=False, default_action_applied=True
        mock_filter_result = FilterResult(
            passed=False,
            rules_evaluated=2,
            default_action_applied=True,
            rule_results=[
                {"field": "objectType", "operator": "equals", "rule_value": "alert", "passed": False},
                {"field": "operation", "operator": "equals", "rule_value": "Creation", "passed": False}
            ]
        )
        
        # Create a mock RequestContext
        from flowbridge.core.context import RequestContext
        from flowbridge.core.models import FilteringSummary
        
        mock_request_context = RequestContext()
        mock_filtering_summary = FilteringSummary(
            rules_evaluated=2,
            default_action_applied=True,
            matched_rules=None
        )
        
        mock_processing_result = ProcessingResult(
            request_context=mock_request_context,
            is_dropped=True,
            filtering_summary=mock_filtering_summary
        )
        
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.return_value = mock_processing_result
            
            # Test valid JSON payload
            payload = {
                "objectType": "notification",
                "operation": "Update",
                "object": {
                    "title": "Test Alert",
                    "severity": 3
                }
            }
            
            response = self.client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            
            # Verify response structure for dropped request
            assert response_data['status'] == 'processed'
            assert response_data['result'] == 'dropped'
            assert 'request_id' in response_data
            assert 'filtering_summary' in response_data
            assert response_data['filtering_summary']['rules_evaluated'] == 2
            assert response_data['filtering_summary']['default_action_applied'] is True
            
            # Verify processing pipeline was called
            mock_pipeline.process_webhook_request.assert_called_once_with(payload)
            

    def test_webhook_endpoint_passed_request(self):
        """Test webhook endpoint with request that passes filtering."""
        # Mock processing pipeline to return passed result
        # Rules passed → passed=True, default_action_applied=False
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            default_action_applied=False,
            rule_results=[
                {"field": "objectType", "operator": "equals", "rule_value": "alert", "passed": True},
                {"field": "operation", "operator": "equals", "rule_value": "Creation", "passed": True}
            ]
        )
        
        # Create a mock RequestContext
        from flowbridge.core.context import RequestContext
        from flowbridge.core.models import FilteringSummary
        
        mock_request_context = RequestContext()
        mock_filtering_summary = FilteringSummary(
            rules_evaluated=2,
            default_action_applied=False,
            matched_rules=["objectType", "operation"]
        )
        
        mock_processing_result = ProcessingResult(
            request_context=mock_request_context,
            is_dropped=False,
            filtering_summary=mock_filtering_summary
        )
        
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.return_value = mock_processing_result
            
            # Test valid JSON payload that passes filtering
            payload = {
                "objectType": "alert",
                "operation": "Creation",
                "object": {
                    "title": "AP_McAfeeMsme-virusDetected",
                    "severity": 5
                }
            }
            
            response = self.client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            
            # Verify response structure for passed request
            assert response_data['status'] == 'processing'
            assert 'request_id' in response_data
            assert 'message' in response_data
            assert 'routing' in response_data['message']
            
            # Verify processing pipeline was called
            mock_pipeline.process_webhook_request.assert_called_once_with(payload)
            

    def test_webhook_endpoint_invalid_json(self):
        """Test webhook endpoint with invalid JSON."""
        # Send invalid JSON
        response = self.client.post(
            '/webhook',
            data='{"invalid": json syntax}',
            content_type='application/json'
        )
        
        # Should return 400 due to JSON parsing error from middleware
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert response_data['error'] == 'InvalidRequestError'
        assert 'message' in response_data
        assert 'request_id' in response_data
        

    def test_webhook_endpoint_missing_content_type(self):
        """Test webhook endpoint with missing content-type header."""
        payload = {
            "objectType": "alert",
            "operation": "Creation"
        }
        
        # Send without content-type header
        response = self.client.post(
            '/webhook',
            data=json.dumps(payload)
            # No content_type specified
        )
        
        # Should return 400 due to missing content-type
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert response_data['error'] == 'InvalidRequestError'
        assert 'content-type' in response_data['message'].lower()
        assert 'request_id' in response_data
        

    def test_webhook_endpoint_wrong_content_type(self):
        """Test webhook endpoint with wrong content-type."""
        payload = {
            "objectType": "alert",
            "operation": "Creation"
        }
        
        # Send with wrong content-type
        response = self.client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/xml'
        )
        
        # Should return 400 due to wrong content-type
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert response_data['error'] == 'InvalidRequestError'
        assert 'content-type' in response_data['message'].lower()
        assert 'request_id' in response_data
        

    def test_webhook_endpoint_non_dictionary_payload(self):
        """Test webhook endpoint with non-dictionary payload."""
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.side_effect = ValidationError(
                "Payload must be a dictionary"
            )
            
            # Test with array payload
            payload = ["item1", "item2"]
            
            response = self.client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Should return 400 due to validation error
            assert response.status_code == 400
            response_data = json.loads(response.data)
            
            assert response_data['error'] == 'InvalidRequestError'
            assert 'dictionary' in response_data['message'].lower()
            assert 'request_id' in response_data
            

    def test_webhook_endpoint_processing_error(self):
        """Test webhook endpoint with processing error."""
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.side_effect = Exception("Internal processing error")
            
            payload = {
                "objectType": "alert",
                "operation": "Creation"
            }
            
            response = self.client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Should return 500 due to internal error
            assert response.status_code == 500
            response_data = json.loads(response.data)
            
            assert response_data['error'] == 'InternalServerError'
            assert response_data['message'] == 'An unexpected error occurred during processing'
            assert 'request_id' in response_data
            

    def test_webhook_endpoint_schema_free_operation(self):
        """Test webhook endpoint accepts various JSON dictionary structures."""
        # Mock processing pipeline to return passed result
        # No rules evaluated, default_action="pass" → passed=True, default_action_applied=True
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=0,
            default_action_applied=True,
            rule_results=[]
        )
        
        # Create a mock RequestContext
        from flowbridge.core.context import RequestContext
        from flowbridge.core.models import FilteringSummary
        
        mock_request_context = RequestContext()
        mock_filtering_summary = FilteringSummary(
            rules_evaluated=0,
            default_action_applied=True,
            matched_rules=None
        )
        
        mock_processing_result = ProcessingResult(
            request_context=mock_request_context,
            is_dropped=False,
            filtering_summary=mock_filtering_summary
        )
        
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.return_value = mock_processing_result
            
            # Test with different JSON structures
            test_payloads = [
                {},  # Empty dictionary
                {"single_field": "value"},  # Single field
                {"nested": {"deep": {"structure": "value"}}},  # Deep nesting
                {"mixed": {"string": "value", "number": 42, "boolean": True, "null": None}},  # Mixed types
                {"array_field": [1, 2, 3]},  # Array field
                {"complex": {"items": [{"id": 1}, {"id": 2}]}}  # Complex structure
            ]
            
            for payload in test_payloads:
                response = self.client.post(
                    '/webhook',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                
                # All valid JSON dictionaries should be accepted
                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert response_data['status'] == 'processing'
                assert 'request_id' in response_data
                assert 'message' in response_data
                

    def test_webhook_endpoint_request_correlation(self):
        """Test that request correlation ID is consistent across response."""
        # Mock processing pipeline to return dropped result
        # Rules failed, default_action="drop" → passed=False, default_action_applied=True
        mock_filter_result = FilterResult(
            passed=False,
            rules_evaluated=1,
            default_action_applied=True,
            rule_results=[]
        )
        
        # Create a mock RequestContext
        from flowbridge.core.context import RequestContext
        from flowbridge.core.models import FilteringSummary
        
        mock_request_context = RequestContext()
        mock_filtering_summary = FilteringSummary(
            rules_evaluated=1,
            default_action_applied=True,
            matched_rules=None
        )
        
        mock_processing_result = ProcessingResult(
            request_context=mock_request_context,
            is_dropped=True,
            filtering_summary=mock_filtering_summary
        )
        
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.return_value = mock_processing_result
            
            payload = {"test": "data"}
            
            response = self.client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            response_data = json.loads(response.data)
            
            # Verify request_id is present and valid UUID format
            assert 'request_id' in response_data
            request_id = response_data['request_id']
            assert len(request_id) == 36  # UUID format
            assert request_id.count('-') == 4  # UUID has 4 hyphens
            

    def test_webhook_endpoint_rules_fail_default_pass(self):
        """Test webhook endpoint with rules that fail but default_action='pass'."""
        # Mock processing pipeline to return passed result despite rule failure
        # Rules failed, default_action="pass" → passed=True, default_action_applied=True
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            default_action_applied=True,
            rule_results=[
                {"field": "objectType", "operator": "equals", "rule_value": "alert", "passed": False},
                {"field": "operation", "operator": "equals", "rule_value": "Creation", "passed": False}
            ]
        )
        
        # Create a mock RequestContext
        from flowbridge.core.context import RequestContext
        from flowbridge.core.models import FilteringSummary
        
        mock_request_context = RequestContext()
        mock_filtering_summary = FilteringSummary(
            rules_evaluated=2,
            default_action_applied=True,
            matched_rules=None
        )
        
        mock_processing_result = ProcessingResult(
            request_context=mock_request_context,
            is_dropped=False,
            filtering_summary=mock_filtering_summary
        )
        
        with patch('flowbridge.api.handlers._processing_pipeline') as mock_pipeline:
            mock_pipeline.process_webhook_request.return_value = mock_processing_result
            
            # Test valid JSON payload that fails rules but passes due to default_action="pass"
            payload = {
                "objectType": "notification",  # Fails rule
                "operation": "Update",  # Fails rule
                "object": {
                    "title": "Test notification",
                    "severity": 3
                }
            }
            
            response = self.client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Verify response
            assert response.status_code == 200
            response_data = json.loads(response.data)
            
            # Verify response structure for passed request (despite rule failure)
            assert response_data['status'] == 'processing'
            assert 'request_id' in response_data
            assert 'message' in response_data
            assert 'routing' in response_data['message']
            
            # Verify processing pipeline was called
            mock_pipeline.process_webhook_request.assert_called_once_with(payload)
            


class TestOperationalEndpoints:
    """Test suite for operational endpoints (health, config)."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def teardown_method(self):
        """Clean up after each test method."""
        self.app_context.pop()
        

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['status'] == 'healthy'
        assert 'timestamp' in response_data
        assert 'request_id' in response_data
        

    def test_config_endpoint(self):
        """Test configuration endpoint."""
        response = self.client.get('/config')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'config' in response_data
        assert 'request_id' in response_data
        assert isinstance(response_data['config'], dict)
        

    def test_404_error_handler(self):
        """Test 404 error handler."""
        response = self.client.get('/nonexistent')
        
        assert response.status_code == 404
        response_data = json.loads(response.data)
        
        assert response_data['error'] == 'NotFound'
        assert 'message' in response_data
        assert 'request_id' in response_data
        

    def test_405_error_handler(self):
        """Test 405 error handler."""
        response = self.client.post('/health')  # GET-only endpoint
        
        assert response.status_code == 405
        response_data = json.loads(response.data)
        
        assert response_data['error'] == 'MethodNotAllowed'
        assert 'POST' in response_data['message']
        assert 'request_id' in response_data 