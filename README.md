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

## API Endpoints

### Webhook Endpoint

**POST /webhook**

The primary business endpoint for JSON payload processing. Accepts JSON payloads, applies configured filtering rules, and either returns an immediate response (for dropped requests) or prepares the request for routing.

#### Request Format

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "objectType": "alert",
    "operation": "Creation",
    "object": {
      "title": "AP_McAfeeMsme-virusDetected",
      "severity": 5
    }
  }'
```

#### Response Formats

**Dropped Request (200 OK):**
```json
{
  "status": "processed",
  "result": "dropped",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "filtering_summary": {
    "rules_evaluated": 2,
    "default_action_applied": true,
    "matched_rules": null
  }
}
```

**Passed Request (200 OK):**
```json
{
  "status": "processing",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request passed filtering, proceeding to routing"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "InvalidRequestError",
  "message": "Invalid JSON format",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Operational Endpoints

**GET /health**

Health check endpoint for monitoring system status.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**GET /config**

Returns the current application configuration.

```bash
curl http://localhost:8000/config
```

## Usage Examples

### Example 1: Basic Alert Processing

```bash
# Send an alert that matches filtering rules
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "objectType": "alert",
    "operation": "Creation",
    "object": {
      "title": "Critical security alert",
      "severity": 8
    }
  }'
```

### Example 2: Request That Gets Dropped

```bash
# Send a request that will be dropped by filtering
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "objectType": "incident",
    "operation": "Update",
    "object": {
      "title": "Maintenance notification",
      "severity": 2
    }
  }'
```

### Example 3: Complex Nested Payload

```bash
# Send a complex nested payload
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "objectType": "alert",
    "operation": "Creation",
    "metadata": {
      "source": "security_system",
      "priority": "high"
    },
    "object": {
      "title": "AP_McAfeeMsme-virusDetected",
      "details": {
        "host": "server01",
        "user": "admin",
        "threat": {
          "type": "malware",
          "severity": 9
        }
      }
    }
  }'
```

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
