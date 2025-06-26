import pytest
from flowbridge.core.filters import (
    FilterEngine,
    FilterOperator,
    LogicOperator,
    FilterConfig,
    FilterRule,
    FilterEvaluator
)


class TestFilterEngine:
    @pytest.fixture
    def config(self):
        return FilterConfig(
            default_action="drop",
            conditions={
                "logic": "AND",
                "rules": [
                    {
                        "field": "objectType",
                        "operator": "equals",
                        "value": "alert"
                    },
                    {
                        "field": "severity.level",
                        "operator": "greater_than",
                        "value": 3
                    }
                ]
            }
        )
        
    @pytest.fixture
    def engine(self, config):
        return FilterEngine(config)
        
    def test_matching_payload(self, engine):
        payload = {
            "objectType": "alert",
            "severity": {"level": 5}
        }
        result = engine.evaluate_payload(payload)
        assert result.passed
        assert result.rules_evaluated == 2
        assert not result.default_action_applied
        
    def test_non_matching_payload(self, engine):
        payload = {
            "objectType": "alert",
            "severity": {"level": 2}
        }
        result = engine.evaluate_payload(payload)
        assert not result.passed
        assert result.rules_evaluated == 2
        
    def test_missing_field(self, engine):
        payload = {"objectType": "alert"}
        result = engine.evaluate_payload(payload)
        assert not result.passed
        assert any(r["error"] is not None for r in result.rule_results)
        
    def test_type_coercion(self, engine):
        payload = {
            "objectType": "alert",
            "severity": {"level": "5"}  # String instead of int
        }
        result = engine.evaluate_payload(payload)
        assert result.passed  # Should coerce "5" to 5 for comparison

    # New comprehensive tests
    def test_empty_rules_configuration(self):
        """Test behavior with no filter rules."""
        config = FilterConfig(
            default_action="pass",
            conditions={"logic": "AND", "rules": []}
        )
        engine = FilterEngine(config)
        
        payload = {"any": "data"}
        result = engine.evaluate_payload(payload)
        
        assert result.passed
        assert result.rules_evaluated == 0
        assert result.default_action_applied
        assert len(result.rule_results) == 0

    def test_single_rule_scenarios(self):
        """Test single rule with different logic operators."""
        # Single rule with AND logic
        config_and = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "AND",
                "rules": [{"field": "status", "operator": "equals", "value": "active"}]
            }
        )
        engine_and = FilterEngine(config_and)
        
        payload = {"status": "active"}
        result = engine_and.evaluate_payload(payload)
        assert result.passed
        assert result.rules_evaluated == 1
        
        # Single rule with OR logic (should behave the same)
        config_or = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "OR",
                "rules": [{"field": "status", "operator": "equals", "value": "active"}]
            }
        )
        engine_or = FilterEngine(config_or)
        
        result = engine_or.evaluate_payload(payload)
        assert result.passed
        assert result.rules_evaluated == 1

    def test_or_logic_combination(self):
        """Test OR logic with multiple rules."""
        config = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "OR",
                "rules": [
                    {"field": "priority", "operator": "equals", "value": "high"},
                    {"field": "category", "operator": "equals", "value": "security"},
                    {"field": "status", "operator": "equals", "value": "critical"}
                ]
            }
        )
        engine = FilterEngine(config)
        
        # Test: Only first rule matches
        payload1 = {"priority": "high", "category": "normal", "status": "ok"}
        result1 = engine.evaluate_payload(payload1)
        assert result1.passed
        
        # Test: Only middle rule matches
        payload2 = {"priority": "low", "category": "security", "status": "ok"}
        result2 = engine.evaluate_payload(payload2)
        assert result2.passed
        
        # Test: Multiple rules match
        payload3 = {"priority": "high", "category": "security", "status": "ok"}
        result3 = engine.evaluate_payload(payload3)
        assert result3.passed
        
        # Test: No rules match
        payload4 = {"priority": "low", "category": "normal", "status": "ok"}
        result4 = engine.evaluate_payload(payload4)
        assert not result4.passed

    def test_default_action_scenarios(self):
        """Test different default actions."""
        # Default action: pass
        config_pass = FilterConfig(
            default_action="pass",
            conditions={"logic": "AND", "rules": []}
        )
        engine_pass = FilterEngine(config_pass)
        
        result = engine_pass.evaluate_payload({"any": "data"})
        assert result.passed
        assert result.default_action_applied
        
        # Default action: drop
        config_drop = FilterConfig(
            default_action="drop",
            conditions={"logic": "AND", "rules": []}
        )
        engine_drop = FilterEngine(config_drop)
        
        result = engine_drop.evaluate_payload({"any": "data"})
        assert not result.passed
        assert result.default_action_applied

    def test_non_dict_payload(self):
        """Test handling of non-dictionary payloads."""
        config = FilterConfig(
            default_action="drop",
            conditions={"logic": "AND", "rules": []}
        )
        engine = FilterEngine(config)
        
        # Test string payload
        result = engine.evaluate_payload("not_a_dict")
        assert not result.passed
        assert result.error_message == "Payload must be a dictionary"
        
        # Test list payload
        result = engine.evaluate_payload([1, 2, 3])
        assert not result.passed
        assert result.error_message == "Payload must be a dictionary"
        
        # Test None payload
        result = engine.evaluate_payload(None)
        assert not result.passed
        assert result.error_message == "Payload must be a dictionary"


