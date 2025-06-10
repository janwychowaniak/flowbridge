import os
from pathlib import Path
import pytest
import yaml
from loguru import logger

from flowbridge.cli import main
from flowbridge.utils.errors import FlowBridgeError

@pytest.fixture
def valid_config(tmp_path: Path) -> Path:
    """Create a valid configuration file for testing."""
    config = {
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
    
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    return config_path

@pytest.fixture
def invalid_config(tmp_path: Path) -> Path:
    """Create an invalid configuration file for testing."""
    config = {
        "general": {
            "route_timeout": "invalid"
        }
    }
    
    config_path = tmp_path / "invalid_config.yaml"
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    return config_path

class TestCLIIntegration:
    def test_successful_config_validation(self, valid_config: Path, capsys):
        """Test successful configuration validation."""
        args = ["--config", str(valid_config), "--validate-only"]
        result = main(args)
        
        captured = capsys.readouterr()
        assert result == 0
        assert "Configuration loaded successfully" in captured.err
        assert "Configuration validation successful" in captured.err

    def test_invalid_config_validation(self, invalid_config: Path, capsys):
        """Test validation failure with invalid configuration."""
        args = ["--config", str(invalid_config), "--validate-only"]
        result = main(args)
        
        captured = capsys.readouterr()
        assert result == 1
        assert "Configuration error" in captured.err

    def test_log_level_override(self, valid_config: Path, capsys):
        """Test log level override via CLI argument."""
        args = [
            "--config", str(valid_config),
            "--validate-only",
            "--log-level", "DEBUG"
        ]
        result = main(args)
        
        captured = capsys.readouterr()
        assert result == 0
        assert "Logging configured with level: DEBUG" in captured.err

    def test_nonexistent_config(self, tmp_path: Path, capsys):
        """Test error handling for nonexistent configuration file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        args = ["--config", str(nonexistent), "--validate-only"]
        result = main(args)
        
        captured = capsys.readouterr()
        assert result == 1
        assert "Configuration file not found" in captured.err
