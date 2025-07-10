import json
import os
from pathlib import Path
import pytest
from typing import Dict, Any

import yaml
from flask import Flask

from flowbridge.app import create_app
from flowbridge.config.loader import load_config
from flowbridge.config.models import FilterCondition
from flowbridge.core.processor import ProcessingPipeline


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

@pytest.fixture
def test_config():
    """Load test configuration for filtering implementation using the config loader."""
    config_path = Path(__file__).parent / "fixtures" / "filtering_impl_config.yaml"
    return load_config(str(config_path))

@pytest.fixture
def webhook_payloads() -> Dict[str, Any]:
    """Load test webhook payloads."""
    payload_path = Path(__file__).parent / "fixtures" / "webhook_payloads.json"
    with open(payload_path) as f:
        return json.load(f)

@pytest.fixture
def error_payloads() -> Dict[str, Any]:
    """Load error test payloads."""
    error_path = Path(__file__).parent / "fixtures" / "error_payloads.json"
    with open(error_path) as f:
        return json.load(f)

@pytest.fixture
def app(test_config) -> Flask:
    """Create Flask test application with test configuration."""
    return create_app(test_config)

@pytest.fixture
def processing_pipeline(test_config) -> ProcessingPipeline:
    """Create ProcessingPipeline instance with test configuration."""
    return ProcessingPipeline(config=test_config)

@pytest.fixture
def test_filtering_config(test_config):
    """Get the filtering configuration for testing."""
    return test_config.filtering

@pytest.fixture
def empty_rules_config(test_config):
    """Create a test configuration with empty rules."""
    config = test_config.model_copy(deep=True)
    config.filtering.conditions.rules = []
    config.filtering.default_action = "pass"
    return config

@pytest.fixture
def complex_rules_config(test_config):
    """Create a test configuration with complex rules."""
    config = test_config.model_copy(deep=True)
    config.filtering.conditions.logic = "OR"
    config.filtering.conditions.rules = [
        FilterCondition(
            field="object.severity",
            operator="greater_than",
            value=7
        ),
        FilterCondition(
            field="object.title",
            operator="contains_any",
            value=["virus", "malware", "trojan"]
        )
    ]
    return config

@pytest.fixture
def processing_pipeline_empty_rules(empty_rules_config) -> ProcessingPipeline:
    """Create ProcessingPipeline instance with empty rules configuration."""
    return ProcessingPipeline(config=empty_rules_config)

@pytest.fixture
def processing_pipeline_complex_rules(complex_rules_config) -> ProcessingPipeline:
    """Create ProcessingPipeline instance with complex rules configuration."""
    return ProcessingPipeline(config=complex_rules_config)

@pytest.fixture
def app_with_empty_rules(empty_rules_config):
    """Create Flask app with empty filtering rules configuration."""
    app = create_app(empty_rules_config)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def app_with_filtering_config(test_config) -> Flask:
    """Create Flask app with filtering configuration for integration tests."""
    app = create_app(test_config)
    app.config['TESTING'] = True
    return app
