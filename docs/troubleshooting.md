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

## Routing Stage Issues

### Route Configuration Errors

#### Problem: No Routing Rules Found
```
Error: No routing configuration found
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Status: 500 Internal Server Error
```

**Solution**:
1. Ensure `routes` section exists in configuration
2. Verify route configuration syntax
3. Check for YAML indentation errors
4. Validate route mapping format

#### Problem: Invalid Route Field Path
```
Error: Invalid routing field path
- Field: object..title
- Error: Empty field name in path
```

**Solution**:
1. Remove duplicate dots in field path
2. Verify field path syntax matches dot notation
3. Check field exists in expected payloads
4. Use proper nesting syntax (e.g., `object.details.title`)

#### Problem: Empty Route Mappings
```
Configuration Error: Empty route mappings
- Route field: object.title
- Mappings count: 0
```

**Solution**:
1. Add at least one mapping to routes
2. Verify mapping syntax: `key: value`
3. Ensure destination URLs are valid
4. Check for duplicate mapping keys

### Route Matching Issues

#### Problem: No Route Match Found
```
Error: No routing rule matched
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Status: 404 Not Found
- Routing field: object.title
- Routing value: "unknown-alert-type"
- Rules checked: 1
```

**Solution**:
1. Check if routing value exists in route mappings
2. Verify exact string matching (case-sensitive)
3. Add mapping for the specific value
4. Consider using wildcard or default routes
5. Check field extraction is working correctly

#### Problem: Route Field Missing from Payload
```
Warning: Routing field not found in payload
- Field path: object.title
- Payload structure: {...}
```

**Solution**:
1. Verify field exists in incoming payload
2. Check field path spelling and case sensitivity
3. Ensure payload structure matches expected format
4. Consider using optional field handling

#### Problem: Route Field Value is Null/Empty
```
Warning: Routing field value is null or empty
- Field path: object.title
- Field value: null
```

**Solution**:
1. Check payload data quality at source
2. Add validation for required fields
3. Consider default value handling
4. Review data transformation before routing

### Route Performance Issues

#### Problem: Slow Route Evaluation
```
Warning: Route evaluation taking too long
- Evaluation time: 150ms
- Expected: < 10ms
- Rules checked: 100
```

**Solution**:
1. Reduce number of route mappings
2. Optimize route ordering (most common first)
3. Consider route indexing strategies
4. Review field extraction performance

#### Problem: High Memory Usage in Routing
```
Warning: High memory usage during routing
- Memory per route evaluation: 25MB
- Expected: < 1MB
```

**Solution**:
1. Check for large route mapping tables
2. Optimize route data structures
3. Review route caching strategies
4. Consider route configuration compression

## Forwarding Stage Issues

### Network Connection Errors

#### Problem: Connection Refused by Destination
```
Error: Failed to forward request to destination
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Status: 502 Bad Gateway
- Destination URL: http://dest_url_0/ep/
- Error type: CONNECTION_ERROR
```

**Solution**:
1. Verify destination service is running
2. Check destination host and port
3. Verify network connectivity to destination
4. Check firewall rules between FlowBridge and destination
5. Validate destination URL format

#### Problem: DNS Resolution Failure
```
Error: Failed to resolve destination hostname
- Destination URL: http://invalid-host.example.com/ep/
- Error: Name resolution failed
```

**Solution**:
1. Verify destination hostname is correct
2. Check DNS server configuration
3. Test DNS resolution manually (`nslookup`, `dig`)
4. Consider using IP addresses instead of hostnames
5. Check network DNS settings

#### Problem: SSL/TLS Certificate Issues
```
Error: SSL certificate verification failed
- Destination URL: https://dest_url_0/ep/
- Error: Certificate verification failed
```

**Solution**:
1. Verify destination SSL certificate validity
2. Check certificate chain completeness
3. Ensure certificate matches hostname
4. Consider certificate authority trust issues
5. Review SSL/TLS configuration

### Timeout and Performance Issues

#### Problem: Request Timeout to Destination
```
Error: Request timeout to destination
- Request ID: 550e8400-e29b-41d4-a716-446655440000
- Status: 504 Gateway Timeout
- Destination URL: http://dest_url_0/ep/
- Error type: TIMEOUT_ERROR
- Timeout: 2 seconds
```

**Solution**:
1. Increase `route_timeout` in configuration
2. Check destination service performance
3. Verify network latency to destination
4. Consider destination load and capacity
5. Monitor destination service health

#### Problem: Slow Destination Response
```
Warning: Destination responding slowly
- Response time: 1.8 seconds
- Configured timeout: 2 seconds
- Risk: Near timeout threshold
```

**Solution**:
1. Monitor destination service performance
2. Increase timeout if acceptable for use case
3. Optimize destination service
4. Consider load balancing destinations
5. Review destination resource allocation

#### Problem: High Forwarding Latency
```
Warning: High forwarding latency
- Average forwarding time: 800ms
- Expected: < 200ms
- Destinations affected: 3
```

