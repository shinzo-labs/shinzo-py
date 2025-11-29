from mcp.server.fastmcp import FastMCP
from shinzo.instrumentation import instrument_server

server = FastMCP("repro-server")

from shinzo.instrumentation import instrument_server

config = {
    "enable": True,
    "server_name": "shinzo-repro",
    "server_version": "0.1.0"
}

observability = instrument_server(server, config)



@server.tool(description="Returns greeting")
def hello(name: str):
    return f"Hello, {name}!"

if __name__ == "__main__":
    server.run()