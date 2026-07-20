import json

from agent_utilities.mcp_utilities import resolve_action, run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..api.api_client_discovery import read_discovery_cache
from ..auth import get_client

ACTIONS = {"broadcast", "targeted", "cloud", "cache"}


def register_discovery_tools(mcp: FastMCP):
    """Register discovery tag dynamic tools."""

    @mcp.tool(tags={"discovery"})
    async def discovery_operations(
        action: str = Field(
            description="Action to perform. Must be one of: "
            "'broadcast', 'targeted', 'cloud', 'cache'."
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters. broadcast: {timeout?, "
            "device_id?}. targeted: {ip, timeout?, device_id?}. cloud: "
            "{device_id?}. cache: {}.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Discover HDHomeRun devices on the network — local UDP broadcast
        (port 65001, may not cross VLANs), targeted UDP to a known IP, or the
        SiliconDust cloud discovery endpoint. CONCEPT:HDHR-discovery.network.device-location"""
        if ctx:
            await ctx.info("Executing discovery tool...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, ACTIONS, service="hdhomerun-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        if action == "broadcast":
            devices = await run_blocking(client.discover_local_broadcast, **kwargs)
            return {"devices": devices}
        if action == "targeted":
            device = await run_blocking(client.discover_local_targeted, **kwargs)
            return {"device": device}
        if action == "cloud":
            devices = await run_blocking(client.discover_cloud, **kwargs)
            return {"devices": devices}
        if action == "cache":
            return {"cache": read_discovery_cache()}
        return {"error": f"Unhandled action: {action}"}