class TestFilterOperators:
    """Test individual filter operators comprehensively."""
    
    @pytest.fixture
    def evaluator(self):
        return FilterEvaluator()

    def test_equals_operator(self, evaluator):
        """Test equals operator with various data types."""
        # String equality
        assert evaluator.apply_operator(FilterOperator.EQUALS, "test", "test")
        assert not evaluator.apply_operator(FilterOperator.EQUALS, "test", "other")
        
        # Number equality with type coercion
        assert evaluator.apply_operator(FilterOperator.EQUALS, 5, 5)
        assert evaluator.apply_operator(FilterOperator.EQUALS, "5", 5)  # Coercion
        assert evaluator.apply_operator(FilterOperator.EQUALS, 5.0, 5)  # Float to int
        
        # Boolean equality
        assert evaluator.apply_operator(FilterOperator.EQUALS, True, True)
        assert not evaluator.apply_operator(FilterOperator.EQUALS, True, False)
        
        # None equality
        assert evaluator.apply_operator(FilterOperator.EQUALS, None, None)
        assert not evaluator.apply_operator(FilterOperator.EQUALS, None, "test")

    def test_not_equals_operator(self, evaluator):
        """Test not_equals operator."""
        assert evaluator.apply_operator(FilterOperator.NOT_EQUALS, "test", "other")
        assert not evaluator.apply_operator(FilterOperator.NOT_EQUALS, "test", "test")
        
        # With type coercion
        assert not evaluator.apply_operator(FilterOperator.NOT_EQUALS, "5", 5)
        assert evaluator.apply_operator(FilterOperator.NOT_EQUALS, "5", 6)

    def test_in_operator(self, evaluator):
        """Test in operator with lists and strings."""
        # List membership
        assert evaluator.apply_operator(FilterOperator.IN, "apple", ["apple", "banana", "orange"])
        assert not evaluator.apply_operator(FilterOperator.IN, "grape", ["apple", "banana", "orange"])
        
        # Number in list
        assert evaluator.apply_operator(FilterOperator.IN, 5, [1, 3, 5, 7])
        assert not evaluator.apply_operator(FilterOperator.IN, 6, [1, 3, 5, 7])
        
        # String in string
        assert evaluator.apply_operator(FilterOperator.IN, "test", "testing")
        assert not evaluator.apply_operator(FilterOperator.IN, "xyz", "testing")

    def test_contains_any_operator(self, evaluator):
        """Test contains_any operator."""
        # String contains any of the substrings
        assert evaluator.apply_operator(FilterOperator.CONTAINS_ANY, "hello world", ["hello", "goodbye"])
        assert evaluator.apply_operator(FilterOperator.CONTAINS_ANY, "hello world", ["world", "universe"])
        assert not evaluator.apply_operator(FilterOperator.CONTAINS_ANY, "hello world", ["goodbye", "universe"])
        
        # List contains any of the elements
        field_value = ["tag1", "tag2", "tag3"]
        assert evaluator.apply_operator(FilterOperator.CONTAINS_ANY, field_value, ["tag1", "tag4"])
        assert not evaluator.apply_operator(FilterOperator.CONTAINS_ANY, field_value, ["tag4", "tag5"])

    def test_less_than_operator(self, evaluator):
        """Test less_than operator with type coercion."""
        # Number comparison
        assert evaluator.apply_operator(FilterOperator.LESS_THAN, 3, 5)
        assert not evaluator.apply_operator(FilterOperator.LESS_THAN, 5, 3)
        assert not evaluator.apply_operator(FilterOperator.LESS_THAN, 5, 5)
        
        # String to number coercion
        assert evaluator.apply_operator(FilterOperator.LESS_THAN, "3", 5)
        assert evaluator.apply_operator(FilterOperator.LESS_THAN, 3, "5")
        
        # Float comparisons
        assert evaluator.apply_operator(FilterOperator.LESS_THAN, 3.14, 4.0)
        assert evaluator.apply_operator(FilterOperator.LESS_THAN, 3, 3.5)

    def test_greater_than_operator(self, evaluator):
        """Test greater_than operator."""
        assert evaluator.apply_operator(FilterOperator.GREATER_THAN, 5, 3)
        assert not evaluator.apply_operator(FilterOperator.GREATER_THAN, 3, 5)
        assert not evaluator.apply_operator(FilterOperator.GREATER_THAN, 5, 5)
        
        # With type coercion
        assert evaluator.apply_operator(FilterOperator.GREATER_THAN, "5", 3)
        assert evaluator.apply_operator(FilterOperator.GREATER_THAN, 5, "3")

    def test_operator_type_coercion_edge_cases(self, evaluator):
        """Test edge cases in type coercion."""
        # Non-numeric strings
        assert not evaluator.apply_operator(FilterOperator.LESS_THAN, "abc", 5)
        assert not evaluator.apply_operator(FilterOperator.GREATER_THAN, "abc", 5)
        
        # Mixed types that can't be coerced
        assert not evaluator.apply_operator(FilterOperator.LESS_THAN, [], 5)
        assert not evaluator.apply_operator(FilterOperator.GREATER_THAN, {}, 5)

    def test_none_value_handling(self, evaluator):
        """Test operator behavior with None values."""
        # None equality
        assert evaluator.apply_operator(FilterOperator.EQUALS, None, None)
        assert not evaluator.apply_operator(FilterOperator.EQUALS, None, "test")
        
        # None with other operators
        assert not evaluator.apply_operator(FilterOperator.LESS_THAN, None, 5)
        assert not evaluator.apply_operator(FilterOperator.GREATER_THAN, None, 5)
        assert not evaluator.apply_operator(FilterOperator.IN, None, ["test"])


