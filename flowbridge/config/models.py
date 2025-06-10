from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, model_validator, field_validator, ValidationError
from pydantic.fields import Field
import re
from enum import Enum

class GeneralConfig(BaseModel):
    """General application configuration settings."""
    route_timeout: int = Field(gt=0, description="Route timeout in seconds")
    log_rotation: str = Field(pattern=r"^\d+[kmg]?b$", description="Log rotation size")
    
    @model_validator(mode='after')
    def validate_log_rotation(self) -> 'GeneralConfig':
        """Validate log rotation format (e.g., '200mb', '1gb')."""
        if not re.match(r'^\d+[kmg]?b$', self.log_rotation.lower()):
            raise ValueError("Log rotation must be specified in bytes (e.g., '200mb', '1gb')")
        self.log_rotation = self.log_rotation.lower()
        return self

class ServerConfig(BaseModel):
    """Server-specific configuration settings."""
    host: str = Field(description="Server host address")
    port: int = Field(gt=0, lt=65536, description="Server port")
    workers: int = Field(default=1, gt=0, description="Number of worker processes")
    log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info",
        description="Logging level"
    )
    
    @model_validator(mode='after')
    def validate_host(self) -> 'ServerConfig':
        """Validate server host address."""
        if not re.match(r'^[a-zA-Z0-9\.\-]+$', self.host):
            raise ValueError("Invalid host address format")
        return self

class FilterOperator(str, Enum):
    """Supported filter operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    CONTAINS_ANY = "contains_any"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"

class LogicOperator(str, Enum):
    """Supported logic operators for combining filter conditions."""
    AND = "AND"
    OR = "OR"

class FilterCondition(BaseModel):
    """Individual filtering rule with field, operator, and value."""
    field: str = Field(description="Field path in dot notation (e.g., 'object.type')")
    operator: FilterOperator = Field(description="Comparison operator")
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(
        description="Value to compare against"
    )

    @field_validator('field')
    @classmethod
    def validate_field_path(cls, v: str) -> str:
        """Validate field path format."""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*)*$', v):
            raise ValueError(
                'Field path must be in dot notation and start with a letter (e.g., "object.type", "alert.severity")'
            )
        return v

    @model_validator(mode='after')
    def validate_value_type(self) -> 'FilterCondition':
        """Validate value type matches operator requirements."""
        if self.operator in {FilterOperator.IN, FilterOperator.CONTAINS_ANY}:
            if not isinstance(self.value, list):
                raise ValueError(f"Operator {self.operator} requires a list value")
        elif self.operator in {FilterOperator.LESS_THAN, FilterOperator.GREATER_THAN}:
            if not isinstance(self.value, (int, float)):
                raise ValueError(f"Operator {self.operator} requires a numeric value")
        return self

class FilterConditions(BaseModel):
    """Filtering conditions with logic operator and rules."""
    logic: LogicOperator = Field(description="Logic operator for combining rules")
    rules: List[FilterCondition] = Field(description="List of filter conditions", min_length=1)

class FilteringConfig(BaseModel):
    """Complete filtering configuration with logic and conditions."""
    default_action: Literal["drop", "pass"] = Field(
        default="drop",
        description="Default action when no rules match"
    )
    conditions: FilterConditions = Field(description="Filtering conditions with logic operator")

class RouteMapping(BaseModel):
    """Route mapping configuration for field values to destination URLs."""
    field: str = Field(description="Field path to extract routing value")
    mappings: Dict[str, HttpUrl] = Field(description="Mapping of field values to destination URLs")

    @field_validator('field')
    @classmethod
    def validate_field_path(cls, v: str) -> str:
        """Validate field path format."""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*)*$', v):
            raise ValueError(
                'Field path must be in dot notation and start with a letter (e.g., "object.title", "alert.type")'
            )
        return v

    @field_validator('mappings')
    @classmethod
    def validate_mappings(cls, v: Dict[str, HttpUrl]) -> Dict[str, HttpUrl]:
        """Validate that mappings are not empty."""
        if not v:
            raise ValueError('Mappings dictionary cannot be empty')
        return v

class ConfigModel(BaseModel):
    """Root configuration model combining all sections."""
    general: GeneralConfig = Field(description="General application settings")
    server: ServerConfig = Field(description="Server configuration")
    filtering: FilteringConfig = Field(description="Filtering rules and logic")
    routes: List[RouteMapping] = Field(description="Route mapping configurations")

    @model_validator(mode='after')
    def validate_routes(self) -> 'ConfigModel':
        """Validate that routes list is not empty."""
        if not self.routes:
            raise ValueError("At least one route mapping must be specified")
        return self
