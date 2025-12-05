"""Example demonstrating resource instrumentation with Shinzo Python SDK."""

import asyncio
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

# Create FastMCP server
mcp = FastMCP(name="shinzo-resources-demo")

# Instrument it with Shinzo
observability = instrument_server(
    mcp,
    config={
        "server_name": "shinzo-resources-demo",
        "server_version": "1.0.0",
        "exporter_auth": {
            "type": "bearer",
            "token": "abc"  # replace with your actual token
        }
    }
)

# Define some tools
@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

# Define resources
@mcp.resource("file:///config/settings.json")
def get_settings() -> dict:
    """Get application settings."""
    return {
        "theme": "dark",
        "language": "en",
        "notifications": True
    }

@mcp.resource("file:///data/users/{user_id}")
def get_user_data(user_id: str) -> dict:
    """Get user data by ID."""
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

@mcp.resource("file:///logs/application.log")
def get_application_logs() -> str:
    """Get application logs."""
    return """
2024-01-15 10:00:00 INFO Application started
2024-01-15 10:01:23 INFO User logged in
2024-01-15 10:05:45 WARN High memory usage detected
2024-01-15 10:10:00 INFO Background task completed
"""

if __name__ == "__main__":
    print("MCP server running with Shinzo instrumentation...")
    print("Resources available:")
    print("  - file:///config/settings.json")
    print("  - file:///data/users/{user_id}")
    print("  - file:///logs/application.log")
    mcp.run()
