import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["repro.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            print(f"Tools: {[t.name for t in tools.tools]}")
            
            # Call tool
            result = await session.call_tool("hello", arguments={"name": "Aadity"})
            print(f"Result: {result.content[0].text}")
            
            assert result.content[0].text == "Hello, World!"

if __name__ == "__main__":
    try:
        asyncio.run(run())
        print("Verification SUCCESS")
    except Exception as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)
