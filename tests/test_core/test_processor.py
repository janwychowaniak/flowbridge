# tests/test_core/test_processor.py
from typing import Dict, Any
import pytest
from unittest.mock import Mock, patch

from flowbridge.core.processor import ProcessingPipeline, ProcessingStage
from flowbridge.core.context import RequestContext
from flowbridge.core.models import (
    DroppedResponse,
    FilteringSummary,
    ProcessingResult
)
from flowbridge.core.filters import FilterResult
from flowbridge.config.models import FilterCondition
from flowbridge.utils.errors import ValidationError as AppValidationError



@pytest.fixture
def request_context() -> RequestContext:
    """Create a test request context."""
    return RequestContext()



class TestProcessingPipeline:
    """Test suite for the ProcessingPipeline class."""


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
        """Test response generation for passed requests."""
        # Configure mock filter engine: rules pass
        mock_filter_result = FilterResult(
            passed=True,
            rules_evaluated=2,
            rule_results=[],
            default_action_applied=False  # Rules passed, no default action needed
        )
        
        with patch.object(processing_pipeline.filter_engine, 'evaluate_payload', return_value=mock_filter_result):
            # Process valid payload
            payload = webhook_payloads["valid_basic"]
            result = processing_pipeline.process_webhook_request(payload, request_context)

            # Test response generation
            response = result.to_response()
            assert isinstance(response, dict)
            assert response["status"] == "processing"
            assert response["request_id"] == str(request_context.request_id)
            # With routing implemented, we expect a different message
            assert "response type unclear" in response["message"]
            assert response["stage"] == "ROUTING"


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
