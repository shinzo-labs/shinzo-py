# Resource Instrumentation Implementation Summary

## Overview

This implementation adds comprehensive support for MCP Resources telemetry to the Shinzo Python SDK, enabling developers to track and analyze resource usage patterns in their MCP servers.

## Changes Made

### 1. Session Event Types (`src/shinzo/session.py`)

- **Added new EventTypes**: `RESOURCE_LIST` and `RESOURCE_READ` to track resource operations
- **Extended SessionEvent dataclass**: Added `resource_uri` field to capture resource URIs
- **Updated event serialization**: Modified `_send_to_backend` to include `resource_uri` in event payloads

### 2. Core Instrumentation (`src/shinzo/instrumentation.py`)

#### New Methods

- `_instrument_resources()`: Main entry point for resource instrumentation, detects FastMCP vs traditional MCP
- `_instrument_fastmcp_resources()`: Wraps FastMCP's `@mcp.resource()` decorator
- `_instrument_traditional_resources()`: Wraps traditional MCP's `list_resources` and `read_resource` methods

#### Enhanced Methods

- `instrument()`: Now calls `_instrument_resources()` alongside `_instrument_tools()`
- `_create_instrumented_handler()`: Updated to use appropriate attributes (`mcp.resource.uri` vs `mcp.tool.name`) based on operation type
- `_execute_instrumented_call()`: Enhanced to:
  - Detect resource vs tool operations via method name
  - Log appropriate event types (RESOURCE_LIST, RESOURCE_READ, or TOOL_CALL/TOOL_RESPONSE)
  - Track resource URIs in session events
  - Handle errors for both resource and tool operations

### 3. Documentation (`README.md`)

- Added "Resource Instrumentation" section with FastMCP example
- Updated Features section to highlight complete MCP coverage
- Added resource instrumentation to test validation list

### 4. Examples (`examples/resource_usage.py`)

Created a comprehensive example demonstrating:

- Multiple resource types (settings, user data, logs)
- Resource URI patterns
- Integration with tools
- Proper instrumentation setup

### 5. Tests (`tests/test_resource_instrumentation.py`)

Added comprehensive test coverage for:

- FastMCP resource instrumentation
- Traditional MCP resource instrumentation
- Session tracking capabilities
- New EventType enums

## Technical Details

### Resource Detection

The implementation detects resource operations by checking the `method` parameter:

- `resources/list` → RESOURCE_LIST event
- `resources/read` → RESOURCE_READ event

### Telemetry Attributes

Resource operations are tracked with:

- `mcp.method.name`: The MCP method (e.g., "resources/read")
- `mcp.resource.uri`: The resource URI (e.g., "file:///config/settings.json")
- Standard attributes: request ID, client address, duration, error status

### Session Tracking

Resource operations are fully integrated with session tracking:

- Resource reads/lists are logged as session events
- Events include resource URI, input/output data (if enabled), duration, and metadata
- Errors are tracked with resource context

## Compatibility

### FastMCP

- Automatically wraps `@mcp.resource()` decorator
- No code changes required in user applications
- Works with both static and parameterized resources

### Traditional MCP

- Wraps `list_resources` and `read_resource` decorators
- Compatible with standard MCP specification
- Supports validation options

## OTel Compatibility

All resource telemetry is exported in OpenTelemetry-compatible format:

- Traces with resource-specific spans
- Metrics for resource operation duration and counts
- Proper error tracking and status codes

## Usage Example

```python
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

mcp = FastMCP(name="my-server")

observability = instrument_server(
    mcp,
    config={
        "server_name": "my-server",
        "server_version": "1.0.0",
        "exporter_auth": {"type": "bearer", "token": "your-token"}
    }
)

# Resources are automatically instrumented
@mcp.resource("file:///config/settings.json")
def get_settings() -> dict:
    return {"theme": "dark", "language": "en"}
```

## Testing

All tests pass (13/13):

- ✅ Resource instrumentation for FastMCP
- ✅ Resource instrumentation for traditional MCP
- ✅ Session tracking capabilities
- ✅ EventType validation
- ✅ Existing functionality preserved

## Benefits for MCP Developers

1. **Usage Analytics**: Track which resources are accessed most frequently
2. **Performance Monitoring**: Measure resource read latencies
3. **Error Tracking**: Identify problematic resources
4. **Session Context**: Understand resource usage patterns within user sessions
5. **Zero Configuration**: Automatic instrumentation with no code changes required
