from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from loguru import logger
from pydantic import BaseModel

from .field_extractor import FieldExtractor, FieldExtractionResult


class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    CONTAINS_ANY = "contains_any"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"


class LogicOperator(str, Enum):
    """Logic operators for combining multiple rules."""
    AND = "AND"
    OR = "OR"


@dataclass
class FilterResult:
    """Result of filter evaluation."""
    passed: bool
    rules_evaluated: int
    rule_results: List[Dict[str, Any]]
    default_action_applied: bool
    error_message: Optional[str] = None


class FilterEvaluator:
    """Evaluates individual filter rules."""
    
    @staticmethod
    def coerce_types(value: Any, target: Any) -> tuple[Any, Any]:
        """Coerce values to matching types for comparison.
        
        Args:
            value: The value to compare
            target: The target value to compare against
            
        Returns:
            Tuple of coerced values
        """
        if value is None or target is None:
            return value, target
            
        # Try to coerce numbers
        if isinstance(target, (int, float)) or isinstance(value, (int, float)):
            try:
                value = float(value)
                target = float(target)
            except (ValueError, TypeError):
                pass
                
        return value, target

    def apply_operator(
        self, 
        operator: FilterOperator, 
        field_value: Any, 
        rule_value: Any
    ) -> bool:
        """Apply a filter operator to compare values.
        
        Args:
            operator: The operator to apply
            field_value: The extracted field value
            rule_value: The value to compare against
            
        Returns:
            Boolean indicating if the comparison passed
        """
        # Handle None cases first
        if field_value is None:
            return operator == FilterOperator.EQUALS and rule_value is None
            
        # Coerce types for comparison
        field_value, rule_value = self.coerce_types(field_value, rule_value)
        
        try:
            if operator == FilterOperator.EQUALS:
                return field_value == rule_value
            elif operator == FilterOperator.NOT_EQUALS:
                return field_value != rule_value
            elif operator == FilterOperator.IN:
                return field_value in rule_value
            elif operator == FilterOperator.CONTAINS_ANY:
                return any(v in field_value for v in rule_value)
            elif operator == FilterOperator.LESS_THAN:
                return field_value < rule_value
            elif operator == FilterOperator.GREATER_THAN:
                return field_value > rule_value
            else:
                raise ValueError(f"Unsupported operator: {operator}")
                
        except TypeError as e:
            logger.warning(
                "Type error in filter evaluation",
                operator=operator,
                field_value=field_value,
                rule_value=rule_value,
                error=str(e)
            )
            return False


class FilterRule(BaseModel):
    """Pydantic model for a single filter rule."""
    field: str
    operator: FilterOperator
    value: Any


class FilterConfig(BaseModel):
    """Pydantic model for filter configuration."""
    default_action: str  # "drop" or "pass"
    conditions: Dict[str, Any]  # Contains logic and rules


class FilterEngine:
    """Main orchestrator for evaluating JSON payloads against filtering rules."""
    
    def __init__(self, config: FilterConfig):
        """Initialize the filter engine with configuration.
        
        Args:
            config: FilterConfig instance containing filtering rules
        """
        self.config = config
        self.field_extractor = FieldExtractor()
        self.evaluator = FilterEvaluator()
        
    def evaluate_single_rule(
        self, 
        payload: dict, 
        rule: FilterRule
    ) -> Dict[str, Any]:
        """Evaluate a single filter rule against a payload.
        
        Args:
            payload: The JSON payload to evaluate
            rule: The FilterRule to apply
            
        Returns:
            Dictionary containing rule evaluation results
        """
        extraction_result = self.field_extractor.extract_field(
            payload, 
            rule.field
        )
        
        result = {
            "field": rule.field,
            "operator": rule.operator,
            "rule_value": rule.value,
            "extracted_value": extraction_result.value,
            "passed": False,
            "error": None
        }
        
        if not extraction_result.success:
            result["error"] = extraction_result.error_message
            return result
            
        try:
            result["passed"] = self.evaluator.apply_operator(
                rule.operator,
                extraction_result.value,
                rule.value
            )
        except Exception as e:
            result["error"] = str(e)
            logger.error(
                "Rule evaluation failed",
                rule=rule.dict(),
                error=str(e)
            )
            
        return result

    def combine_results(
        self, 
        results: List[bool], 
        logic: LogicOperator
    ) -> bool:
        """Combine multiple rule results using specified logic.
        
        Args:
            results: List of boolean results from individual rules
            logic: LogicOperator to apply (AND/OR)
            
        Returns:
            Combined boolean result
        """
        if not results:
            return True  # Empty rule set passes by default
            
        if logic == LogicOperator.AND:
            return all(results)
        elif logic == LogicOperator.OR:
            return any(results)
        else:
            raise ValueError(f"Unsupported logic operator: {logic}")

    def evaluate_payload(self, payload: dict) -> FilterResult:
        """Evaluate a payload against all configured filter rules.
        
        Args:
            payload: The JSON payload to evaluate
            
        Returns:
            FilterResult containing evaluation outcome
        """
        if not isinstance(payload, dict):
            return FilterResult(
                passed=False,
                rules_evaluated=0,
                rule_results=[],
                default_action_applied=True,
                error_message="Payload must be a dictionary"
            )
            
        conditions = self.config.conditions
        rules = [FilterRule(**rule) for rule in conditions.get("rules", [])]
        logic = LogicOperator(conditions.get("logic", "AND"))
        
        rule_results = []
        rule_outcomes = []
        
        for rule in rules:
            result = self.evaluate_single_rule(payload, rule)
            rule_results.append(result)
            rule_outcomes.append(result["passed"])
            
        # Handle empty rules case
        if not rules:
            passed = self.config.default_action == "pass"
            default_action_applied = True
        else:
            passed = self.combine_results(rule_outcomes, logic)
            default_action_applied = False
            
        return FilterResult(
            passed=passed,
            rules_evaluated=len(rules),
            rule_results=rule_results,
            default_action_applied=default_action_applied
        )