"""Knowledge-graph ingest tools, which are not client-method wrappers."""

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field
from scion_sdk.mcp.concurrency import run_blocking

from .. import kg_ingest
from ..auth import get_client


def register_ingest_tools(mcp: FastMCP):
    """Register the three ingest tools."""

    @mcp.tool(tags={"ingest"})
    async def hdhomerun_ingest_device(
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Push the tuner device description into the knowledge graph."""
        if ctx:
            await ctx.info("Ingesting the device...")
        info = await run_blocking(client.get_discover)
        return {"ingested": await kg_ingest.ingest_device(info)}

    @mcp.tool(tags={"ingest"})
    async def hdhomerun_ingest_lineup(
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Push the channel lineup of the tuner device into the knowledge graph."""
        if ctx:
            await ctx.info("Ingesting the lineup...")
        info = await run_blocking(client.get_discover)
        channels = await run_blocking(client.get_lineup)
        return {
            "ingested": await kg_ingest.ingest_lineup(info.get("DeviceID"), channels)
        }

    @mcp.tool(tags={"ingest"})
    async def hdhomerun_ingest_recording_rules(
        device_auth: str | None = Field(
            default=None, description="Device authorization for the cloud DVR."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Fetch the cloud DVR recording rules and push them into the knowledge graph."""
        if ctx:
            await ctx.info("Ingesting the recording rules...")
        kwargs = {} if device_auth is None else {"device_auth": device_auth}
        rules = await run_blocking(client.list_recording_rules, **kwargs)
        return {"ingested": await kg_ingest.ingest_recording_rules(rules)}
