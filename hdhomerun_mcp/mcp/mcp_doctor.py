import json

from agent_utilities.mcp.action_dispatch import resolve_action
from agent_utilities.mcp.concurrency import run_blocking
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


async def _run_full_diagnostics(client, kwargs: dict) -> dict:
    return await run_blocking(client.run_doctor, **kwargs)


async def _check_device_reachable(client, kwargs: dict) -> dict:
    return await run_blocking(client.check_device_reachable, **kwargs)


async def _check_firmware_model(client, kwargs: dict) -> dict:
    return await run_blocking(client.check_firmware_model, **kwargs)


async def _check_tuner_count_vs_jellyfin(client, kwargs: dict) -> dict:
    return await run_blocking(client.check_tuner_count_vs_jellyfin, **kwargs)


async def _check_signal_strength(client, kwargs: dict) -> dict:
    return await run_blocking(client.check_signal_strength, **kwargs)


async def _check_device_auth(client, kwargs: dict) -> dict:
    return await run_blocking(client.check_device_auth, **kwargs)


async def _check_cache_freshness(client, kwargs: dict) -> dict:
    return await run_blocking(client.check_discovery_cache_freshness, **kwargs)


# Action name -> handler. Keeps `doctor_operations` itself to a single
# lookup-and-call instead of an N-way if/elif chain over `action`.
DOCTOR_ACTION_HANDLERS = {
    "run": _run_full_diagnostics,
    "device_reachable": _check_device_reachable,
    "firmware_model": _check_firmware_model,
    "tuner_count_vs_jellyfin": _check_tuner_count_vs_jellyfin,
    "signal_strength": _check_signal_strength,
    "device_auth": _check_device_auth,
    "cache_freshness": _check_cache_freshness,
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

        handler = DOCTOR_ACTION_HANDLERS.get(action)
        if handler is None:
            return {"error": f"Unhandled action: {action}"}
        return await handler(client, kwargs)
