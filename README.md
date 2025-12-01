<a id="readme-top"></a>
<div align="center">
    <a href="https://github.com/shinzo-labs/shinzo-py"><img src="https://github.com/user-attachments/assets/64f5e0ae-6924-41b1-b1da-1b22627e5c43" alt="Logo" width="256" height="256"></a>
    <h1 align="center">
        Shinzo Python SDK: Complete Observability for MCP Servers
    </h1>
    <p align=center>
        <a href="https://github.com/shinzo-labs/shinzo-py/stargazers"><img src="https://img.shields.io/github/stars/shinzo-labs/shinzo-py?style=flat&logo=github&color=e3b341" alt="Stars"></a>
        <a href="https://github.com/shinzo-labs/shinzo-py/forks"><img src="https://img.shields.io/github/forks/shinzo-labs/shinzo-py?style=flat&logo=github&color=8957e5" alt="Forks"></a>
        <a href="https://github.com/shinzo-labs/shinzo-py/pulls"><img src="https://img.shields.io/badge/build-passing-green" alt="Build"></a>
        <a href="https://github.com/shinzo-labs/shinzo-py/graphs/contributors"><img src="https://img.shields.io/badge/contributors-welcome-339933?logo=github" alt="contributors welcome"></a>
        <a href="https://discord.gg/UYUdSdp5N8"><img src="https://discord-live-members-count-badge.vercel.app/api/discord-members?guildId=1079318797590216784" alt="Discord"></a>
    </p>
    The SDK provides OpenTelemetry-compatible instrumentation for Python MCP servers. Gain insight into agent usage patterns, contextualize tool calls, and analyze performance of your servers across platforms. Instrumentation can be installed in servers in just a few steps with an emphasis on ease of use and flexibility.
    <p align=center>
        <a href="https://docs.shinzo.ai/sdk/python/installation"><strong>Explore the docs »</strong></a>
    </p>
</div>

## Installation

The Shinzo Python instrumentation library works with Python MCP servers built with the core MCP SDK or FastMCP. Simply install the base package:

```bash
pip install shinzo
```

## Quick Start

Choose the example that matches your MCP SDK:

### FastMCP Example

```python
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

# Create FastMCP server
mcp = FastMCP(name="my-mcp-server")

# Instrument it with Shinzo
observability = instrument_server(
    mcp,
    config={
        "server_name": "my-mcp-server",
        "server_version": "1.0.0",
        "exporter_auth": {
            "type": "bearer",
            "token": "your-api-token"
        }
    }
)

# Define your tools
@mcp.tool()
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather for {city}: Sunny"

# Run the server
if __name__ == "__main__":
    mcp.run()
```

###  MCP SDK Example

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

## SDK Compatibility

Shinzo automatically detects and instruments your MCP server regardless of which SDK you use:

| SDK | Detection Method | Decorator | Use Case |
|-----|-----------------|-----------|----------|
| **FastMCP** | `server.tool` attribute | `@mcp.tool()` | Simpler API, modern Python patterns, recommended for new projects |
| **Traditional MCP** | `server.call_tool` attribute | `@server.call_tool()` | Standard MCP specification, more configuration options |

Both SDKs receive the same comprehensive instrumentation with no additional configuration needed.

## Features

- 🔍 **Automatic Instrumentation** - Zero-code changes for basic tracing across both FastMCP and Traditional MCP
- 📊 **Rich Metrics** - Track request duration, error rates, and custom metrics
- 🔐 **PII Sanitization** - Built-in sensitive data protection
- 🎯 **Session Tracking** - Correlate all requests in a user session
- ⚡ **High Performance** - Minimal overhead with efficient batching
- 🛠️ **Flexible Configuration** - Customize sampling, exporters, and processors

## Configuration

| Setting | Required | Type | Default | Description |
|---------|----------|------|---------|-------------|
| `server_name` | ✅ | `str` | - | Name of your MCP server |
| `server_version` | ✅ | `str` | - | Version of your MCP server |
| `exporter_endpoint` | ❌ | `str` | `"https://api.app.shinzo.ai/telemetry/ingest_http"` | OTLP endpoint URL for telemetry export |
| `exporter_auth` | ❌ | `AuthConfig` | `None` | Authentication configuration for the exporter |
| `exporter_type` | ❌ | `"otlp-http"` \| `"console"` | `"otlp-http"` | Type of exporter to use |
| `sampling_rate` | ❌ | `float` | `1.0` | Trace sampling rate (0.0-1.0) |
| `enable_metrics` | ❌ | `bool` | `True` | Enable metrics collection |
| `enable_tracing` | ❌ | `bool` | `True` | Enable distributed tracing |
| `enable_pii_sanitization` | ❌ | `bool` | `False` | Enable automatic PII sanitization |
| `enable_argument_collection` | ❌ | `bool` | `True` | Collect and include tool arguments in telemetry |
| `metric_export_interval_ms` | ❌ | `int` | `60000` | Interval for exporting metrics (milliseconds) |
| `batch_timeout_ms` | ❌ | `int` | `30000` | Timeout for batching telemetry data (milliseconds) |
| `data_processors` | ❌ | `list[Callable]` | `None` | Custom data processors for telemetry attributes |
| `pii_sanitizer` | ❌ | `PIISanitizer` | `None` | Custom PII sanitizer instance |

### Authentication Configuration (`exporter_auth`)

| Setting | Required | Type | Description |
|---------|----------|------|-------------|
| `type` | ✅ | `"bearer"` \| `"apiKey"` \| `"basic"` | Authentication method |
| `token` | ❌ | `str` | Bearer token (required when `type="bearer"`) |
| `api_key` | ❌ | `str` | API key (required when `type="apiKey"`) |
| `username` | ❌ | `str` | Username (required when `type="basic"`) |
| `password` | ❌ | `str` | Password (required when `type="basic"`) |

## Testing

Run the test suite to verify the library's behavior:

```bash
# Run all tests
python -m pytest tests/

# Run with coverage report
python -m pytest tests/ --cov=shinzo --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_config.py -v
```

The test suite validates:
- ✅ Configuration validation and error handling
- ✅ PII sanitization for emails and sensitive data
- ✅ Authentication configuration (bearer, basic, API key)
- ✅ Sampling rate validation

## License

This package is distributed under the [MIT License](./LICENSE.md).

## Contributing

Contributions are welcome! Please see the [Contributing Guide](./CONTRIBUTING.md) for more information.