**Solution**:
1. Check network connectivity and routing
2. Monitor destination service response times
3. Consider geographic proximity of destinations
4. Review network infrastructure
5. Optimize HTTP client configuration

### HTTP Protocol Issues

#### Problem: Destination Returns HTTP Errors
```
Warning: Destination returned HTTP error
- Status code: 500 Internal Server Error
- Destination response: {"error": "Database connection failed"}
- Action: Error passed through to client
```

**Solution**:
1. Check destination service logs
2. Verify destination service health
3. Monitor destination error rates
4. Consider circuit breaker patterns
5. Review destination service configuration

#### Problem: Large Response Payload Issues
```
Warning: Large response from destination
- Response size: 50MB
- Processing time: 5 seconds
- Memory usage: High
```

**Solution**:
1. Implement response size limits
2. Enable response streaming
3. Compress responses if possible
4. Monitor memory usage patterns
5. Consider pagination for large datasets

#### Problem: Response Format Issues
```
Warning: Unexpected response format from destination
- Expected: JSON
- Received: text/html
- Content-Type: text/html
```

**Solution**:
1. Verify destination API specification
2. Check request headers sent to destination
3. Validate destination endpoint configuration
4. Review API version compatibility
5. Monitor destination service changes

### Connection Pool and Resource Issues

#### Problem: Connection Pool Exhaustion
```
Error: HTTP connection pool exhausted
- Active connections: 100
- Pool size limit: 100
- Queued requests: 50
```

**Solution**:
1. Increase HTTP connection pool size
2. Optimize connection reuse
3. Reduce connection timeout
4. Monitor connection lifecycle
5. Consider destination-specific pools

#### Problem: Memory Leaks in HTTP Client
```
Warning: Memory usage increasing over time
- Initial memory: 100MB
- Current memory: 500MB
- Requests processed: 10,000
```

**Solution**:
1. Review HTTP client configuration
2. Check for unclosed connections
3. Monitor response handling
4. Implement connection lifecycle management
5. Consider restarting workers periodically

## Network and Infrastructure Issues

### Load and Scalability Issues

#### Problem: High Concurrent Request Load
```
Warning: High concurrent request processing
- Concurrent requests: 57
- Success rate: 100%
- Average response time: 25ms
```

**Monitoring Recommendations**:
1. Monitor system resource usage
2. Track error rates across all stages
3. Monitor destination service capacity
4. Review worker process utilization
5. Consider horizontal scaling

#### Problem: Resource Exhaustion Under Load
```
Error: System resource exhaustion
- CPU usage: 95%
- Memory usage: 90%
- Active connections: 500
```

**Solution**:
1. Scale worker processes appropriately
2. Optimize processing pipeline efficiency
3. Implement request queuing
4. Monitor system resource limits
5. Consider hardware upgrades

### Monitoring and Observability

#### Problem: Missing Forwarding Metrics
```
Warning: Unable to track forwarding performance
- Metrics available: Basic
- Missing: Destination-specific timing
```

**Solution**:
1. Enable detailed request logging
2. Implement destination-specific metrics
3. Monitor forwarding success rates
4. Track timeout occurrences
5. Set up alerting for failures

#### Problem: Poor Error Visibility
```
Warning: Forwarding errors not well tracked
- Error categorization: Basic
- Root cause analysis: Difficult
```

**Solution**:
1. Enhance error logging detail
2. Implement structured error reporting
3. Add destination health monitoring
4. Create error dashboards
5. Set up proactive alerting

## Advanced Troubleshooting

### End-to-End Request Tracing

#### Problem: Request Processing Visibility
```
Challenge: Difficult to trace request through all stages
- Stages: Validation → Filtering → Routing → Forwarding
- Correlation: Request ID tracking
```

**Troubleshooting Steps**:
1. Enable detailed logging for each stage
2. Track request ID through entire pipeline
3. Monitor processing time per stage
4. Review error handling at each stage
5. Implement distributed tracing if needed

#### Problem: Performance Bottleneck Identification
```
Challenge: Identifying slowest stage in pipeline
- Total processing time: 500ms
- Stage breakdown: Unknown
```

**Solution**:
1. Add timing instrumentation per stage
2. Monitor stage-specific performance
3. Identify bottleneck patterns
4. Optimize critical path stages
5. Balance processing across workers

### Production Readiness Issues

#### Problem: Destination Service Integration
```
Challenge: Integration with real destination services
- Test environments: Mock servers
- Production: Real services with different behavior
```

**Recommendations**:
1. Test with real destination services
2. Validate timeout configurations under load
3. Monitor destination service dependencies
4. Implement circuit breaker patterns
5. Plan for destination service failures

#### Problem: High Availability Requirements
```
Challenge: Ensuring system reliability
- Uptime requirement: 99.9%
- Error handling: Critical
```

**Solution**:
1. Implement comprehensive health checks
2. Monitor all system dependencies
3. Plan for graceful degradation
4. Implement retry mechanisms where appropriate
5. Design for fault tolerance

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