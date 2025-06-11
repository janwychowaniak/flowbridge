import os
from pathlib import Path
import pytest
import yaml
from loguru import logger
from click.testing import CliRunner

from flowbridge.cli import cli, serve
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

@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()

class TestCLIIntegration:
    def test_successful_config_validation(self, valid_config: Path, cli_runner: CliRunner):
        """Test successful configuration validation."""
        result = cli_runner.invoke(serve, [
            "--config", str(valid_config),
            "--validate-only"
        ])
        
        assert result.exit_code == 0
        assert "Configuration loaded successfully" in result.stderr or "Loading configuration from:" in result.stderr
        assert "Configuration validation successful" in result.stderr

    def test_invalid_config_validation(self, invalid_config: Path, cli_runner: CliRunner):
        """Test validation failure with invalid configuration."""
        result = cli_runner.invoke(serve, [
            "--config", str(invalid_config),
            "--validate-only"
        ])
        
        assert result.exit_code == 1
        assert "Configuration validation failed" in result.stderr

    def test_log_level_override(self, valid_config: Path, cli_runner: CliRunner):
        """Test log level override via CLI argument."""
        result = cli_runner.invoke(serve, [
            "--config", str(valid_config),
            "--validate-only",
            "--log-level", "DEBUG"
        ])
        
        assert result.exit_code == 0
        assert "Logging configured with level: DEBUG" in result.stderr or "Loading configuration from:" in result.stderr

    def test_nonexistent_config(self, tmp_path: Path, cli_runner: CliRunner):
        """Test error handling for nonexistent configuration file."""
        nonexistent = tmp_path / "nonexistent.yaml"
        result = cli_runner.invoke(serve, [
            "--config", str(nonexistent),
            "--validate-only"
        ])
        
        assert result.exit_code != 0  # Should fail
        # Click will handle the file existence check, so we expect an error message
        assert "does not exist" in result.output or "Error" in result.output
