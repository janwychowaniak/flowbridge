# FlowBridge Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using FlowBridge.

## Configuration Issues

### YAML Syntax Errors

#### Problem: Invalid YAML Syntax
```
Configuration Error: YAML syntax error
- Line 5, Column 3
- Found unexpected character ':'
```

**Solution**:
1. Check indentation (must use spaces, not tabs)
2. Verify colon placement in key-value pairs
3. Ensure lists are properly formatted with dashes
4. Use YAML validator to check syntax

#### Problem: Invalid Value Type
```
Configuration Error: Invalid value type
- Field: server.port
- Expected: integer
- Found: string "8000"
```

**Solution**:
1. Remove quotes from numeric values
2. Ensure boolean values are true/false (not "true"/"false")
3. Check list formatting for array values

### Field Path Errors

#### Problem: Invalid Field Path
```
Configuration Error: Invalid field path
- Field: user..name
- Error: Empty field name in path
```

**Solution**:
1. Remove duplicate dots
2. Verify field names exist
3. Check array index format
4. Maximum path depth is 10 levels

#### Problem: Array Index Format
```
Configuration Error: Invalid array index
- Field: items.[0].id
- Error: Invalid array index syntax
```

**Solution**:
1. Use numeric index directly (items.0.id)
2. Ensure index is non-negative
3. Remove square brackets

### Operator Errors

#### Problem: Invalid Operator
```
Configuration Error: Invalid operator
- Field: status
- Operator: contains
- Error: Unsupported operator
```

**Solution**:
1. Use supported operators:
   - equals
   - not_equals
   - in
   - contains_any
   - less_than
   - greater_than
2. Check operator spelling
3. Verify operator compatibility with value type

#### Problem: Type Mismatch
```
Configuration Error: Type mismatch
- Field: priority
- Operator: greater_than
- Value: "high"
- Error: Numeric operator requires numeric value
```

**Solution**:
1. Use numeric values for numeric comparisons
2. Use string values for string comparisons
3. Check value type matches operator requirements

### URL Configuration

#### Problem: Invalid URL Format
```
Configuration Error: Invalid URL
- URL: destination1/endpoint
- Error: Missing scheme (http:// or https://)
```

**Solution**:
1. Add http:// or https:// prefix
2. Use absolute URLs
3. Properly encode special characters
4. Remove authentication information from URLs

#### Problem: URL Length
```
Configuration Error: URL too long
- URL length: 2500
- Maximum allowed: 2048
```

**Solution**:
1. Shorten URL path
2. Remove unnecessary query parameters
3. Consider URL shortening service
4. Split into multiple endpoints if needed

## Runtime Issues

### Connection Errors

#### Problem: Destination Timeout
```
Runtime Error: Destination timeout
- URL: http://destination/endpoint
- Timeout: 2 seconds
```

**Solution**:
1. Check destination server status
2. Increase route_timeout in configuration
3. Verify network connectivity
4. Check firewall rules

#### Problem: Connection Refused
```
Runtime Error: Connection refused
- URL: http://internal-service:8080
- Error: Connection actively refused
```

**Solution**:
1. Verify service is running
2. Check port number
3. Verify firewall rules
4. Ensure service accepts connections from FlowBridge IP

### Performance Issues

#### Problem: High Memory Usage
```
Warning: High memory usage
- Current: 85%
- Threshold: 80%
```

**Solution**:
1. Reduce number of worker processes
2. Optimize filtering rules
3. Check for memory leaks
4. Monitor system resources

#### Problem: High CPU Usage
```
Warning: High CPU usage
- Current: 95%
- Threshold: 80%
```

**Solution**:
1. Simplify filtering rules
2. Adjust worker count
3. Check for infinite loops
4. Monitor system load

### Logging Issues

#### Problem: Log File Size
```
Warning: Log file size exceeds rotation threshold
- Current size: 250MB
- Rotation size: 200MB
```

**Solution**:
1. Adjust log_rotation setting
2. Implement log cleanup
3. Reduce log verbosity
4. Archive old logs

#### Problem: Missing Logs
```
Warning: No log entries found
- Time period: Last 1 hour
- Log level: info
```

**Solution**:
1. Check log_level setting
2. Verify log file permissions
3. Check disk space
4. Ensure logging is enabled

## Webhook Processing Issues

### Request Format Errors

#### Problem: Invalid JSON Payload
```
Error: Invalid JSON format
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Status: 400 Bad Request
```

