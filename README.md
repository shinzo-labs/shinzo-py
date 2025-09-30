# Shinzo Python SDK

Complete Observability for MCP servers in Python.

## Installation

```bash
pip install shinzo
```

## Quick Start

```python
from mcp.server import Server
from shinzo import instrument_server

# Create your MCP server
server = Server("my-mcp-server")

# Instrument it with Shinzo
observability = instrument_server(
    server,
    config={
        "server_name": "my-mcp-server",
        "server_version": "1.0.0",
        "exporter_endpoint": "https://app.shinzo.ai/v1/otlp",
        "exporter_auth": {
            "type": "bearer",
            "token": "your-api-token"
        }
    }
)

# Define your tools
@server.call_tool()
async def get_weather(city: str) -> str:
    return f"Weather for {city}: Sunny"

# Clean shutdown
async def shutdown():
    await observability.shutdown()
```

## Features

- 🔍 **Automatic Instrumentation** - Zero-code changes for basic tracing
- 📊 **Rich Metrics** - Track request duration, error rates, and custom metrics
- 🔐 **PII Sanitization** - Built-in sensitive data protection
- 🎯 **Session Tracking** - Correlate all requests in a user session
- ⚡ **High Performance** - Minimal overhead with efficient batching
- 🛠️ **Flexible Configuration** - Customize sampling, exporters, and processors

## Configuration

### Required Settings

- `server_name`: Name of your MCP server
- `server_version`: Version of your MCP server

### Optional Settings

- `exporter_endpoint`: OTLP endpoint URL (default: http://localhost:4318/v1/otlp)
- `exporter_auth`: Authentication configuration
- `sampling_rate`: Trace sampling rate (0.0-1.0, default: 1.0)
- `enable_metrics`: Enable metrics collection (default: True)
- `enable_tracing`: Enable tracing (default: True)
- `enable_pii_sanitization`: Enable PII sanitization (default: False)
- `enable_argument_collection`: Collect tool arguments (default: True)
- `metric_export_interval_ms`: Metric export interval (default: 60000)
- `batch_timeout_ms`: Batch timeout (default: 30000)

## License

MIT License - see LICENSE file for details
