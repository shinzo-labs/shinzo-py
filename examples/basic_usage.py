"""Basic usage example for Shinzo Python SDK."""

import asyncio
from mcp.server import Server
from shinzo import instrument_server


async def main():
    """Run a basic instrumented MCP server."""
    # Create your MCP server
    server = Server("example-mcp-server")

    # Instrument it with Shinzo
    observability = instrument_server(
        server,
        config={
            "server_name": "example-mcp-server",
            "server_version": "1.0.0",
            "exporter_endpoint": "http://localhost:8000/v1/otlp",
            "enable_tracing": True,
            "enable_metrics": True,
            "enable_argument_collection": True,
        }
    )

    # Define your tools
    @server.call_tool()
    async def get_weather(city: str) -> str:
        """Get weather for a city."""
        # Simulate some work
        await asyncio.sleep(0.1)
        return f"Weather for {city}: Sunny, 72°F"

    @server.call_tool()
    async def calculate(operation: str, a: float, b: float) -> float:
        """Perform a calculation."""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

    print("MCP server running with Shinzo instrumentation...")
    print("Server will export telemetry to: http://localhost:8000/v1/otlp")

    try:
        # In a real application, the server would run indefinitely
        # For this example, we'll just wait a bit
        await asyncio.sleep(60)
    finally:
        # Clean shutdown
        print("Shutting down...")
        await observability.shutdown()
        print("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
