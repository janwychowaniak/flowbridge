# flowbridge/core/router.py

"""
Routing engine for FlowBridge - extracts field values from JSON payloads,
matches them against configured mappings, and determines destination URLs.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from loguru import logger

from flowbridge.core.field_extractor import FieldExtractor, FieldExtractionResult
from flowbridge.config.models import RouteMapping
from flowbridge.utils.errors import RoutingError


@dataclass
class RoutingResult:
    """Result of routing decision process."""
    success: bool
    destination_url: Optional[str]
    matched_value: Optional[str]
    field_path: str
    rule_index: Optional[int]
    error_message: Optional[str]
    extraction_result: Optional[FieldExtractionResult]


class RoutingEngine:
    """
    Main routing engine that processes JSON payloads and determines destinations.
    
    Uses existing FieldExtractor to extract field values and matches them against
    configured routing mappings with first-match-wins logic.
    """
    
    def __init__(self, routing_rules: List[RouteMapping]):
        """Initialize routing engine with routing configuration.
        
        Args:
            routing_rules: List of RouteMapping instances from configuration
        """
        self.routing_rules = routing_rules
        self.field_extractor = FieldExtractor()
        
    def find_destination(self, payload: Dict[str, Any]) -> RoutingResult:
        """
        Find destination URL for payload based on configured routing rules.
        
        Args:
            payload: JSON payload to route
            
        Returns:
            RoutingResult with destination URL or error information
        """
        if not self.routing_rules:
            logger.info("No routing rules configured, dropping request")
            return RoutingResult(
                success=False,
                destination_url=None,
                matched_value=None,
                field_path="",
                rule_index=None,
                error_message="No routing rules configured",
                extraction_result=None
            )
        
        # Process routing rules in order (first-match-wins)
        for rule_index, rule in enumerate(self.routing_rules):
            try:
                result = self.evaluate_routing_rule(payload, rule, rule_index)
                if result.success:
                    logger.info(
                        "Routing decision made",
                        field_path=result.field_path,
                        matched_value=result.matched_value,
                        destination_url=result.destination_url,
                        rule_index=result.rule_index
                    )
                    return result
                    
            except Exception as e:
                logger.warning(
                    "Error evaluating routing rule",
                    rule_index=rule_index,
                    field_path=rule.field,
                    error=str(e)
                )
                continue
        
        # No rules matched
        logger.info("No routing rules matched, dropping request")
        return RoutingResult(
            success=False,
            destination_url=None,
            matched_value=None,
            field_path=self.routing_rules[0].field if self.routing_rules else "",
            rule_index=None,
            error_message="No matching routing rule found",
            extraction_result=None
        )
    
    def evaluate_routing_rule(self, payload: Dict[str, Any], rule: RouteMapping, rule_index: int) -> RoutingResult:
        """
        Evaluate a single routing rule against payload.
        
        Args:
            payload: JSON payload to evaluate
            rule: Routing rule to evaluate
            rule_index: Index of rule in configuration
            
        Returns:
            RoutingResult with evaluation outcome
        """
        # Extract field value using existing field extractor
        extraction_result = self.field_extractor.extract_field(payload, rule.field)
        
        if not extraction_result.success:
            logger.debug(
                "Field extraction failed for routing",
                field_path=rule.field,
                error=extraction_result.error_message
            )
            return RoutingResult(
                success=False,
                destination_url=None,
                matched_value=None,
                field_path=rule.field,
                rule_index=rule_index,
                error_message=f"Field extraction failed: {extraction_result.error_message}",
                extraction_result=extraction_result
            )
        
        # Convert field value to string for matching
        field_value = str(extraction_result.value) if extraction_result.value is not None else None
        
        if field_value is None:
            logger.debug(
                "Extracted field value is None",
                field_path=rule.field,
                rule_index=rule_index
            )
            return RoutingResult(
                success=False,
                destination_url=None,
                matched_value=None,
                field_path=rule.field,
                rule_index=rule_index,
                error_message="Extracted field value is None",
                extraction_result=extraction_result
            )
        
        # Check if field value matches any mapping key (exact match)
        destination_url_obj = rule.mappings.get(field_value)
        
        if destination_url_obj:
            # Convert HttpUrl to string for consistent handling throughout the system
            destination_url = str(destination_url_obj)
            logger.debug(
                "Routing rule matched",
                field_path=rule.field,
                field_value=field_value,
                destination_url=destination_url,
                rule_index=rule_index
            )
            return RoutingResult(
                success=True,
                destination_url=destination_url,
                matched_value=field_value,
                field_path=rule.field,
                rule_index=rule_index,
                error_message=None,
                extraction_result=extraction_result
            )
        else:
            logger.debug(
                "Routing rule did not match",
                field_path=rule.field,
                field_value=field_value,
                available_mappings=list(rule.mappings.keys()),
                rule_index=rule_index
            )
            return RoutingResult(
                success=False,
                destination_url=None,
                matched_value=field_value,
                field_path=rule.field,
                rule_index=rule_index,
                error_message=f"No mapping found for value: {field_value}",
                extraction_result=extraction_result
            )
