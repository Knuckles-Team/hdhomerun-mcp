"""The discovery cache read, which is not a client-method wrapper.

Every other HDHomeRun operation is served by the SDK as one typed tool per client
method; this tool reads the on-disk discovery cache the doctor checks.
"""

from fastmcp import Context, FastMCP
from pydantic import Field

from ..api.api_client_discovery import read_discovery_cache


def register_discovery_tools(mcp: FastMCP):
    """Register the discovery cache tool."""

    @mcp.tool(tags={"discovery"})
    async def hdhomerun_read_discovery_cache(
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Read the on-disk cache of the last device discovery.

        CONCEPT:HDHR-discovery.network.device-location
        """
        if ctx:
            await ctx.info("Reading the discovery cache...")
        return {"cache": read_discovery_cache()}
