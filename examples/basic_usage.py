"""Basic usage example for Shinzo Python SDK with FastMCP."""

import asyncio
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

# Create FastMCP server
mcp = FastMCP(name="shinzo-py-demo")

# Instrument it with Shinzo
observability = instrument_server(
    mcp,
    config={
        "server_name": "shinzo-py-demo",
        "server_version": "1.0.0",
        "exporter_auth": {"type": "bearer", "token": "abc"},  # replace with your actual token
    },
)


@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def get_weather(city: str, unit: str = "celsius") -> str:
    """Get weather for a city."""
    # This would normally call a weather API
    return f"Weather in {city}: 22 degrees {unit[0].upper()}"


if __name__ == "__main__":
    print("MCP server running with Shinzo instrumentation...")
    mcp.run()
