import json

from agent_utilities.mcp_utilities import resolve_action, run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from .. import kg_ingest
from ..auth import get_client

ACTIONS = {
    "discover",
    "lineup",
    "lineup_status",
    "scan_start",
    "scan_abort",
    "stream_url",
    "ingest_device",
    "ingest_lineup",
}


def register_http_tools(mcp: FastMCP):
    """Register http tag dynamic tools."""

    @mcp.tool(tags={"http"})
    async def http_operations(
        action: str = Field(
            description="Action to perform. Must be one of: "
            "'discover', 'lineup', 'lineup_status', 'scan_start', 'scan_abort', "
            "'stream_url'."
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters. lineup: {fmt}. scan_start: "
            "{source?}. stream_url: {channel, tuner?, by_frequency?, program?, "
            "duration?, transcode?}. ingest_device/ingest_lineup: {} (fetches "
            "live and pushes into the knowledge graph; device_id required for "
            "ingest_lineup).",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Query the HDHomeRun device HTTP JSON API — discover.json, channel
        lineup, and scan control. CONCEPT:HDHR-http.api.json-interface"""
        if ctx:
            await ctx.info("Executing http tool...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, ACTIONS, service="hdhomerun-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        if action == "discover":
            return await run_blocking(client.get_discover, **kwargs)
        if action == "lineup":
            return await run_blocking(client.get_lineup, **kwargs)
        if action == "lineup_status":
            return await run_blocking(client.get_lineup_status, **kwargs)
        if action == "scan_start":
            client.start_scan(**kwargs)
            return {"status": "scan started"}
        if action == "scan_abort":
            client.abort_scan()
            return {"status": "scan aborted"}
        if action == "stream_url":
            return {"url": client.build_stream_url(**kwargs)}
        if action == "ingest_device":
            info = await run_blocking(client.get_discover)
            return {"ingested": kg_ingest.ingest_device(info)}
        if action == "ingest_lineup":
            info = await run_blocking(client.get_discover)
            channels = await run_blocking(client.get_lineup)
            return {"ingested": kg_ingest.ingest_lineup(info.get("DeviceID"), channels)}
        return {"error": f"Unhandled action: {action}"}
