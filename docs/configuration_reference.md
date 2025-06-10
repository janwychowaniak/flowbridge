# FlowBridge Configuration Reference

This document provides a detailed reference for all configuration options available in FlowBridge.

## Configuration File Structure

The configuration file is in YAML format and consists of four main sections:
- `general`: Global settings
- `server`: Server configuration
- `filtering`: Filtering rules and conditions
- `routes`: Routing rules and destinations

## General Settings

### route_timeout
- **Type**: Integer
- **Default**: 2
- **Units**: Seconds
- **Description**: Maximum time to wait for a response from destination endpoints
- **Validation**:
  - Must be positive integer
  - Maximum value: 30 seconds
  - Minimum value: 1 second

### log_rotation
- **Type**: String
- **Default**: "200mb"
- **Format**: "{size}{unit}" where unit is one of [kb, mb, gb]
- **Description**: Size threshold for log file rotation
- **Validation**:
  - Must match format pattern
  - Minimum size: "100kb"
  - Maximum size: "1gb"

## Server Settings

### host
- **Type**: String
- **Default**: "0.0.0.0"
- **Description**: Network interface to bind to
- **Validation**:
  - Must be valid IPv4 address
  - Special value "0.0.0.0" for all interfaces

### port
- **Type**: Integer
- **Default**: 8000
- **Description**: TCP port to listen on
- **Validation**:
  - Range: 1-65535
  - Common ports (80, 443) require root privileges

### workers
- **Type**: Integer
- **Default**: 1
- **Description**: Number of worker processes
- **Validation**:
  - Minimum: 1
  - Maximum: Number of CPU cores * 2 + 1

### log_level
- **Type**: String
- **Default**: "info"
- **Options**: ["debug", "info", "warning", "error"]
- **Description**: Logging verbosity level

## Filtering Configuration

### default_action
- **Type**: String
- **Default**: "drop"
- **Options**: ["drop", "pass"]
- **Description**: Action to take when no filtering rules match

### conditions
- **Type**: Object
- **Required**: Yes
- **Fields**:
  - `logic`: String, one of ["AND", "OR"]
  - `rules`: List of filter conditions

### Filter Condition
- **Type**: Object
- **Required Fields**:
  - `field`: String (dot notation path)
  - `operator`: String
  - `value`: Any (type depends on operator)

### Available Operators

#### equals
- **Type**: Any
- **Description**: Exact value match
- **Example**:
  ```yaml
  field: status
  operator: equals
  value: active
  ```

#### not_equals
- **Type**: Any
- **Description**: Value inequality
- **Example**:
  ```yaml
  field: status
  operator: not_equals
  value: deleted
  ```

#### in
- **Type**: List
- **Description**: Value must be in list
- **Example**:
  ```yaml
  field: category
  operator: in
  value: ["error", "warning", "critical"]
  ```

#### contains_any
- **Type**: List
- **Description**: Field list contains any of specified values
- **Example**:
  ```yaml
  field: tags
  operator: contains_any
  value: ["security", "network"]
  ```

#### less_than
- **Type**: Number
- **Description**: Numeric less than comparison
- **Example**:
  ```yaml
  field: priority
  operator: less_than
  value: 5
  ```

#### greater_than
- **Type**: Number
- **Description**: Numeric greater than comparison
- **Example**:
  ```yaml
  field: severity
  operator: greater_than
  value: 7
  ```

## Routes Configuration

### Route Definition
- **Type**: Object
- **Required Fields**:
  - `field`: String (dot notation path)
  - `mappings`: Object (key-value pairs)

### Field
- **Type**: String
- **Description**: JSON path to field used for routing
- **Format**: Dot notation (e.g., "object.field.subfield")
- **Validation**:
  - Must be valid field path
  - Cannot be empty
  - Maximum depth: 10 levels

### Mappings
- **Type**: Object
- **Description**: Map of field values to destination URLs
- **Validation**:
  - Keys: String (field values)
  - Values: Valid HTTP(S) URLs
  - URLs must include scheme (http:// or https://)
  - URLs must be absolute
  - Maximum URL length: 2048 characters

## Field Path Syntax

### Dot Notation
- Use dots to separate nested field names
- Array indices are specified as numbers
- Maximum path length: 256 characters

### Examples
```yaml
# Simple field
field: status

# Nested field
field: user.profile.name

# Array element
field: items.0.id

# Deep nesting
field: data.attributes.metadata.type
```

## Validation Rules

1. File Format
   - Must be valid YAML
   - UTF-8 encoding required
   - Maximum file size: 1MB

2. Section Requirements
   - All top-level sections required
   - Sections must not be empty
   - Unknown sections not allowed

3. Value Constraints
   - String fields: Maximum length 1024 characters
   - Lists: Maximum 100 elements
   - Objects: Maximum 100 key-value pairs
   - Numbers: Must be finite, non-NaN

4. URL Validation
   - Must be absolute URLs
   - Must include scheme (http/https)
   - Must be properly encoded
   - No authentication information allowed in URLs

## Error Messages

FlowBridge provides detailed error messages for configuration issues:

```
Configuration Error: Invalid value for 'server.port'
- Expected: Integer between 1 and 65535
- Found: -80
- Location: Line 8, Column 3
```

## Best Practices

1. Use meaningful names for route mappings
2. Keep filtering rules simple and focused
3. Use comments to document complex configurations
4. Validate configurations before deployment
5. Monitor log files for configuration-related issues 