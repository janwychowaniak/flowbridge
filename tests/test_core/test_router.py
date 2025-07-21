import pytest
from unittest.mock import Mock, patch
from pydantic import HttpUrl

from flowbridge.core.router import RoutingEngine, RoutingResult
from flowbridge.core.field_extractor import FieldExtractionResult
from flowbridge.config.models import RouteMapping
from flowbridge.utils.errors import RoutingError


class TestRoutingEngine:
    """Test suite for RoutingEngine component."""

    @pytest.fixture
    def basic_route_mappings(self):
        """Create basic route mappings for testing."""
        return [
            RouteMapping(
                field="object.title",
                mappings={
                    "virus-detected": HttpUrl("http://security-team.com/alerts"),
                    "malware-found": HttpUrl("http://incident-response.com/alerts"),
                    "network-intrusion": HttpUrl("http://network-team.com/alerts")
                }
            )
        ]

    @pytest.fixture
    def multiple_route_mappings(self):
        """Create multiple route mappings for first-match-wins testing."""
        return [
            RouteMapping(
                field="alert.type",
                mappings={
                    "critical": HttpUrl("http://critical-alerts.com/api"),
                    "warning": HttpUrl("http://warning-alerts.com/api")
                }
            ),
            RouteMapping(
                field="object.title", 
                mappings={
                    "virus-detected": HttpUrl("http://fallback-security.com/alerts"),
                    "test-alert": HttpUrl("http://test-destination.com/api")
                }
            )
        ]

    @pytest.fixture
    def deep_nested_route_mappings(self):
        """Create route mappings with deep nested field paths."""
        return [
            RouteMapping(
                field="data.attributes.metadata.category.type",
                mappings={
                    "security": HttpUrl("http://deep-security.com/api"),
                    "network": HttpUrl("http://deep-network.com/api")
                }
            )
        ]

    @pytest.fixture
    def routing_engine(self, basic_route_mappings):
        """Create RoutingEngine instance with basic configuration."""
        return RoutingEngine(basic_route_mappings)

    @pytest.fixture
    def empty_routing_engine(self):
        """Create RoutingEngine instance with no routing rules."""
        return RoutingEngine([])

    def test_routing_engine_initialization(self, basic_route_mappings):
        """Test RoutingEngine initialization with configuration."""
        engine = RoutingEngine(basic_route_mappings)
        assert engine.routing_rules == basic_route_mappings
        assert engine.field_extractor is not None

    def test_routing_engine_initialization_empty_rules(self):
        """Test RoutingEngine initialization with empty rules."""
        engine = RoutingEngine([])
        assert engine.routing_rules == []
        assert engine.field_extractor is not None

    def test_successful_route_matching(self, routing_engine):
        """Test successful routing with exact match."""
        payload = {
            "object": {
                "title": "virus-detected",
                "severity": 8
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert result.success
        assert result.destination_url == "http://security-team.com/alerts"
        assert result.matched_value == "virus-detected"
        assert result.field_path == "object.title"
        assert result.rule_index == 0
        assert result.error_message is None
        assert result.extraction_result is not None
        assert result.extraction_result.success

    def test_successful_route_matching_different_values(self, routing_engine):
        """Test successful routing with different mapping values."""
        test_cases = [
            ("malware-found", "http://incident-response.com/alerts"),
            ("network-intrusion", "http://network-team.com/alerts")
        ]
        
        for title_value, expected_url in test_cases:
            payload = {
                "object": {
                    "title": title_value,
                    "details": "test"
                }
            }
            
            result = routing_engine.find_destination(payload)
            
            assert result.success
            assert result.destination_url == expected_url
            assert result.matched_value == title_value
            assert result.field_path == "object.title"
            assert result.rule_index == 0

    def test_no_matching_routes(self, routing_engine):
        """Test routing failure when no rules match."""
        payload = {
            "object": {
                "title": "unknown-alert-type",
                "severity": 5
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value is None  # No match found, so matched_value is None
        assert result.field_path == "object.title"
        assert result.rule_index is None
        assert "No matching routing rule found" in result.error_message
        assert result.extraction_result is None

    def test_no_routing_rules_configured(self, empty_routing_engine):
        """Test routing failure when no rules are configured."""
        payload = {
            "object": {
                "title": "any-alert",
                "severity": 5
            }
        }
        
        result = empty_routing_engine.find_destination(payload)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value is None
        assert result.field_path == ""
        assert result.rule_index is None
        assert "No routing rules configured" in result.error_message
        assert result.extraction_result is None

    def test_field_extraction_failure(self, routing_engine):
        """Test routing failure when field extraction fails."""
        payload = {
            "different_structure": {
                "title": "virus-detected"
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value is None
        assert result.field_path == "object.title"
        assert result.rule_index is None
        assert "No matching routing rule found" in result.error_message

    def test_field_value_is_none(self, routing_engine):
        """Test routing failure when extracted field value is None."""
        payload = {
            "object": {
                "title": None,
                "severity": 5
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value is None
        assert result.field_path == "object.title"
        assert result.rule_index is None
        assert "No matching routing rule found" in result.error_message

    def test_first_match_wins_logic(self):
        """Test that first matching rule wins when multiple rules could match."""
        route_mappings = [
            RouteMapping(
                field="object.title",
                mappings={
                    "test-alert": HttpUrl("http://first-destination.com/api")
                }
            ),
            RouteMapping(
                field="object.title", 
                mappings={
                    "test-alert": HttpUrl("http://second-destination.com/api")
                }
            )
        ]
        
        engine = RoutingEngine(route_mappings)
        payload = {
            "object": {
                "title": "test-alert"
            }
        }
        
        result = engine.find_destination(payload)
        
        assert result.success
        assert result.destination_url == "http://first-destination.com/api"
        assert result.rule_index == 0

    def test_multiple_rules_first_match_wins(self, multiple_route_mappings):
        """Test first-match-wins with different field paths."""
        engine = RoutingEngine(multiple_route_mappings)
        
        # Test payload that matches first rule
        payload1 = {
            "alert": {
                "type": "critical"
            },
            "object": {
                "title": "virus-detected"  # This would match second rule
            }
        }
        
        result1 = engine.find_destination(payload1)
        
        assert result1.success
        assert result1.destination_url == "http://critical-alerts.com/api"
        assert result1.rule_index == 0
        assert result1.field_path == "alert.type"

    def test_second_rule_matching(self, multiple_route_mappings):
        """Test matching second rule when first rule doesn't match."""
        engine = RoutingEngine(multiple_route_mappings)
        
        # Test payload that only matches second rule
        payload = {
            "alert": {
                "type": "info"  # Doesn't match first rule
            },
            "object": {
                "title": "test-alert"  # Matches second rule
            }
        }
        
        result = engine.find_destination(payload)
        
        assert result.success
        assert result.destination_url == "http://test-destination.com/api"
        assert result.rule_index == 1
        assert result.field_path == "object.title"

    def test_deep_nested_field_extraction(self, deep_nested_route_mappings):
        """Test routing with deep nested field paths."""
        engine = RoutingEngine(deep_nested_route_mappings)
        
        payload = {
            "data": {
                "attributes": {
                    "metadata": {
                        "category": {
                            "type": "security"
                        }
                    }
                }
            }
        }
        
        result = engine.find_destination(payload)
        
        assert result.success
        assert result.destination_url == "http://deep-security.com/api"
        assert result.matched_value == "security"
        assert result.field_path == "data.attributes.metadata.category.type"

    def test_case_sensitive_matching(self, routing_engine):
        """Test that routing matching is case-sensitive."""
        payload = {
            "object": {
                "title": "VIRUS-DETECTED"  # Different case
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert not result.success
        assert result.matched_value is None  # No match found due to case sensitivity
        assert "No matching routing rule found" in result.error_message

    def test_string_conversion_of_field_values(self):
        """Test that field values are converted to strings for matching."""
        # Create a route mapping that expects string representation of number
        route_mappings = [
            RouteMapping(
                field="alert.code",
                mappings={
                    "404": HttpUrl("http://error-handler.com/api"),
                    "200": HttpUrl("http://success-handler.com/api")
                }
            )
        ]
        
        engine = RoutingEngine(route_mappings)
        
        # Test with numeric value
        payload = {
            "alert": {
                "code": 404  # Numeric value
            }
        }
        
        result = engine.find_destination(payload)
        
        assert result.success
        assert result.destination_url == "http://error-handler.com/api"
        assert result.matched_value == "404"

    def test_evaluate_routing_rule_success(self, routing_engine):
        """Test successful evaluation of single routing rule."""
        rule = routing_engine.routing_rules[0]
        payload = {
            "object": {
                "title": "virus-detected"
            }
        }
        
        result = routing_engine.evaluate_routing_rule(payload, rule, 0)
        
        assert result.success
        assert result.destination_url == "http://security-team.com/alerts"
        assert result.matched_value == "virus-detected"
        assert result.field_path == "object.title"
        assert result.rule_index == 0
        assert result.error_message is None

    def test_evaluate_routing_rule_field_extraction_failure(self, routing_engine):
        """Test routing rule evaluation with field extraction failure."""
        rule = routing_engine.routing_rules[0]
        payload = {
            "wrong_structure": {
                "title": "virus-detected"
            }
        }
        
        result = routing_engine.evaluate_routing_rule(payload, rule, 0)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value is None
        assert result.field_path == "object.title"
        assert result.rule_index == 0
        assert "Field extraction failed" in result.error_message

    def test_evaluate_routing_rule_null_field_value(self, routing_engine):
        """Test routing rule evaluation with null extracted field value."""
        rule = routing_engine.routing_rules[0]
        payload = {
            "object": {
                "title": None
            }
        }
        
        result = routing_engine.evaluate_routing_rule(payload, rule, 0)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value is None
        assert result.field_path == "object.title"
        assert result.rule_index == 0
        assert "Extracted field value is None" in result.error_message

    def test_evaluate_routing_rule_no_mapping_match(self, routing_engine):
        """Test routing rule evaluation with no mapping match."""
        rule = routing_engine.routing_rules[0]
        payload = {
            "object": {
                "title": "unknown-alert"
            }
        }
        
        result = routing_engine.evaluate_routing_rule(payload, rule, 0)
        
        assert not result.success
        assert result.destination_url is None
        assert result.matched_value == "unknown-alert"
        assert result.field_path == "object.title"
        assert result.rule_index == 0
        assert "No mapping found for value: unknown-alert" in result.error_message

    @patch('flowbridge.core.router.logger')
    def test_logging_on_successful_routing(self, mock_logger, routing_engine):
        """Test that successful routing generates appropriate log messages."""
        payload = {
            "object": {
                "title": "virus-detected"
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert result.success
        mock_logger.info.assert_called()
        # Verify the log call contains routing decision information
        log_calls = mock_logger.info.call_args_list
        assert any("Routing decision made" in str(call) for call in log_calls)

    @patch('flowbridge.core.router.logger')
    def test_logging_on_no_rules_configured(self, mock_logger, empty_routing_engine):
        """Test logging when no routing rules are configured."""
        payload = {"object": {"title": "test"}}
        
        result = empty_routing_engine.find_destination(payload)
        
        assert not result.success
        mock_logger.info.assert_called_with("No routing rules configured, dropping request")

    @patch('flowbridge.core.router.logger')
    def test_logging_on_no_match_found(self, mock_logger, routing_engine):
        """Test logging when no routing rules match."""
        payload = {
            "object": {
                "title": "unknown-alert"
            }
        }
        
        result = routing_engine.find_destination(payload)
        
        assert not result.success
        mock_logger.info.assert_called_with("No routing rules matched, dropping request")

    def test_routing_result_dataclass_structure(self):
        """Test RoutingResult dataclass structure and fields."""
        result = RoutingResult(
            success=True,
            destination_url="http://test.com",
            matched_value="test-value",
            field_path="test.field",
            rule_index=0,
            error_message=None,
            extraction_result=None
        )
        
        assert result.success
        assert result.destination_url == "http://test.com"
        assert result.matched_value == "test-value"
        assert result.field_path == "test.field"
        assert result.rule_index == 0
        assert result.error_message is None
        assert result.extraction_result is None

    def test_http_url_to_string_conversion(self):
        """Test that HttpUrl objects are properly converted to strings."""
        route_mappings = [
            RouteMapping(
                field="test.field",
                mappings={
                    "test": HttpUrl("https://example.com/webhook")
                }
            )
        ]
        
        engine = RoutingEngine(route_mappings)
        payload = {
            "test": {
                "field": "test"
            }
        }
        
        result = engine.find_destination(payload)
        
        assert result.success
        assert isinstance(result.destination_url, str)
        assert result.destination_url == "https://example.com/webhook"

    def test_exception_handling_in_rule_evaluation(self, routing_engine):
        """Test exception handling during rule evaluation."""
        # Mock the field extractor to raise an exception
        with patch.object(routing_engine.field_extractor, 'extract_field') as mock_extract:
            mock_extract.side_effect = Exception("Mock extraction error")
            
            payload = {
                "object": {
                    "title": "virus-detected"
                }
            }
            
            result = routing_engine.find_destination(payload)
            
            # Should continue to next rule or fail gracefully
            assert not result.success
            assert "No matching routing rule found" in result.error_message

    def test_empty_payload_handling(self, routing_engine):
        """Test routing behavior with empty payload."""
        payload = {}
        
        result = routing_engine.find_destination(payload)
        
        assert not result.success
        assert "No matching routing rule found" in result.error_message

    def test_malformed_payload_handling(self, routing_engine):
        """Test routing behavior with malformed payload structure."""
        payloads = [
            {"object": {}},  # Missing title field
            {"object": {"title": ""}},  # Empty title
            {"object": {"different_field": "value"}},  # Wrong field name
        ]
        
        for payload in payloads:
            result = routing_engine.find_destination(payload)
            assert not result.success 