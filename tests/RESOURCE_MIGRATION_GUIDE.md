# Resource Instrumentation Migration Guide

## For Existing Shinzo Users

If you're already using Shinzo to instrument your MCP server's tools, **no changes are required** to start tracking resources! The instrumentation is automatic.

### What's New

Your existing code:

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

@mcp.tool()
def my_tool(param: str) -> str:
    return f"Result: {param}"
```

Now automatically supports resources:

```python
# Just add resources - they're automatically instrumented!
@mcp.resource("file:///data/config.json")
def get_config() -> dict:
    return {"setting": "value"}
```

## What Gets Tracked

### For Each Resource Operation

1. **Traces**

   - Span name: `resources/read {uri}` or `resources/list list_resources`
   - Attributes:
     - `mcp.method.name`: "resources/read" or "resources/list"
     - `mcp.resource.uri`: The resource URI
     - `mcp.request.id`: Unique request identifier
     - `client.address`: Client address
     - `error.type`: Error type (if failed)

2. **Metrics**

   - Counter: `mcp.server.resources.read.{uri}` or `mcp.server.resources.list.list_resources`
   - Histogram: `mcp.server.operation.duration` (with resource-specific attributes)

3. **Session Events** (if session tracking enabled)
   - Event type: `RESOURCE_LIST` or `RESOURCE_READ`
   - Resource URI
   - Input parameters (if `enable_argument_collection: true`)
   - Output data (if `enable_argument_collection: true`)
   - Duration in milliseconds
   - Error details (if failed)

## Configuration Options

All existing configuration options work with resources:

### Enable/Disable Argument Collection

```python
config = {
    "server_name": "my-server",
    "server_version": "1.0.0",
    "enable_argument_collection": True,  # Captures resource URIs and data
    "exporter_auth": {"type": "bearer", "token": "your-token"}
}
```

### PII Sanitization

```python
config = {
    "server_name": "my-server",
    "server_version": "1.0.0",
    "enable_pii_sanitization": True,  # Sanitizes resource data
    "exporter_auth": {"type": "bearer", "token": "your-token"}
}
```

### Session Tracking

```python
# Enable session tracking to correlate resource reads with tool calls
await observability.instrumentation.enable_session_tracking(
    resource_uuid="user-session-123",
    metadata={"user_id": "user-456"}
)

# All resource operations and tool calls will be tracked in this session
```

## Viewing Resource Telemetry

### In Shinzo Dashboard

1. Navigate to your server in the Shinzo dashboard
2. View the "Resources" tab to see:
   - Most accessed resources
   - Resource read latencies
   - Error rates by resource
   - Resource usage over time

### In Custom OTel Backends

Resource telemetry is exported in standard OpenTelemetry format, so it works with:

- Jaeger
- Zipkin
- Prometheus
- Grafana
- Any OTel-compatible backend

Look for spans with:

- `mcp.method.name = "resources/read"` or `"resources/list"`
- `mcp.resource.uri` attribute

## Example Use Cases

### 1. Track Configuration Access

```python
@mcp.resource("file:///config/app-settings.json")
def get_app_settings() -> dict:
    return load_settings()

# Telemetry shows:
# - How often settings are accessed
# - Which clients access settings
# - Settings read latency
```

### 2. Monitor Database Resources

```python
@mcp.resource("db:///users/{user_id}")
def get_user(user_id: str) -> dict:
    return db.query_user(user_id)

# Telemetry shows:
# - Most frequently accessed users
# - Database query performance
# - Error rates for user lookups
```

### 3. Track File Access Patterns

```python
@mcp.resource("file:///{path}")
def read_file(path: str) -> str:
    return read_file_content(path)

# Telemetry shows:
# - Which files are accessed most
# - File read performance
# - Access patterns over time
```

## Troubleshooting

### Resources Not Showing in Telemetry

1. **Check server type detection**

   ```python
   # Verify your server has the resource decorator
   print(hasattr(mcp, "resource"))  # Should be True for FastMCP
   ```

2. **Verify instrumentation**

   ```python
   # Check that instrumentation is active
   print(observability.instrumentation.is_instrumented)  # Should be True
   ```

3. **Check exporter configuration**
   ```python
   # Ensure exporter is configured correctly
   config = {
       "exporter_endpoint": "https://api.app.shinzo.ai/telemetry/ingest_http",
       "exporter_auth": {"type": "bearer", "token": "your-token"}
   }
   ```

### High Cardinality URIs

If you have resources with many unique URIs (e.g., `file:///{path}` with thousands of paths):

1. **Use sampling**

   ```python
   config = {
       "sampling_rate": 0.1,  # Sample 10% of requests
   }
   ```

2. **Disable argument collection for specific resources**
   - This is a global setting currently
   - Consider using custom data processors to filter high-cardinality data

## Best Practices

1. **Use descriptive URIs**: Make resource URIs meaningful for analytics

   - ✅ `file:///config/database.json`
   - ❌ `file:///cfg/db.json`

2. **Group related resources**: Use consistent URI patterns

   - ✅ `db:///users/{id}`, `db:///posts/{id}`
   - ❌ `user-{id}`, `post-data-{id}`

3. **Enable session tracking**: Correlate resource reads with tool calls

   ```python
   await observability.instrumentation.enable_session_tracking("session-id")
   ```

4. **Monitor resource performance**: Set up alerts for slow resource reads

   - Track `mcp.server.operation.duration` metric
   - Alert on p95 > threshold

5. **Use PII sanitization**: Protect sensitive data in resource content
   ```python
   config = {"enable_pii_sanitization": True}
   ```

## Upgrading

To get resource instrumentation support:

```bash
pip install --upgrade shinzo
```

No code changes required - existing instrumentation automatically includes resources!

## Support

If you encounter issues with resource instrumentation:

1. Check the [GitHub Issues](https://github.com/shinzo-labs/shinzo-py/issues)
2. Join the [Discord community](https://discord.gg/UYUdSdp5N8)
3. Review the [documentation](https://docs.shinzo.ai)
