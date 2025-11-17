"""Test protobuf telemetry ingestion to local backend."""

import asyncio
import time
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

# Create FastMCP server
mcp = FastMCP(name="test-protobuf")

# Instrument it with Shinzo pointing to local backend
observability = instrument_server(
    mcp,
    config={
        "server_name": "test-protobuf-server",
        "server_version": "1.0.0",
        "exporter_endpoint": "http://localhost:8000/telemetry/ingest_http",
        "exporter_auth": {
            "type": "bearer",
            "token": "abc"  # Using test token
        }
    }
)

@mcp.tool()
def test_add(a: int, b: int) -> int:
    """Test addition tool."""
    return a + b

async def test_tool_call():
    """Test a tool call to generate telemetry."""
    print("Testing tool call...")
    result = test_add(5, 3)
    print(f"Result: {result}")
    # Wait for telemetry to be exported
    await asyncio.sleep(3)
    print("Telemetry should have been sent!")

if __name__ == "__main__":
    print("Testing protobuf telemetry ingestion...")
    print("Server will export telemetry to: http://localhost:8000/telemetry/ingest_http")
    asyncio.run(test_tool_call())
    # Shutdown to flush telemetry
    asyncio.run(observability.shutdown())
    print("Test complete!")