**Solution**:
1. Validate JSON syntax before sending
2. Ensure proper escaping of special characters
3. Check for trailing commas or missing quotes
4. Use JSON validator tools

#### Problem: Missing Content-Type Header
```
Error: Missing or invalid Content-Type header
- Expected: application/json
- Found: text/plain
```

**Solution**:
1. Include `Content-Type: application/json` header
2. Verify header is set correctly in HTTP client
3. Check for typos in header name or value

#### Problem: Non-Dictionary Payload
```
Error: Payload must be a JSON object
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Payload type: string
```

**Solution**:
1. Ensure payload is a JSON object (dictionary)
2. Wrap array payloads in object structure
3. Avoid sending primitive values (strings, numbers)

### Filtering Stage Issues

#### Problem: Request Unexpectedly Dropped
```
Response: Request dropped by filtering rules
- Rules evaluated: 2
- Default action applied: true
- Result: dropped
```

**Solution**:
1. Review filtering rules in configuration
2. Check if payload fields match rule criteria
3. Verify field paths are correct
4. Consider adjusting default_action to "pass"

#### Problem: Field Extraction Errors
```
Warning: Field extraction failed
- Field path: object.details.severity
- Error: Field not found in payload
```

**Solution**:
1. Verify field exists in payload structure
2. Check for typos in field path
3. Ensure case sensitivity matches
4. Consider using optional field handling

#### Problem: Filtering Rules Not Applied
```
Warning: No filtering rules evaluated
- Rules configured: 3
- Rules evaluated: 0
```

**Solution**:
1. Check filtering configuration syntax
2. Verify rules are properly formatted
3. Ensure logic operator is valid (AND/OR)
4. Test with simplified rule set

### Processing Pipeline Errors

#### Problem: Internal Processing Error
```
Error: Internal server error during processing
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Status: 500 Internal Server Error
```

**Solution**:
1. Check application logs for detailed error
2. Verify configuration is valid
3. Ensure adequate system resources
4. Restart application if needed

#### Problem: Request Context Issues
```
Error: Request context corruption
- Request ID: missing
- Stage: unknown
```

**Solution**:
1. Check middleware configuration
2. Verify request processing order
3. Ensure proper error handling
4. Review application startup logs

### Performance and Scalability

#### Problem: Slow Webhook Response
```
Warning: Webhook processing taking too long
- Average response time: 2.5 seconds
- Expected: < 1 second
```

**Solution**:
1. Optimize filtering rules complexity
2. Reduce number of rules evaluated
3. Check system resource usage
4. Consider increasing worker processes

#### Problem: Memory Usage During Processing
```
Warning: High memory usage during webhook processing
- Memory per request: 50MB
- Expected: < 10MB
```

**Solution**:
1. Check for large JSON payloads
2. Optimize field extraction logic
3. Review filtering rule complexity
4. Monitor garbage collection

### Request Correlation Issues

#### Problem: Missing Request ID
```
Error: Request ID not found in response
- Endpoint: /webhook
- Status: 200 OK
```

**Solution**:
1. Verify middleware is properly configured
2. Check request preprocessing
3. Ensure error handling preserves request ID
4. Review logging configuration

#### Problem: Request ID Mismatch
```
Error: Request ID inconsistency
- Header ID: 550e8400-e29b-41d4-a716-446655440000
- Response ID: 778b2d1f-b234-4a12-9876-123456789abc
```

**Solution**:
1. Check request context handling
2. Verify concurrent request isolation
3. Review error handling logic
4. Ensure proper UUID generation

## Best Practices

### Configuration Management

1. Version Control
   - Keep configurations in version control
   - Document changes
   - Use meaningful commit messages

2. Testing
   - Test configurations in development
   - Validate before deployment
   - Use --validate-only flag

3. Monitoring
   - Monitor log files
   - Set up alerts
   - Track performance metrics

### Security

1. URL Security
   - Use HTTPS where possible
   - Avoid sensitive data in URLs
   - Validate destination certificates

2. Access Control
   - Restrict configuration file access
   - Use secure file permissions
   - Monitor configuration changes

3. Network Security
   - Use firewall rules
   - Restrict access to necessary ports
   - Monitor network traffic

## Getting Help

If you encounter issues not covered in this guide:

1. Check the latest documentation
2. Review log files for detailed error messages
3. Search issue tracker for similar problems
4. Create detailed bug report with:
   - Configuration file (sanitized)
   - Error messages
   - Log excerpts
   - Steps to reproduce 