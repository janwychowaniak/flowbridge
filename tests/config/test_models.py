from typing import Any, Dict
import pytest
from pydantic import ValidationError

from flowbridge.config.models import (
    GeneralConfig,
    ServerConfig,
    FilterCondition,
    FilteringConfig,
    RouteMapping,
    ConfigModel
)

class TestGeneralConfig:
    def test_valid_general_config(self):
        """Test valid general configuration."""
        config = GeneralConfig(
            route_timeout=2,
            log_rotation="200mb"
        )
        assert config.route_timeout == 2
        assert config.log_rotation == "200mb"

    def test_invalid_timeout(self):
        """Test invalid route timeout validation."""
        with pytest.raises(ValidationError) as exc_info:
            GeneralConfig(route_timeout=-1, log_rotation="200mb")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "route_timeout" in errors[0]["loc"]
        assert "greater than 0" in errors[0]["msg"]

    def test_invalid_log_rotation(self):
        """Test invalid log rotation format."""
        with pytest.raises(ValidationError) as exc_info:
            GeneralConfig(route_timeout=2, log_rotation="invalid")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "log_rotation" in errors[0]["loc"]
        assert "string should match pattern" in errors[0]["msg"].lower()

class TestServerConfig:
    def test_valid_server_config(self):
        """Test valid server configuration."""
        config = ServerConfig(
            host="0.0.0.0",
            port=8000,
            workers=1,
            log_level="info"
        )
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.workers == 1
        assert config.log_level == "info"

    def test_invalid_port(self):
        """Test invalid port number validation."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(
                host="0.0.0.0",
                port=65536,  # Invalid port
                workers=1,
                log_level="info"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "port" in errors[0]["loc"]

    def test_invalid_workers(self):
        """Test invalid workers count validation."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(
                host="0.0.0.0",
                port=8000,
                workers=0,  # Invalid workers count
                log_level="info"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "workers" in errors[0]["loc"]

    def test_invalid_log_level(self):
        """Test invalid log level validation."""
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(
                host="0.0.0.0",
                port=8000,
                workers=1,
                log_level="invalid"  # Invalid log level
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "log_level" in errors[0]["loc"]

class TestFilterCondition:
    def test_valid_filter_condition(self):
        """Test valid filter condition."""
        condition = FilterCondition(
            field="objectType",
            operator="equals",
            value="alert"
        )
        assert condition.field == "objectType"
        assert condition.operator == "equals"
        assert condition.value == "alert"

    def test_invalid_operator(self):
        """Test invalid operator validation."""
        with pytest.raises(ValidationError) as exc_info:
            FilterCondition(
                field="objectType",
                operator="invalid",  # Invalid operator
                value="alert"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "operator" in errors[0]["loc"]

    def test_nested_field_path(self):
        """Test nested field path validation."""
        condition = FilterCondition(
            field="object.type.name",
            operator="equals",
            value="alert"
        )
        assert condition.field == "object.type.name"

    def test_invalid_field_path(self):
        """Test invalid field path validation."""
        with pytest.raises(ValidationError) as exc_info:
            FilterCondition(
                field="object..type",  # Invalid path
                operator="equals",
                value="alert"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "field" in errors[0]["loc"]

class TestFilteringConfig:
    def test_valid_filtering_config(self):
        """Test valid filtering configuration."""
        config = FilteringConfig(
            default_action="drop",
            conditions={
                "logic": "AND",
                "rules": [
                    {
                        "field": "objectType",
                        "operator": "equals",
                        "value": "alert"
                    }
                ]
            }
        )
        assert config.default_action == "drop"
        assert config.conditions.logic == "AND"
        assert len(config.conditions.rules) == 1

    def test_invalid_logic(self):
        """Test invalid logic operator validation."""
        with pytest.raises(ValidationError) as exc_info:
            FilteringConfig(
                default_action="drop",
                conditions={
                    "logic": "INVALID",  # Invalid logic
                    "rules": []
                }
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 2  # Both logic and rules are invalid
        # Check that one error is for logic operator
        logic_errors = [e for e in errors if 'logic' in e['loc']]
        assert len(logic_errors) == 1
        assert 'logic' in logic_errors[0]['loc']

    def test_empty_rules(self):
        """Test empty rules validation."""
        with pytest.raises(ValidationError) as exc_info:
            FilteringConfig(
                default_action="drop",
                conditions={
                    "logic": "AND",
                    "rules": []  # Empty rules
                }
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "rules" in errors[0]["loc"]

class TestRouteMapping:
    def test_valid_route_mapping(self):
        """Test valid route mapping."""
        mapping = RouteMapping(
            field="object.title",
            mappings={
                "test-case": "http://localhost:8000/test"
            }
        )
        assert mapping.field == "object.title"
        assert "test-case" in mapping.mappings

    def test_invalid_url(self):
        """Test invalid URL validation."""
        with pytest.raises(ValidationError) as exc_info:
            RouteMapping(
                field="object.title",
                mappings={
                    "test-case": "invalid-url"  # Invalid URL
                }
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "mappings" in errors[0]["loc"]

    def test_empty_mappings(self):
        """Test empty mappings validation."""
        with pytest.raises(ValidationError) as exc_info:
            RouteMapping(
                field="object.title",
                mappings={}  # Empty mappings
            )
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "mappings" in errors[0]["loc"]

class TestConfigModel:
    @pytest.fixture
    def valid_config_dict(self) -> Dict[str, Any]:
        """Create a valid configuration dictionary."""
        return {
            "general": {
                "route_timeout": 2,
                "log_rotation": "200mb"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 1,
                "log_level": "info"
            },
            "filtering": {
                "default_action": "drop",
                "conditions": {
                    "logic": "AND",
                    "rules": [
                        {
                            "field": "objectType",
                            "operator": "equals",
                            "value": "alert"
                        }
                    ]
                }
            },
            "routes": [
                {
                    "field": "object.title",
                    "mappings": {
                        "test-case": "http://localhost:8000/test"
                    }
                }
            ]
        }

    def test_valid_complete_config(self, valid_config_dict):
        """Test valid complete configuration."""
        config = ConfigModel(**valid_config_dict)
        assert config.general.route_timeout == 2
        assert config.server.port == 8000
        assert len(config.filtering.conditions.rules) == 1
        assert len(config.routes) == 1

    def test_missing_required_section(self, valid_config_dict):
        """Test missing required section validation."""
        del valid_config_dict["server"]
        
        with pytest.raises(ValidationError) as exc_info:
            ConfigModel(**valid_config_dict)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "server" in errors[0]["loc"]

    def test_invalid_nested_config(self, valid_config_dict):
        """Test invalid nested configuration validation."""
        valid_config_dict["server"]["port"] = 999999  # Invalid port
        
        with pytest.raises(ValidationError) as exc_info:
            ConfigModel(**valid_config_dict)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "server" in errors[0]["loc"]
        assert "port" in errors[0]["loc"]
