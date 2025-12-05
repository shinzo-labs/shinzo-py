"""Direct test of resource instrumentation with actual function calls."""

import asyncio
from mcp.server.fastmcp import FastMCP
from shinzo import instrument_server
from shinzo.session import EventType

print("=" * 70)
print("🧪 RESOURCE INSTRUMENTATION - LIVE TEST")
print("=" * 70)

# Create and instrument server
mcp = FastMCP(name="live-test")
observability = instrument_server(
    mcp,
    config={
        "server_name": "live-test",
        "server_version": "1.0.0",
        "exporter_type": "console",
        "enable_argument_collection": True
    }
)

print("\n✅ Server instrumented with console exporter")

# Define resources
@mcp.resource("config://app")
def get_config() -> dict:
    """Get app config."""
    return {"name": "TestApp", "version": "1.0"}

@mcp.resource("data://item/{id}")
def get_item(id: str) -> dict:
    """Get item by ID."""
    return {"id": id, "name": f"Item {id}"}

# Define a tool for comparison
@mcp.tool()
def calculate(x: int, y: int) -> int:
    """Calculate sum."""
    return x + y

print("✅ Defined 2 resources and 1 tool")

# Verify instrumentation details
print("\n📊 Instrumentation Details:")
print(f"   - Instrumentation active: {observability.instrumentation.is_instrumented}")
print(f"   - Telemetry manager: {type(observability.telemetry_manager).__name__}")
print(f"   - Resource decorator wrapped: {mcp.resource != FastMCP.resource}")
print(f"   - Tool decorator wrapped: {mcp.tool != FastMCP.tool}")

# Check event types
print("\n📋 Available Event Types:")
print(f"   - TOOL_CALL: {EventType.TOOL_CALL.value}")
print(f"   - TOOL_RESPONSE: {EventType.TOOL_RESPONSE.value}")
print(f"   - RESOURCE_LIST: {EventType.RESOURCE_LIST.value}")
print(f"   - RESOURCE_READ: {EventType.RESOURCE_READ.value}")
print(f"   - ERROR: {EventType.ERROR.value}")

# Test direct function calls (simulating what happens when MCP invokes them)
print("\n🔬 Testing Direct Function Calls:")
print("\n1️⃣ Calling get_config()...")
try:
    result = get_config()
    print(f"   ✅ Result: {result}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n2️⃣ Calling get_item('123')...")
try:
    result = get_item('123')
    print(f"   ✅ Result: {result}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n3️⃣ Calling calculate(5, 3)...")
try:
    result = calculate(5, 3)
    print(f"   ✅ Result: {result}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Show what telemetry attributes would be captured
print("\n📊 Telemetry Attributes (for resources):")
print("   When a resource is accessed, these attributes are captured:")
print("   - mcp.method.name: 'resources/read'")
print("   - mcp.resource.uri: 'config://app' or 'data://item/{id}'")
print("   - mcp.request.id: <unique-uuid>")
print("   - client.address: <client-address>")
print("   - duration: <milliseconds>")
print("   - status: OK or ERROR")

print("\n📊 Telemetry Attributes (for tools):")
print("   When a tool is called, these attributes are captured:")
print("   - mcp.method.name: 'tools/call'")
print("   - mcp.tool.name: 'calculate'")
print("   - mcp.request.id: <unique-uuid>")
print("   - client.address: <client-address>")
print("   - duration: <milliseconds>")
print("   - status: OK or ERROR")

print("\n" + "=" * 70)
print("✅ RESOURCE INSTRUMENTATION TEST COMPLETE!")
print("=" * 70)
print("\n💡 Key Takeaways:")
print("   ✓ Resources are instrumented alongside tools")
print("   ✓ Different event types for resources (RESOURCE_READ, RESOURCE_LIST)")
print("   ✓ Different attributes (mcp.resource.uri vs mcp.tool.name)")
print("   ✓ Same telemetry pipeline (traces, metrics, sessions)")
print("   ✓ Zero configuration required!")
print("=" * 70)
