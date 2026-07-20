import json

from agent_utilities.mcp_utilities import resolve_action, run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client

ACTIONS = {
    "run",
    "device_reachable",
    "firmware_model",
    "tuner_count_vs_jellyfin",
    "signal_strength",
    "device_auth",
    "cache_freshness",
}


def register_doctor_tools(mcp: FastMCP):
    """Register doctor tag dynamic tools."""

    @mcp.tool(tags={"doctor"})
    async def doctor_operations(
        action: str = Field(
            default="run",
            description="Diagnostic action. 'run' executes the full suite "
            "(recommended); or run a single check: 'device_reachable', "
            "'firmware_model', 'tuner_count_vs_jellyfin', 'signal_strength', "
            "'device_auth', 'cache_freshness'.",
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters. 'run'/'tuner_count_vs_jellyfin': "
            "{jellyfin_url?, jellyfin_api_key?}. 'run'/'signal_strength': "
            "{signal_channels?: [str]}. 'device_auth': {validate_cloud?: bool}.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Diagnose an HDHomeRun deployment: device reachability, firmware/model,
        tuner count vs a paired Jellyfin TunerHost, per-channel signal strength,
        DeviceAuth presence/validity, and discovery-cache freshness — each
        check reports pass/fail/warn/skip with an actionable next step on
        failure. CONCEPT:HDHR-doctor.diagnostics.health-report"""
        if ctx:
            await ctx.info("Running doctor diagnostics...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, ACTIONS, service="hdhomerun-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        if action == "run":
            return await run_blocking(client.run_doctor, **kwargs)
        if action == "device_reachable":
            return await run_blocking(client.check_device_reachable, **kwargs)
        if action == "firmware_model":
            return await run_blocking(client.check_firmware_model, **kwargs)
        if action == "tuner_count_vs_jellyfin":
            return await run_blocking(client.check_tuner_count_vs_jellyfin, **kwargs)
        if action == "signal_strength":
            return await run_blocking(client.check_signal_strength, **kwargs)
        if action == "device_auth":
            return await run_blocking(client.check_device_auth, **kwargs)
        if action == "cache_freshness":
            return await run_blocking(client.check_discovery_cache_freshness, **kwargs)
        return {"error": f"Unhandled action: {action}"}
