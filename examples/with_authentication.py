"""Example with authentication for Shinzo Platform."""

import asyncio
from mcp.server import Server
from shinzo import instrument_server


async def main():
    """Run an instrumented MCP server with authentication."""
    server = Server("authenticated-mcp-server")

    # Instrument with bearer token authentication
    observability = instrument_server(
        server,
        config={
            "server_name": "authenticated-mcp-server",
            "server_version": "1.0.0",
            "exporter_endpoint": "https://app.shinzo.ai/v1/otlp",
            "exporter_auth": {
                "type": "bearer",
                "token": "your-api-token-here"
            },
            "enable_tracing": True,
            "enable_metrics": True,
            "sampling_rate": 1.0,
        }
    )

    @server.call_tool()
    async def greet(name: str) -> str:
        """Greet a user."""
        return f"Hello, {name}!"

    print("Authenticated MCP server running...")
    print("Exporting to Shinzo at: https://app.shinzo.ai")

    try:
        await asyncio.sleep(60)
    finally:
        await observability.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
