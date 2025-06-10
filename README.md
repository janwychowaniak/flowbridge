# FlowBridge

A content-aware HTTP JSON traffic router with advanced filtering and routing capabilities.

## Features

- YAML-based configuration
- Content-aware JSON payload filtering
- Dynamic routing based on payload content
- Comprehensive logging and monitoring
- High performance and reliability
- Fail-fast behavior with clear error messages

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. Create a configuration file (e.g., `config.yaml`):

```yaml
general:
  route_timeout: 2
  log_rotation: 200mb

server:
  host: 0.0.0.0
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
      alert-type-1: http://destination1/ep/
      alert-type-2: http://destination2/ep/
```

2. Run FlowBridge:

```bash
python -m flowbridge --config config.yaml
```

## Configuration Reference

### General Settings

- `route_timeout`: Request timeout in seconds
- `log_rotation`: Log file rotation size (e.g., "200mb")

### Server Settings

- `host`: Server host address
- `port`: Server port number
- `workers`: Number of worker processes
- `log_level`: Logging level (debug, info, warning, error)

### Filtering Configuration

- `default_action`: Default action when no rules match (drop/pass)
- `conditions`: Filter conditions structure
  - `logic`: Top-level logic operator (AND/OR)
  - `rules`: List of filtering rules
    - `field`: JSON field path
    - `operator`: Comparison operator
    - `value`: Expected value

### Routes Configuration

- `field`: JSON field path for routing decisions
- `mappings`: Key-value pairs of field values to destination URLs

## Operators

Available filtering operators:
- `equals`: Exact value match
- `not_equals`: Value does not match
- `in`: Value is in list
- `contains_any`: List contains any specified values
- `less_than`: Numeric comparison (<)
- `greater_than`: Numeric comparison (>)

## Field Path Syntax

Use dot notation to access nested JSON fields:
- `field.subfield`
- `array.0.field`
- `deeply.nested.field`

## Error Handling

FlowBridge provides clear error messages for:
- Configuration syntax errors
- Invalid field paths
- Unsupported operators
- Validation failures
- Runtime errors

## Logging

Logs are written in JSON format with the following structure:
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "ERROR",
  "category": "CONFIG_ERROR",
  "message": "Invalid configuration structure",
  "context": {
    "config_path": "/path/to/config.yaml",
    "error_details": "Field 'operator' has invalid value"
  }
}
```

## Troubleshooting

### Common Issues

1. Configuration Validation Errors
   - Check YAML syntax
   - Verify field paths exist in your JSON
   - Ensure operators are supported
   - Validate URL formats in routes

2. Runtime Issues
   - Check log files for detailed error messages
   - Verify network connectivity to destinations
   - Monitor system resources

3. Performance Issues
   - Optimize filtering rules
   - Adjust worker count
   - Monitor memory usage

## Development

### Running Tests

```bash
pytest tests/
pytest --cov=flowbridge tests/
```

### Code Style

```bash
black .
isort .
pylint flowbridge tests
mypy flowbridge
```

## License

MIT License - See LICENSE file for details
