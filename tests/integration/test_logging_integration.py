import json
from pathlib import Path
import pytest
from loguru import logger

from flowbridge.utils.logging_utils import setup_logging, log_config_loaded, log_config_error

class TestLoggingIntegration:
    def test_file_logging_setup(self, tmp_path: Path):
        """Test logging setup with file output."""
        log_file = tmp_path / "test.log"
        setup_logging(
            log_level="DEBUG",
            log_file=log_file,
            rotation="1 MB"
        )
        
        test_message = "Test log message"
        logger.debug(test_message)
        
        # Verify log file exists and contains the message
        assert log_file.exists()
        log_content = log_file.read_text()
        assert test_message in log_content
        
        # Verify JSON structure - parse each line separately
        log_lines = log_content.strip().split('\n')
        test_log_entry = None
        
        # Find the log entry with our test message
        for line in log_lines:
            if line.strip():  # Skip empty lines
                entry = json.loads(line)
                if test_message in entry.get("text", ""):
                    test_log_entry = entry
                    break
        
        assert test_log_entry is not None, "Test message not found in log entries"
        
        # Verify the JSON structure contains required fields
        assert "text" in test_log_entry
        assert "record" in test_log_entry
        assert "time" in test_log_entry["record"]
        assert "level" in test_log_entry["record"]
        assert "message" in test_log_entry["record"]
        assert test_log_entry["record"]["message"] == test_message

    def test_config_loaded_logging(self, tmp_path: Path, capsys):
        """Test configuration loaded logging with sections."""
        setup_logging()
        test_path = tmp_path / "config.yaml"
        test_sections = ["general", "server", "filtering"]
        
        log_config_loaded(test_path, test_sections)
        
        captured = capsys.readouterr()
        assert str(test_path) in captured.err
        for section in test_sections:
            assert section in captured.err

    def test_config_error_logging(self, capsys):
        """Test configuration error logging with context."""
        setup_logging()
        error_type = "ValidationError"
        error_message = "Invalid configuration value"
        context = {"field": "server.port", "value": "invalid"}
        
        log_config_error(error_type, error_message, context)
        
        captured = capsys.readouterr()
        assert error_type in captured.err
        assert error_message in captured.err
        assert "server.port" in captured.err

    def test_log_level_propagation(self, capsys):
        """Test log level propagation across handlers."""
        setup_logging(log_level="WARNING")
        
        # This should not appear in output
        logger.debug("Debug message")
        logger.info("Info message")
        
        # This should appear
        logger.warning("Warning message")
        logger.error("Error message")
        
        captured = capsys.readouterr()
        assert "Debug message" not in captured.err
        assert "Info message" not in captured.err
        assert "Warning message" in captured.err
        assert "Error message" in captured.err
