from mcp.server.fastmcp import FastMCP
import httpx

# Initialize FastMCP
mcp = FastMCP("SahamSignalServer")

@mcp.tool()
async def get_latest_signals():
    """Fetches the latest stock signals from the local server."""
    async with httpx.AsyncClient() as client:
        try:
            # Mapping /api/signals to /api/latest as /api/latest provides the most recent signals
            response = await client.get("http://127.0.0.1:5000/api/latest")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
