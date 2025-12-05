"""Test client to interact with the MCP server and trigger resource operations."""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_resources():
    """Test resource operations."""
    
    # Connect to the server
    server_params = StdioServerParameters(
        command="python",
        args=["test_resources_demo.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("✅ Connected to MCP server\n")
            
            # Test 1: List available resources
            print("📋 Test 1: Listing resources...")
            resources = await session.list_resources()
            print(f"   Found {len(resources.resources)} resources:")
            for resource in resources.resources:
                print(f"   - {resource.uri}: {resource.name}")
            print()
            
            # Test 2: Read a static resource
            print("📖 Test 2: Reading config://settings...")
            result = await session.read_resource("config://settings")
            print(f"   Result: {result.contents[0].text if result.contents else 'No content'}")
            print()
            
            # Test 3: Read a parameterized resource
            print("📖 Test 3: Reading data://users/123...")
            result = await session.read_resource("data://users/123")
            print(f"   Result: {result.contents[0].text if result.contents else 'No content'}")
            print()
            
            # Test 4: Call a tool for comparison
            print("🔧 Test 4: Calling greet tool...")
            tool_result = await session.call_tool("greet", {"name": "Alice"})
            print(f"   Result: {tool_result.content[0].text if tool_result.content else 'No content'}")
            print()
            
            print("✅ All tests completed!")
            print("\n📊 Check the console output above for telemetry data")

if __name__ == "__main__":
    asyncio.run(test_resources())