class TestComplexFilteringScenarios:
    """Test complex real-world filtering scenarios."""
    
    def test_security_alert_filtering(self):
        """Test filtering security alerts with complex rules."""
        config = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "AND",
                "rules": [
                    {"field": "alert.type", "operator": "equals", "value": "security"},
                    {"field": "alert.severity", "operator": "greater_than", "value": 3},
                    {"field": "alert.tags", "operator": "contains_any", "value": ["critical", "high"]},
                    {"field": "alert.source.verified", "operator": "equals", "value": True}
                ]
            }
        )
        engine = FilterEngine(config)
        
        # Should pass: Matches all criteria
        payload_pass = {
            "alert": {
                "type": "security",
                "severity": 5,
                "tags": ["critical", "network"],
                "source": {"verified": True}
            }
        }
        result = engine.evaluate_payload(payload_pass)
        assert result.passed
        
        # Should fail: Wrong type
        payload_fail1 = {
            "alert": {
                "type": "performance",
                "severity": 5,
                "tags": ["critical"],
                "source": {"verified": True}
            }
        }
        result = engine.evaluate_payload(payload_fail1)
        assert not result.passed
        
        # Should fail: Low severity
        payload_fail2 = {
            "alert": {
                "type": "security",
                "severity": 2,
                "tags": ["critical"],
                "source": {"verified": True}
            }
        }
        result = engine.evaluate_payload(payload_fail2)
        assert not result.passed

    def test_webhook_event_filtering_or_logic(self):
        """Test webhook event filtering with OR logic."""
        config = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "OR",
                "rules": [
                    {"field": "event.type", "operator": "in", "value": ["user.created", "user.updated", "user.deleted"]},
                    {"field": "event.priority", "operator": "equals", "value": "urgent"},
                    {"field": "event.metadata.admin_action", "operator": "equals", "value": True}
                ]
            }
        )
        engine = FilterEngine(config)
        
        # Should pass: Matches event type
        payload1 = {
            "event": {"type": "user.created", "priority": "normal", "metadata": {"admin_action": False}}
        }
        assert engine.evaluate_payload(payload1).passed
        
        # Should pass: Matches priority
        payload2 = {
            "event": {"type": "system.update", "priority": "urgent", "metadata": {"admin_action": False}}
        }
        assert engine.evaluate_payload(payload2).passed
        
        # Should pass: Matches admin_action
        payload3 = {
            "event": {"type": "system.update", "priority": "normal", "metadata": {"admin_action": True}}
        }
        assert engine.evaluate_payload(payload3).passed
        
        # Should fail: Matches none
        payload4 = {
            "event": {"type": "system.update", "priority": "normal", "metadata": {"admin_action": False}}
        }
        assert not engine.evaluate_payload(payload4).passed

    def test_mixed_data_types_filtering(self):
        """Test filtering with mixed data types and edge cases."""
        config = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "AND",
                "rules": [
                    {"field": "data.string_field", "operator": "equals", "value": "test"},
                    {"field": "data.number_field", "operator": "greater_than", "value": 10},
                    {"field": "data.boolean_field", "operator": "equals", "value": True},
                    {"field": "data.array_field", "operator": "contains_any", "value": ["item1", "item2"]},
                    {"field": "data.null_field", "operator": "equals", "value": None}
                ]
            }
        )
        engine = FilterEngine(config)
        
        # Perfect match
        payload = {
            "data": {
                "string_field": "test",
                "number_field": 15,
                "boolean_field": True,
                "array_field": ["item1", "item3"],
                "null_field": None
            }
        }
        result = engine.evaluate_payload(payload)
        assert result.passed
        assert all(r["error"] is None for r in result.rule_results)

    def test_error_handling_in_complex_rules(self):
        """Test error handling when rules reference missing or invalid fields."""
        config = FilterConfig(
            default_action="pass",
            conditions={
                "logic": "AND",
                "rules": [
                    {"field": "existing.field", "operator": "equals", "value": "test"},
                    {"field": "missing.field", "operator": "equals", "value": "test"},
                    {"field": "invalid..path", "operator": "equals", "value": "test"}
                ]
            }
        )
        engine = FilterEngine(config)
        
        payload = {"existing": {"field": "test"}}
        result = engine.evaluate_payload(payload)
        
        # Should fail because of missing/invalid fields
        assert not result.passed
        assert result.rules_evaluated == 3
        
        # Check individual rule results
        rule_results = result.rule_results
        assert rule_results[0]["error"] is None  # existing.field should work
        assert rule_results[1]["error"] is not None  # missing.field should error
        assert rule_results[2]["error"] is not None  # invalid..path should error

    def test_filter_result_audit_trail(self):
        """Test that FilterResult contains comprehensive audit information."""
        config = FilterConfig(
            default_action="drop",
            conditions={
                "logic": "OR",
                "rules": [
                    {"field": "status", "operator": "equals", "value": "active"},
                    {"field": "priority", "operator": "greater_than", "value": 5}
                ]
            }
        )
        engine = FilterEngine(config)
        
        payload = {"status": "active", "priority": 3}
        result = engine.evaluate_payload(payload)
        
        # Check result properties
        assert isinstance(result.passed, bool)
        assert isinstance(result.rules_evaluated, int)
        assert isinstance(result.rule_results, list)
        assert isinstance(result.default_action_applied, bool)
        
        # Check rule results structure
        assert len(result.rule_results) == 2
        for rule_result in result.rule_results:
            assert "field" in rule_result
            assert "operator" in rule_result
            assert "rule_value" in rule_result
            assert "extracted_value" in rule_result
            assert "passed" in rule_result
            assert "error" in rule_result