from pathlib import Path
import pytest
from pydantic import HttpUrl

from flowbridge.config.loader import load_config, validate_config_path, load_yaml_safely
from flowbridge.utils.errors import ConfigurationError, ValidationError
from flowbridge.config.models import ConfigModel

def test_validate_config_path_valid(valid_config_file):
    """Test validation of a valid configuration file path."""
    path = validate_config_path(valid_config_file)
    assert isinstance(path, Path)
    assert path.exists()
    assert path.is_file()

def test_validate_config_path_invalid():
    """Test validation of an invalid configuration file path."""
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config_path("/nonexistent/path/config.yaml")
    assert "Invalid configuration path" in str(exc_info.value)
    assert "path" in exc_info.value.context

def test_load_yaml_safely_valid(valid_config_file):
    """Test loading a valid YAML configuration file."""
    config_dict = load_yaml_safely(valid_config_file)
    assert isinstance(config_dict, dict)
    assert "general" in config_dict
    assert "server" in config_dict
    assert "filtering" in config_dict
    assert "routes" in config_dict

def test_load_yaml_safely_invalid(invalid_yaml_file):
    """Test loading an invalid YAML configuration file."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_yaml_safely(invalid_yaml_file)
    assert "Failed to parse YAML configuration" in str(exc_info.value)
    assert "path" in exc_info.value.context

def test_load_config_valid(valid_config_file):
    """Test loading a valid configuration file."""
    config = load_config(valid_config_file)
    assert isinstance(config, ConfigModel)
    assert config.general.route_timeout == 2
    assert config.general.log_rotation == "200mb"
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8000
    assert isinstance(config.routes[0].mappings["test-alert1"], HttpUrl)
    assert isinstance(config.routes[0].mappings["test-alert2"], HttpUrl)

def test_load_config_missing_required_field(tmp_path):
    """Test loading a configuration with missing required fields."""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text("""
    general:
        route_timeout: 2
    server:
        host: "0.0.0.0"
        port: 8000
    """)
    
    with pytest.raises(ValidationError) as exc_info:
        load_config(config_file)
    assert "Configuration validation failed" in str(exc_info.value)
    assert "errors" in exc_info.value.context

def test_load_config_invalid_field_value(tmp_path):
    """Test loading a configuration with invalid field values."""
    config_file = tmp_path / "invalid_values.yaml"
    config_file.write_text("""
    general:
        route_timeout: -1  # Invalid: must be positive
        log_rotation: "200mb"
    server:
        host: "0.0.0.0"
        port: 8000
        workers: 1
        log_level: info
    filtering:
        default_action: drop
        conditions:
            logic: AND
            rules: []  # Invalid: empty rules list
    routes:
        - field: "object.title"
          mappings:
            test-alert: "not_a_valid_url"  # Invalid URL format
    """)
    
    with pytest.raises(ValidationError) as exc_info:
        load_config(config_file)
    assert "Configuration validation failed" in str(exc_info.value)
    errors = exc_info.value.context["errors"]
    assert any("route_timeout" in str(e) for e in errors)

def test_load_config_invalid_filter_operator(tmp_path):
    """Test loading a configuration with invalid filter operator."""
    config_file = tmp_path / "invalid_operator.yaml"
    config_file.write_text("""
    general:
        route_timeout: 2
        log_rotation: "200mb"
    server:
        host: "0.0.0.0"
        port: 8000
        workers: 1
        log_level: info
    filtering:
        default_action: drop
        conditions:
            logic: AND
            rules:
                - field: objectType
                  operator: invalid_operator  # Invalid operator
                  value: alert
    routes:
        - field: "object.title"
          mappings:
            test-alert: "http://localhost:5000/endpoint"
    """)
    
    with pytest.raises(ValidationError) as exc_info:
        load_config(config_file)
    assert "Configuration validation failed" in str(exc_info.value)
    errors = exc_info.value.context["errors"]
    assert any("operator" in str(e) for e in errors)
