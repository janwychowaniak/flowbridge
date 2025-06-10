from pathlib import Path
import pytest
import yaml

@pytest.fixture
def valid_config_dict():
    """Return a valid configuration dictionary."""
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
                    },
                    {
                        "field": "operation",
                        "operator": "equals",
                        "value": "Creation"
                    }
                ]
            }
        },
        "routes": [
            {
                "field": "object.title",
                "mappings": {
                    "test-alert1": "http://localhost:5001/endpoint",
                    "test-alert2": "http://localhost:5002/endpoint"
                }
            }
        ]
    }

@pytest.fixture
def valid_config_file(tmp_path: Path, valid_config_dict):
    """Create a temporary valid configuration file."""
    config_file = tmp_path / "config.yaml"
    with config_file.open('w') as f:
        yaml.safe_dump(valid_config_dict, f)
    return config_file

@pytest.fixture
def invalid_yaml_file(tmp_path: Path):
    """Create a temporary file with invalid YAML syntax."""
    config_file = tmp_path / "invalid.yaml"
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
                  operator: equals
                  value: alert
    routes:
        - field: object.title
          mappings:
            test-alert: http://localhost:5000/endpoint
    # Invalid YAML - incorrect indentation and missing quotes
    invalid:
        - test: [1, 2,
    """)
    return config_file
