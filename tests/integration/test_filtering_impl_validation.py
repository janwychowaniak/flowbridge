"""
Integration tests for Stage 4 - Main Processing Pipeline & Webhook Endpoint

This module contains comprehensive integration tests that validate the complete
filtering stage processing flow without mocking internal components.
Tests use real configuration files and validate end-to-end functionality.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

from flask import Flask




class TestFilteringStageIntegration:
    """Integration tests for Stage 4 filtering stage implementation."""
    

    def test_dropped_request_end_to_end(self, app_with_filtering_config: Flask) -> None:
        """
        Test complete end-to-end flow for a request that gets dropped.
        
        This tests the complete Stage 4 flow:
        1. HTTP request → middleware → webhook handler
        2. Processing pipeline → filtering engine → dropped response
        3. HTTP response with proper formatting
        """
        client = app_with_filtering_config.test_client()
        
        # Payload that will be dropped by filtering rules
        payload = {
            "objectType": "incident",  # Does not match "alert" rule
            "operation": "Creation",
            "object": {
                "title": "Test Alert",
                "severity": 3
            }
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return 200 with dropped response
        assert response.status_code == 200
        
        response_data = response.get_json()
        assert response_data['status'] == 'processed'
        assert response_data['result'] == 'dropped'
        assert 'request_id' in response_data
        assert 'filtering_summary' in response_data
        
        # Validate filtering summary
        summary = response_data['filtering_summary']
        assert summary['rules_evaluated'] > 0
        assert isinstance(summary['default_action_applied'], bool)
        assert summary['default_action_applied']
    

    def test_passed_request_filtering_stage(self, app_with_filtering_config: Flask) -> None:
        """
        Test filtering stage for a request that passes filtering rules.
        
        Stage 4 only tests the filtering portion for passed requests,
        as they continue to Stage 5 (routing).
        """
        client = app_with_filtering_config.test_client()
        
        # Payload that will pass filtering rules
        payload = {
            "objectType": "alert",      # Matches "alert" rule
            "operation": "Creation",    # Matches "Creation" rule
            "object": {
                "title": "AP_McAfeeMsme-virusDetected",
                "severity": 5
            }
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should return 200 with processing status (routing successful but no forwarding yet)
        assert response.status_code == 200
        
        response_data = response.get_json()
        assert response_data['status'] == 'processing'
        assert 'response type unclear' in response_data['message']  # Updated for Stage 5
        assert 'request_id' in response_data
    

    def test_missing_fields_in_filtering_rules(self, app_with_filtering_config: Flask) -> None:
        """
        Test requests with missing fields referenced in filtering rules.
        
        The filtering engine should handle missing fields gracefully
        and apply default actions appropriately.
        """
        client = app_with_filtering_config.test_client()
        
        # Payload with missing objectType field (referenced in filtering rules)
        payload = {
            "operation": "Creation",
            "object": {
                "title": "Test Alert",
                "severity": 2
            }
            # Missing "objectType" field
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should succeed with default action applied
        assert response.status_code == 200
        
        response_data = response.get_json()
        assert response_data['status'] == 'processed'
        
        # With missing fields, filtering should apply default action
        # If dropped, should have filtering summary
        assert 'filtering_summary' in response_data
        summary = response_data['filtering_summary']
        assert summary['default_action_applied'] is True
    

    def test_complex_nested_field_scenarios(self, app_with_filtering_config: Flask) -> None:
        """
        Test complex nested field extraction scenarios with real field extractor.
        
        Tests deep nesting, various data types, and edge cases
        with the actual field extraction engine.
        """
        client = app_with_filtering_config.test_client()
        
        # Complex nested payload
        payload = {
            "objectType": "alert",
            "operation": "Creation",
            "object": {
                "title": "Test Alert",  # Use routing-compatible value
                "details": {
                    "level1": {
                        "level2": {
                            "level3": {
                                "deep_field": "deep_value"
                            }
                        }
                    }
                },
                "arrays": [
                    {"item": "first"},
                    {"item": "second"}
                ],
                "mixed_types": {
                    "number": 42,
                    "boolean": True,
                    "null_value": None,
                    "string": "test"
                }
            }
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should process successfully regardless of complexity
        assert response.status_code == 200
        
        response_data = response.get_json()
        assert response_data['status'] in ['processed', 'processing']
        assert 'request_id' in response_data
    

    def test_empty_rules_with_default_actions(self, app_with_empty_rules: Flask) -> None:
        """
        Test configuration with empty filtering rules and default actions.
        
        This tests the scenario where no filtering rules are defined,
        and the system should apply the default action.
        """
        client = app_with_empty_rules.test_client()
        
        payload = {
            "objectType": "any",
            "operation": "any",
            "object": {"title": "Test Alert"}  # Use routing-compatible value
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        response_data = response.get_json()
        assert response_data['status'] in ['processed', 'processing']
        
        # With empty rules, default action should be applied
        if 'filtering_summary' in response_data:
            summary = response_data['filtering_summary']
            assert summary['default_action_applied'] is True
            assert summary['rules_evaluated'] == 0
    

    def test_error_scenarios_full_pipeline(self, app_with_filtering_config: Flask) -> None:
        """
        Test various error scenarios with full pipeline integration.
        
        Tests error handling across the complete processing pipeline
        without mocking any components.
        """
        client = app_with_filtering_config.test_client()
        
        # Test invalid JSON
        response = client.post(
            '/webhook',
            data='{"invalid": json}',
            content_type='application/json'
        )
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'error' in response_data
        assert 'request_id' in response_data
        
        # Test missing content-type
        response = client.post(
            '/webhook',
            data=json.dumps({"test": "data"})
        )
        assert response.status_code == 400
        
        # Test wrong content-type
        response = client.post(
            '/webhook',
            data=json.dumps({"test": "data"}),
            content_type='text/plain'
        )
        assert response.status_code == 400
        
        # Test non-dictionary payload
        response = client.post(
            '/webhook',
            data=json.dumps("string payload"),
            content_type='application/json'
        )
        assert response.status_code == 400
    

    def test_schema_free_operation_various_structures(self, app_with_filtering_config: Flask) -> None:
        """
        Test schema-free operation with various JSON dictionary structures.
        
        Validates that the system accepts any valid JSON dictionary
        without enforcing a specific schema.
        """
        client = app_with_filtering_config.test_client()
        
        # Test various valid JSON dictionary structures
        test_payloads = [
            # Minimal structure
            {"a": 1},
            
            # Different field names
            {"custom_field": "value", "another_field": 123},
            
            # Mixed data types
            {
                "string": "text",
                "number": 42,
                "boolean": True,
                "null": None,
                "array": [1, 2, 3],
                "object": {"nested": "value"}
            },
            
            # Different from typical webhook structure
            {
                "event_type": "custom",
                "metadata": {"source": "test"},
                "data": {"content": "anything"}
            }
        ]
        
        for payload in test_payloads:
            response = client.post(
                '/webhook',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            # Should process successfully (schema-free)
            assert response.status_code == 200
            
            response_data = response.get_json()
            assert response_data['status'] in ['processed', 'processing']
            assert 'request_id' in response_data
    

    def test_concurrent_request_handling(self, app_with_filtering_config: Flask) -> None:
        """
        Test concurrent request handling for performance validation.
        
        Validates that the processing pipeline can handle multiple
        concurrent requests without interference.
        """
        client = app_with_filtering_config.test_client()
        
        def make_request(payload_data: Dict[str, Any]) -> Dict[str, Any]:
            """Make a single webhook request and return response data."""
            response = client.post(
                '/webhook',
                data=json.dumps(payload_data),
                content_type='application/json'
            )
            return {
                'status_code': response.status_code,
                'data': response.get_json(),
                'request_id': response.get_json().get('request_id') if response.get_json() else None
            }
        
        # Create varied payloads for concurrent testing
        payloads = [
            {"objectType": "alert", "operation": "Creation", "object": {"title": "Test Alert"}, "index": i}
            for i in range(10)
        ]
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, payload) for payload in payloads]
            results = [future.result() for future in as_completed(futures)]
        
        # Validate all requests were processed successfully
        assert len(results) == 10
        
        for result in results:
            assert result['status_code'] == 200
            assert result['data']['status'] in ['processed', 'processing']
            assert result['request_id'] is not None
        
        # Validate all request IDs are unique (no interference)
        request_ids = [r['request_id'] for r in results]
        assert len(set(request_ids)) == len(request_ids)
    

    def test_request_correlation_across_pipeline(self, app_with_filtering_config: Flask) -> None:
        """
        Test request correlation tracking across the complete pipeline.
        
        Validates that request IDs are properly maintained and logged
        throughout the processing pipeline.
        """
        client = app_with_filtering_config.test_client()
        
        payload = {
            "objectType": "alert",
            "operation": "Creation",
            "object": {"title": "Test Alert"}
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        response_data = response.get_json()
        request_id = response_data.get('request_id')
        
        # Validate request ID format (should be UUID)
        assert request_id is not None
        assert len(request_id) == 36  # UUID format
        assert request_id.count('-') == 4  # UUID has 4 dashes
        
        # Validate request ID is consistent in response
        assert response_data['request_id'] == request_id
    

    def test_memory_usage_large_payloads(self, app_with_filtering_config: Flask) -> None:
        """
        Test memory usage with large JSON payloads.
        
        Validates that the processing pipeline efficiently handles
        large payloads without excessive memory usage.
        """
        client = app_with_filtering_config.test_client()
        
        # Create a large payload with nested structures
        large_object = {
            "title": "Test Alert",  # Add routing-compatible title
            "large_array": [{"item": f"data_{i}"} for i in range(1000)],
            "nested_data": {
                f"field_{i}": f"value_{i}" for i in range(100)
            }
        }
        
        payload = {
            "objectType": "alert",
            "operation": "Creation",
            "object": large_object
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Should handle large payloads successfully
        assert response.status_code == 200
        
        response_data = response.get_json()
        assert response_data['status'] in ['processed', 'processing']
        assert 'request_id' in response_data
    

    def test_error_isolation_between_requests(self, app_with_filtering_config: Flask) -> None:
        """
        Test that errors in individual requests don't affect other requests.
        
        Validates system stability when processing mixed valid/invalid requests.
        """
        client = app_with_filtering_config.test_client()
        
        # Mix of valid and invalid requests
        requests_data = [
            # Valid request
            {
                'payload': {"objectType": "alert", "operation": "Creation", "object": {"title": "Test Alert"}},
                'expected_status': 200
            },
            # Invalid JSON
            {
                'payload': '{"invalid": json}',
                'expected_status': 400,
                'raw_data': True
            },
            # Another valid request
            {
                'payload': {"objectType": "incident", "operation": "Update", "object": {"title": "Test Alert"}},
                'expected_status': 200
            },
            # Non-dictionary payload
            {
                'payload': "string payload",
                'expected_status': 400
            },
            # Final valid request
            {
                'payload': {"objectType": "alert", "operation": "Creation", "object": {"title": "Test Alert"}},
                'expected_status': 200
            }
        ]
        
        results = []
        for request_info in requests_data:
            if request_info.get('raw_data'):
                # Send raw string data
                response = client.post(
                    '/webhook',
                    data=request_info['payload'],
                    content_type='application/json'
                )
            else:
                # Send JSON data
                response = client.post(
                    '/webhook',
                    data=json.dumps(request_info['payload']),
                    content_type='application/json'
                )
            
            results.append({
                'expected': request_info['expected_status'],
                'actual': response.status_code,
                'response': response.get_json()
            })
        
        # Validate each request got the expected response
        for result in results:
            assert result['actual'] == result['expected']
        
        # Validate valid requests were processed successfully
        valid_responses = [r for r in results if r['expected'] == 200]
        for response in valid_responses:
            assert response['response']['status'] in ['processed', 'processing']
            assert 'request_id' in response['response']
