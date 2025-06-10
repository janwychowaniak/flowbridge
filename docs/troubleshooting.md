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