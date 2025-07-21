# tests/test_core/test_processor.py
from typing import Dict, Any
import pytest
from unittest.mock import Mock, patch

from flowbridge.core.processor import ProcessingPipeline
from flowbridge.core.context import RequestContext
from flowbridge.core.models import (
    DroppedResponse,
    FilteringSummary,
    ProcessingResult,
    RoutingFailureResponse,
    ForwardingFailureResponse
)
from flowbridge.core.filters import FilterResult
from flowbridge.core.router import RoutingResult
from flowbridge.core.forwarder import ForwardingResult
from flowbridge.utils.errors import ValidationError as AppValidationError



@pytest.fixture
def request_context() -> RequestContext:
    """Create a test request context."""
    return RequestContext()


# =============================================================================
# CORE PIPELINE FUNCTIONALITY TESTS
# =============================================================================

class TestProcessingPipelineCore:
    """Test suite for core ProcessingPipeline functionality (general validation and error handling)."""

    def test_invalid_request_validation(
        self,
        processing_pipeline: ProcessingPipeline,
        request_context: RequestContext
    ):
        """Test validation failure for non-dictionary payloads."""
        # Test string payload
        with pytest.raises(AppValidationError) as exc_info:
            processing_pipeline.process_webhook_request("not a dict", request_context)
        assert "Payload must be a JSON object (dictionary)" in str(exc_info.value)
        
        # Test array payload
        with pytest.raises(AppValidationError) as exc_info:
            processing_pipeline.process_webhook_request([1, 2, 3], request_context)
        assert "Payload must be a JSON object (dictionary)" in str(exc_info.value)
        
        # Test number payload
        with pytest.raises(AppValidationError) as exc_info:
            processing_pipeline.process_webhook_request(123, request_context)
        assert "Payload must be a JSON object (dictionary)" in str(exc_info.value)

    def test_schema_free_operation(
        self,
        processing_pipeline: ProcessingPipeline,
        request_context: RequestContext
    ):
        """Test that the processor accepts any valid JSON dictionary structure."""
        # Mock the filter engine to pass any payload
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=0,
            rule_results=[],
            default_action_applied=False
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Test various JSON structures
            test_payloads = [
                {"any": "structure"},
                {"nested": {"deep": {"structure": "works"}}},
                {"arrays": [1, 2, 3], "mixed": True, "number": 42},
                {"empty": {}},
                {"null_values": None, "boolean": False}
            ]
            
            for payload in test_payloads:
                result = processing_pipeline.process_webhook_request(payload, request_context)
                assert isinstance(result, ProcessingResult)
                assert result.is_dropped is False

    def test_filter_engine_error_handling(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test handling of filter engine errors."""
        # Mock the filter engine to raise an error
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', side_effect=Exception("Filter evaluation failed")):
            # Process valid payload
            payload = webhook_payloads["valid_basic"]
            
            with pytest.raises(Exception) as exc_info:
                processing_pipeline.process_webhook_request(payload, request_context)
            
            assert "Filter evaluation failed" in str(exc_info.value)

    def test_non_dictionary_payloads(
        self,
        processing_pipeline: ProcessingPipeline,
        error_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test handling of non-dictionary payloads."""
        # Test various non-dictionary types that should be rejected
        non_dict_payloads = [
            error_payloads["string_payload"],
            error_payloads["number_payload"],
            error_payloads["boolean_payload"],
            error_payloads["null_payload"],
            error_payloads["array_root"]
        ]
        
        for payload in non_dict_payloads:
            with pytest.raises(AppValidationError) as exc_info:
                processing_pipeline.process_webhook_request(payload, request_context)
            assert "Payload must be a JSON object (dictionary)" in str(exc_info.value)

    def test_valid_dictionary_with_mixed_types(
        self,
        processing_pipeline: ProcessingPipeline,
        request_context: RequestContext
    ):
        """Test that dictionaries with any value types are accepted."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=0,
            rule_results=[],
            default_action_applied=False  # Rules passed (or no rules evaluated)
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # This should be perfectly valid in schema-free operation
            payload = {
                "objectType": 123,           # number
                "operation": True,           # boolean
                "object": "not an object",   # string
                "null_field": None,          # null
                "array_field": [1, 2, 3],    # array
                "nested": {"any": "structure"} # nested object
            }
            
            result = processing_pipeline.process_webhook_request(payload, request_context)
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False

    def test_empty_dictionary(
        self,
        processing_pipeline: ProcessingPipeline,
        error_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test handling of empty dictionary payload."""
        # Empty dictionary: rules will likely fail, default_action="drop" 
        mock_filter_result = FilterResult(
            passed=False,  # Rules fail (can't extract fields from empty dict)
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=True  # Rules failed, default action applied
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            payload = error_payloads["empty_object"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is True  # Dropped due to default action

    def test_null_field_handling(
        self,
        processing_pipeline: ProcessingPipeline,
        request_context: RequestContext
    ):
        """Test handling of payloads with null fields."""
        # This should work fine - null fields are valid in schema-free operation
        payload = {"field1": None, "field2": "value"}
        
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=0,
            rule_results=[],
            default_action_applied=False
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            result = processing_pipeline.process_webhook_request(payload, request_context)
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False

    def test_array_root_validation(
        self,
        processing_pipeline: ProcessingPipeline,
        request_context: RequestContext
    ):
        """Test validation of array root payload."""
        # Array root should be rejected since filtering requires dictionary
        payload = [{"objectType": "alert"}]
        
        with pytest.raises(AppValidationError) as exc_info:
            processing_pipeline.process_webhook_request(payload, request_context)
        
        assert "Payload must be a JSON object (dictionary)" in str(exc_info.value)


# =============================================================================
# FILTERING STAGE INTEGRATION TESTS  
# =============================================================================

class TestFilteringStageIntegration:
    """Test suite for filtering stage integration within the processing pipeline."""

    def test_process_valid_basic_request_dropped(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test processing of a valid basic request that should be dropped."""
        # Configure mock filter engine: rules fail, default_action="drop"
        mock_filter_result = FilterResult(
            passed=False,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=True  # Rules failed, default action applied
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Process valid basic payload
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)

            # Verify result
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is True
            assert result.request_context == request_context
            assert isinstance(result.filtering_summary, FilteringSummary)
            assert result.filtering_summary.rules_evaluated == 2
            assert result.filtering_summary.default_action_applied is True

    def test_process_valid_complex_request_pass(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test processing of a valid complex request that should pass."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False  # Rules passed, no default action needed
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Process valid complex payload
            payload = webhook_payloads["valid_complex"]
            result = processing_pipeline.process_webhook_request(payload, request_context)

            # Verify result
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False
            assert result.request_context == request_context
            assert isinstance(result.filtering_summary, FilteringSummary)

    def test_empty_rules_default_action(
        self,
        processing_pipeline_empty_rules: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test processing with empty rules using default action."""
        # Configure mock filter engine: no rules, default_action="pass"
        mock_filter_result = FilterResult(
            passed=True,  # passes because default_action is "pass"
            rules_evaluated=0,
            rule_results=[],
            default_action_applied=True  # No rules, default action applied
        )
        
        with patch.object(processing_pipeline_empty_rules.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Process valid payload with empty rules
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline_empty_rules.process_webhook_request(payload, request_context)

            # Verify default action was applied
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False  # passes because default action is "pass"
            assert result.filtering_summary.default_action_applied is True

    def test_request_context_progression(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test request context progression through pipeline stages."""
        # Configure mock filter engine: rules fail, default_action="drop"
        mock_filter_result = FilterResult(
            passed=False,
            rules_evaluated=1,
            rule_results=[],
            default_action_applied=True  # Rules failed, default action applied
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Process valid payload
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)

            # Verify context progression
            assert "validation" in request_context.processing_stages
            assert "filtering" in request_context.processing_stages
            assert "payload" in request_context.metadata
            assert request_context.metadata["payload"] == payload

    def test_to_response_dropped_request(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test response generation for dropped requests."""
        # Configure mock filter engine: rules fail, default_action="drop"
        mock_filter_result = FilterResult(
            passed=False,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=True  # Rules failed, default action applied
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Process valid payload
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)

            # Test response generation
            response = result.to_response()
            assert isinstance(response, DroppedResponse)
            assert response.status == "processed"
            assert response.result == "dropped"
            assert response.request_id == str(request_context.request_id)

    def test_to_response_passed_request(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test response generation for passed requests with successful forwarding."""
        from flowbridge.core.forwarder import ForwardingResult
        from flowbridge.core.models import RoutedResponse
        
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False  # Rules passed, no default action needed
        )
        
        # Configure mock forwarder: forwarding succeeds
        mock_forwarding_result = ForwardingResult(
            success=True,
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"result": "success"}',
            error_message=None,
            error_type=None,
            destination_url="http://localhost:5000/endpoint1",
            response_time_ms=150.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            # Process valid payload
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)

            # Verify the forwarding was successful in the result
            assert result.request_context.forwarding.success == True
            assert result.destination_response is not None

            # Test response generation
            response = result.to_response()
            assert isinstance(response, RoutedResponse)
            assert response.status == "forwarded"
            assert response.result == "success"
            assert response.request_id == str(request_context.request_id)
            assert response.destination_response.status_code == 200
            assert response.destination_response.destination_url == "http://localhost:5000/endpoint1"

    def test_rules_fail_but_default_pass(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test scenario where rules fail but default_action is pass."""
        # Configure mock filter engine: rules fail, but default_action="pass"
        mock_filter_result = FilterResult(
            passed=True,  # Passes due to default_action="pass"
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=True  # Rules failed, default action applied
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False  # Not dropped due to default_action="pass"
            assert result.filtering_summary.default_action_applied is True


# =============================================================================
# ROUTING STAGE INTEGRATION TESTS
# =============================================================================

class TestRoutingStageIntegration:
    """Test suite for routing and forwarding stage integration within the processing pipeline."""

    def test_routing_stage_success_flow(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test successful routing stage integration within pipeline."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False
        )
        
        # Configure mock routing engine: routing succeeds
        mock_routing_result = RoutingResult(
            success=True,
            destination_url="http://localhost:5000/endpoint",
            field_path="object.title",
            matched_value="test-payload-1",
            rule_index=0,
            error_message=None,
            extraction_result=None
        )
        
        # Configure mock forwarder: forwarding succeeds
        mock_forwarding_result = ForwardingResult(
            success=True,
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"result": "success"}',
            error_message=None,
            error_type=None,
            destination_url="http://localhost:5000/endpoint",
            response_time_ms=100.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify complete pipeline flow
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False
            assert result.request_context.routing.success is True
            assert result.destination_response is not None
            
            # Verify routing context
            routing_context = result.request_context.routing
            assert routing_context is not None
            assert routing_context.success is True
            assert routing_context.destination_url == "http://localhost:5000/endpoint"
            assert routing_context.field_path == "object.title"
            assert routing_context.matched_value == "test-payload-1"
            assert routing_context.rule_index == 0
            
            # Verify forwarding context
            forwarding_context = result.request_context.forwarding
            assert forwarding_context is not None
            assert forwarding_context.success is True
            assert forwarding_context.destination_url == "http://localhost:5000/endpoint"
            assert forwarding_context.response_time_ms == 100.0

    def test_routing_stage_failure_no_matching_rules(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test routing stage failure when no rules match."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False
        )
        
        # Configure mock routing engine: no matching rules
        mock_routing_result = RoutingResult(
            success=False,
            destination_url=None,
            field_path="object.title",
            matched_value="unknown-value",
            rule_index=None,
            error_message="No matching routing rule found for value: unknown-value",
            extraction_result=None
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify routing failure handling
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False
            assert result.request_context.routing.success is False
            assert result.destination_response is None
            
            # Verify routing context contains error
            routing_context = result.request_context.routing
            assert routing_context is not None
            assert routing_context.success is False
            assert routing_context.destination_url is None
            assert routing_context.error_message == "No matching routing rule found for value: unknown-value"
            
            # Verify no forwarding was attempted (default ForwardingContext with no changes)
            forwarding_context = result.request_context.forwarding
            assert forwarding_context is not None
            assert forwarding_context.success is False
            assert forwarding_context.destination_url is None
            assert forwarding_context.status_code is None

    def test_routing_stage_failure_missing_field(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test routing stage failure when routing field is missing."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False
        )
        
        # Configure mock routing engine: field extraction fails
        mock_routing_result = RoutingResult(
            success=False,
            destination_url=None,
            field_path="object.title",
            matched_value=None,
            rule_index=None,
            error_message="Could not extract routing field 'object.title' from payload",
            extraction_result=None
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify routing failure handling
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False
            assert result.request_context.routing.success is False
            
            # Verify routing context contains field extraction error
            routing_context = result.request_context.routing
            assert routing_context is not None
            assert routing_context.success is False
            assert routing_context.field_path == "object.title"
            assert routing_context.matched_value is None
            assert "Could not extract routing field" in routing_context.error_message

    def test_forwarding_stage_network_failure(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test forwarding stage failure due to network error."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False
        )
        
        # Configure mock routing engine: routing succeeds
        mock_routing_result = RoutingResult(
            success=True,
            destination_url="http://unreachable:5000/endpoint",
            field_path="object.title",
            matched_value="test-payload-1",
            rule_index=0,
            error_message=None,
            extraction_result=None
        )
        
        # Configure mock forwarder: network error
        mock_forwarding_result = ForwardingResult(
            success=False,
            status_code=None,
            headers={},
            content=None,
            error_message="Connection timeout after 2 seconds",
            error_type="CONNECTION_TIMEOUT",
            destination_url="http://unreachable:5000/endpoint",
            response_time_ms=2000.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify pipeline flow up to forwarding failure
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False
            assert result.request_context.routing.success is True
            assert result.destination_response is None
            
            # Verify routing was successful
            routing_context = result.request_context.routing
            assert routing_context.success is True
            
            # Verify forwarding failure
            forwarding_context = result.request_context.forwarding
            assert forwarding_context is not None
            assert forwarding_context.success is False
            assert forwarding_context.error_message == "Connection timeout after 2 seconds"
            assert forwarding_context.error_type == "CONNECTION_TIMEOUT"
            assert forwarding_context.response_time_ms == 2000.0

    def test_forwarding_stage_destination_error(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test forwarding stage with destination server error."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False
        )
        
        # Configure mock routing engine: routing succeeds
        mock_routing_result = RoutingResult(
            success=True,
            destination_url="http://localhost:5000/endpoint",
            field_path="object.title",
            matched_value="test-payload-1",
            rule_index=0,
            error_message=None,
            extraction_result=None
        )
        
        # Configure mock forwarder: destination returns error
        mock_forwarding_result = ForwardingResult(
            success=False,
            status_code=500,
            headers={"Content-Type": "application/json"},
            content=b'{"error": "Internal server error"}',
            error_message="HTTP 500: Internal Server Error",
            error_type="DESTINATION_ERROR",
            destination_url="http://localhost:5000/endpoint",
            response_time_ms=50.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify pipeline flow with destination error
            assert isinstance(result, ProcessingResult)
            assert result.is_dropped is False
            assert result.request_context.routing.success is True
            assert result.destination_response is None
            
            # Verify forwarding captured destination error
            forwarding_context = result.request_context.forwarding
            assert forwarding_context is not None
            assert forwarding_context.success is False
            assert forwarding_context.status_code == 500
            assert forwarding_context.error_type == "DESTINATION_ERROR"
            assert "Internal Server Error" in forwarding_context.error_message

    def test_complete_pipeline_flow_processing_stages(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test that request context tracks all processing stages correctly."""
        # Configure mocks for complete successful flow
        mock_filter_result = FilterResult(passed=True, rules_evaluated=2, rule_results=[], default_action_applied=False)
        mock_routing_result = RoutingResult(
            success=True, destination_url="http://localhost:5000/endpoint", field_path="object.title",
            matched_value="test-payload-1", rule_index=0, error_message=None, extraction_result=None
        )
        mock_forwarding_result = ForwardingResult(
            success=True, status_code=200, headers={}, content=b'{"result": "success"}',
            error_message=None, error_type=None, destination_url="http://localhost:5000/endpoint", response_time_ms=100.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify all processing stages were tracked
            stages = result.request_context.processing_stages
            assert "validation" in stages
            assert "filtering" in stages
            assert "routing" in stages
            assert "forwarding" in stages
            
            # Verify stage progression order (based on timestamps)
            stage_times = [stages[stage] for stage in [
                "validation",
                "filtering",
                "routing",
                "forwarding"
            ]]
            assert stage_times == sorted(stage_times)  # Should be in chronological order

    def test_pipeline_error_stage_tracking(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test that processing stages are tracked even when errors occur."""
        # Configure mocks for routing failure
        mock_filter_result = FilterResult(passed=True, rules_evaluated=2, rule_results=[], default_action_applied=False)
        mock_routing_result = RoutingResult(
            success=False, destination_url=None, field_path="object.title", matched_value="unknown-value",
            rule_index=None, error_message="No matching routing rule", extraction_result=None
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify stages up to routing were tracked
            stages = result.request_context.processing_stages
            assert "validation" in stages
            assert "filtering" in stages
            assert "routing" in stages
            # Forwarding should not be tracked since routing failed
            assert "forwarding" not in stages

    def test_request_context_metadata_progression(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test that request context metadata is properly maintained throughout routing."""
        # Configure mocks for successful flow
        mock_filter_result = FilterResult(passed=True, rules_evaluated=2, rule_results=[], default_action_applied=False)
        mock_routing_result = RoutingResult(
            success=True, destination_url="http://localhost:5000/endpoint", field_path="object.title",
            matched_value="test-payload-1", rule_index=0, error_message=None, extraction_result=None
        )
        mock_forwarding_result = ForwardingResult(
            success=True, status_code=200, headers={}, content=b'{"result": "success"}',
            error_message=None, error_type=None, destination_url="http://localhost:5000/endpoint", response_time_ms=100.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Verify payload is preserved in metadata
            assert "payload" in result.request_context.metadata
            assert result.request_context.metadata["payload"] == payload
            
            # Verify all context sections are populated
            assert result.request_context.filtering is not None
            assert result.request_context.routing is not None
            assert result.request_context.forwarding is not None
            
            # Verify context continuity
            assert result.request_context.request_id == request_context.request_id

    def test_response_generation_routing_failure(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test response generation for routing failures returns 404."""
        # Configure mocks for routing failure
        mock_filter_result = FilterResult(passed=True, rules_evaluated=2, rule_results=[], default_action_applied=False)
        mock_routing_result = RoutingResult(
            success=False, destination_url=None, field_path="object.title", matched_value="unknown-value",
            rule_index=None, error_message="No matching routing rule found", extraction_result=None
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Test response generation
            response = result.to_response()
            assert isinstance(response, RoutingFailureResponse)
            assert response.status == "failed"
            assert response.result == "routing_failed"
            assert response.request_id == str(request_context.request_id)
            assert "No matching routing rule found" in response.error_message

    def test_response_generation_forwarding_failure(
        self,
        processing_pipeline: ProcessingPipeline,
        webhook_payloads: Dict[str, Any],
        request_context: RequestContext
    ):
        """Test response generation for forwarding failures returns appropriate error response."""
        # Configure mocks for forwarding failure
        mock_filter_result = FilterResult(passed=True, rules_evaluated=2, rule_results=[], default_action_applied=False)
        mock_routing_result = RoutingResult(
            success=True, destination_url="http://localhost:5000/endpoint", field_path="object.title",
            matched_value="test-payload-1", rule_index=0, error_message=None, extraction_result=None
        )
        mock_forwarding_result = ForwardingResult(
            success=False, status_code=None, headers={}, content=None,
            error_message="Connection timeout", error_type="CONNECTION_TIMEOUT",
            destination_url="http://localhost:5000/endpoint", response_time_ms=2000.0
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result), \
             patch.object(processing_pipeline.routing_engine, 'find_destination', return_value=mock_routing_result), \
             patch.object(processing_pipeline.request_forwarder, 'forward_request', return_value=mock_forwarding_result):
            
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)
            
            # Test response generation
            response = result.to_response()
            assert isinstance(response, ForwardingFailureResponse)
            assert response.status == "failed"
            assert response.result == "forwarding_failed"
            assert response.request_id == str(request_context.request_id)
            assert response.forwarding_summary.error_type == "CONNECTION_TIMEOUT"
