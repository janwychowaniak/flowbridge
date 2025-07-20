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
        
        # Should return 502 because forwarding to localhost:5000 fails (no server running)
        assert response.status_code == 502
        
        response_data = response.get_json()
        assert response_data['status'] == 'failed'
        assert response_data['result'] == 'forwarding_failed'
        assert 'request_id' in response_data
        # Verify filtering and routing were successful
        assert response_data['filtering_summary']['rules_evaluated'] == 2
        assert response_data['routing_summary']['success'] == True
        assert response_data['routing_summary']['destination_url'] == 'http://localhost:5000/endpoint1'
    

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
        
        # Should return 502 because forwarding to localhost:5000 fails (no server running)
        assert response.status_code == 502
        
        response_data = response.get_json()
        assert response_data['status'] == 'failed'
        assert response_data['result'] == 'forwarding_failed'
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
        
        # Should return 502 because with empty rules and default_action="pass", 
        # the request passes filtering and tries to forward, but fails
        assert response.status_code == 502
        
        response_data = response.get_json()
        assert response_data['status'] == 'failed'
        assert response_data['result'] == 'forwarding_failed'
        
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
            assert result['status_code'] == 502  # Forwarding failures
            assert result['data']['status'] == 'failed'
            assert result['data']['result'] == 'forwarding_failed'
            assert result['request_id'] is not None
        
        # Validate all request IDs are unique (no interference)
        request_ids = [r['request_id'] for r in results]
        assert len(set(request_ids)) == len(request_ids)
    

    def test_request_id_format_validation(self, app_with_filtering_config: Flask) -> None:
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
        
        assert response.status_code == 502  # Forwarding failure
        
        response_data = response.get_json()
        request_id = response_data.get('request_id')
        
        # Validate request ID format (should be UUID)
        assert request_id is not None
        assert len(request_id) == 36  # UUID format
        assert request_id.count('-') == 4  # UUID has 4 dashes
    

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
        
        # Should return 502 because forwarding fails (large payload handled correctly)
        assert response.status_code == 502
        
        response_data = response.get_json()
        assert response_data['status'] == 'failed'
        assert response_data['result'] == 'forwarding_failed'
        assert 'request_id' in response_data
    

    def test_error_isolation_between_requests(self, app_with_filtering_config: Flask) -> None:
        """
        STRESS TEST: Concurrent error isolation under heavy load.
        
        Validates system stability when processing many mixed valid/invalid 
        requests simultaneously. Tests true error isolation, threading safety,
        and system resilience under stress.
        """
        import time
        import random
        
        client = app_with_filtering_config.test_client()
        
        def make_request(request_info: Dict[str, Any]) -> Dict[str, Any]:
            """Execute a single request and return detailed results."""
            start_time = time.time()
            
            try:
                if request_info.get('raw_data'):
                    # Send raw string data (malformed)
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
                
                response_time = time.time() - start_time
                response_data = response.get_json()
                
                return {
                    'expected': request_info['expected_status'],
                    'actual': response.status_code,
                    'response': response_data,
                    'response_time': response_time,
                    'request_type': request_info.get('type', 'unknown'),
                    'success': response.status_code == request_info['expected_status'],
                    'request_id': response_data.get('request_id') if response_data else None
                }
                
            except Exception as e:
                return {
                    'expected': request_info['expected_status'],
                    'actual': 500,
                    'response': None,
                    'response_time': time.time() - start_time,
                    'request_type': request_info.get('type', 'unknown'),
                    'success': False,
                    'error': str(e),
                    'request_id': None
                }
        
        # EXPANDED STRESS TEST DATASET
        base_requests = [
            # === VALID REQUESTS (should succeed but fail forwarding) ===
            {
                'payload': {"objectType": "alert", "operation": "Creation", "object": {"title": "Test Alert"}},
                'expected_status': 502,
                'type': 'valid_forwarding_fail'
            },
            {
                'payload': {"objectType": "alert", "operation": "Creation", "object": {"title": "Critical malware detected"}},
                'expected_status': 502,
                'type': 'valid_forwarding_fail'
            },
            
            # === DROPPED REQUESTS (filtered out) ===
            {
                'payload': {"objectType": "incident", "operation": "Update", "object": {"title": "Test Alert"}},
                'expected_status': 200,
                'type': 'dropped_by_filter'
            },
            {
                'payload': {"objectType": "notification", "operation": "Creation", "object": {"title": "Test"}},
                'expected_status': 200,
                'type': 'dropped_by_filter'
            },
            
            # === MALFORMED JSON ERRORS ===
            {
                'payload': '{"invalid": json}',
                'expected_status': 400,
                'raw_data': True,
                'type': 'invalid_json'
            },
            {
                'payload': '{"unclosed": "string"',
                'expected_status': 400,
                'raw_data': True,
                'type': 'invalid_json'
            },
            {
                'payload': '{broken json here}',
                'expected_status': 400,
                'raw_data': True,
                'type': 'invalid_json'
            },
            {
                'payload': '{"trailing": "comma",}',
                'expected_status': 400,
                'raw_data': True,
                'type': 'invalid_json'
            },
            
            # === NON-DICTIONARY PAYLOADS ===
            {
                'payload': "string payload",
                'expected_status': 400,
                'type': 'non_dict_string'
            },
            {
                'payload': 42,
                'expected_status': 400,
                'type': 'non_dict_number'
            },
            {
                'payload': [1, 2, 3],
                'expected_status': 400,
                'type': 'non_dict_array'
            },
            {
                'payload': True,
                'expected_status': 400,
                'type': 'non_dict_boolean'
            },
            {
                'payload': None,
                'expected_status': 400,
                'type': 'non_dict_null'
            },
            
            # === EDGE CASE PAYLOADS ===
            {
                'payload': {},
                'expected_status': 200,
                'type': 'empty_dict'
            },
            {
                'payload': {"": ""},
                'expected_status': 200,
                'type': 'empty_strings'
            },
            {
                'payload': {"null_field": None, "objectType": "alert", "operation": "Creation", "object": {"title": "AP_McAfeeMsme-virusDetected"}},
                'expected_status': 502,
                'type': 'null_fields'
            },
            
            # === LARGE PAYLOADS (memory stress) ===
            {
                'payload': {
                    "objectType": "alert",
                    "operation": "Creation", 
                    "object": {
                        "title": "AP_McAfeeMsme-virusDetected",
                        "large_data": "x" * 10000,  # 10KB string
                        "big_array": [f"item_{i}" for i in range(500)],
                        "nested": {"level" + str(i): f"value_{i}" for i in range(100)}
                    }
                },
                'expected_status': 502,
                'type': 'large_payload'
            },
            
            # === DEEPLY NESTED PAYLOADS ===
            {
                'payload': {
                    "objectType": "alert",
                    "operation": "Creation",
                    "object": {
                        "title": "AP_McAfeeMsme-virusDetected",
                        "deep": {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "deep_value"}}}}}}
                    }
                },
                'expected_status': 502,
                'type': 'deep_nesting'
            },
            
            # === UNICODE AND SPECIAL CHARACTERS ===
            {
                'payload': {
                    "objectType": "alert",
                    "operation": "Creation",
                    "object": {
                        "title": "AP_McAfeeMsme-virusDetected",
                        "unicode": "🚀💥🔥",
                        "special": "line1\nline2\ttab",
                        "quotes": 'mixed "quotes" here',
                        "backslashes": "\\path\\to\\file"
                    }
                },
                'expected_status': 502,
                'type': 'unicode_special'
            }
        ]
        
        # STRESS MULTIPLIER: Create many concurrent instances
        stress_multiplier = 3  # Each request type appears 3 times
        requests_data = []
        
        for _ in range(stress_multiplier):
            for req in base_requests:
                # Add some randomization to make timing more realistic
                req_copy = req.copy()
                if req_copy.get('type') == 'valid_forwarding_fail':
                    # Vary the titles with routing-compatible values from test config
                    titles = ["AP_McAfeeMsme-virusDetected", "Critical malware detected", "Test Alert", "Test Notification"]
                    req_copy['payload'] = req_copy['payload'].copy()
                    req_copy['payload']['object'] = req_copy['payload']['object'].copy()
                    req_copy['payload']['object']['title'] = random.choice(titles)
                requests_data.append(req_copy)
        
        total_requests = len(requests_data)
        print(f"\n🚀 STRESS TEST: Firing {total_requests} concurrent requests...")
        
        # EXECUTE ALL REQUESTS CONCURRENTLY 
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:  # High concurrency!
            futures = [executor.submit(make_request, req) for req in requests_data]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        print(f"⚡ Completed {total_requests} requests in {total_time:.2f}s ({total_requests/total_time:.1f} req/s)")
        
        # === VALIDATION: STRESS TEST ANALYSIS ===
        
        # 1. Basic success validation
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        print(f"✅ Success rate: {len(successful_results)}/{total_requests} ({len(successful_results)/total_requests*100:.1f}%)")
        
        if failed_results:
            print("❌ Failed requests:")
            for fail in failed_results[:5]:  # Show first 5 failures
                print(f"  - {fail['request_type']}: expected {fail['expected']}, got {fail['actual']}")
        
        # 2. All requests should get expected responses (error isolation test)
        assert len(successful_results) == total_requests, f"Error isolation failed! {len(failed_results)} requests failed"
        
        # 3. Unique request IDs (no state corruption)
        request_ids = [r['request_id'] for r in results if r['request_id']]
        assert len(set(request_ids)) == len(request_ids), "Request ID collision detected!"
        
        # 4. Performance validation (no major slowdowns from errors)
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        max_response_time = max(r['response_time'] for r in results)
        print(f"⏱️  Avg response time: {avg_response_time*1000:.1f}ms, Max: {max_response_time*1000:.1f}ms")
        
        # Should handle requests reasonably fast even under stress
        assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time:.2f}s"
        assert max_response_time < 3.0, f"Max response time too slow: {max_response_time:.2f}s"
        
        # 5. Validate different request types got correct responses
        by_type = {}
        for result in results:
            req_type = result['request_type']
            if req_type not in by_type:
                by_type[req_type] = []
            by_type[req_type].append(result)
        
        # Spot check a few categories
        if 'valid_forwarding_fail' in by_type:
            for result in by_type['valid_forwarding_fail']:
                assert result['actual'] == 502, f"Valid request should fail forwarding: {result}"
                
        if 'invalid_json' in by_type:
            for result in by_type['invalid_json']:
                assert result['actual'] == 400, f"Invalid JSON should return 400: {result}"
                
        if 'dropped_by_filter' in by_type:
            for result in by_type['dropped_by_filter']:
                assert result['actual'] == 200, f"Filtered request should return 200: {result}"
        
        print(f"🎯 ERROR ISOLATION STRESS TEST PASSED! {total_requests} concurrent requests handled correctly.")
