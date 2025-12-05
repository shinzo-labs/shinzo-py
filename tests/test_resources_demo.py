"""Minimal MCP server to test resource instrumentation."""

from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

# Create server
mcp = FastMCP(name="resource-test")

# Instrument with console output
observability = instrument_server(
    mcp,
    config={
        "server_name": "resource-test",
        "server_version": "1.0.0",
        "exporter_type": "console",  # Print telemetry to console
        "enable_argument_collection": True
    }
)

# Define a tool
@mcp.tool()
def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"

# Define resources
@mcp.resource("config://settings")
def get_settings() -> dict:
    """Get app settings."""
    print("📦 Resource accessed: config://settings")
    return {"theme": "dark", "version": "1.0"}

@mcp.resource("data://users/{user_id}")
def get_user(user_id: str) -> dict:
    """Get user data."""
    print(f"📦 Resource accessed: data://users/{user_id}")
    return {"id": user_id, "name": f"User {user_id}"}

if __name__ == "__main__":
    print("🚀 Starting MCP server with resource instrumentation...")
    print("📊 Telemetry will be printed to console")
    print("\nAvailable operations:")
    print("  🔧 Tool: greet(name)")
    print("  📦 Resource: config://settings")
    print("  📦 Resource: data://users/{user_id}")
    print("\nPress Ctrl+C to stop\n")
    mcp.run()
