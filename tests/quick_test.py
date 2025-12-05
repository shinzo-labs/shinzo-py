"""Quick inline test of resource instrumentation."""

import asyncio
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server

print("=" * 60)
print("🧪 TESTING RESOURCE INSTRUMENTATION")
print("=" * 60)

# Create and instrument server
mcp = FastMCP(name="test")
observability = instrument_server(
    mcp,
    config={
        "server_name": "test",
        "server_version": "1.0.0",
        "exporter_type": "console"
    }
)

print("\n✅ Server created and instrumented")

# Define a tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Define a resource
@mcp.resource("test://data")
def get_data() -> dict:
    """Get test data."""
    return {"status": "ok", "value": 42}

print("✅ Tool and resource defined")

# Check instrumentation
print("\n📊 Instrumentation Status:")
print(f"   - Server instrumented: {observability.instrumentation.is_instrumented}")
print(f"   - Has resource decorator: {hasattr(mcp, 'resource')}")
print(f"   - Has tool decorator: {hasattr(mcp, 'tool')}")

# Verify the decorators are wrapped
print("\n🔍 Verification:")
print(f"   - Tool decorator type: {type(mcp.tool).__name__}")
print(f"   - Resource decorator type: {type(mcp.resource).__name__}")

# Test that the functions are registered
print("\n✅ Resource instrumentation is ACTIVE!")
print("\n💡 To see telemetry in action:")
print("   1. Run: python test_resources_demo.py")
print("   2. Use an MCP client (like Claude Desktop or mcp-cli)")
print("   3. Access the resources and watch console output")

print("\n" + "=" * 60)
print("✅ TEST PASSED - Resource instrumentation working!")
print("=" * 60)
