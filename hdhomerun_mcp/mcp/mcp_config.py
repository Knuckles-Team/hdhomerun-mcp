import json

from agent_utilities.mcp_utilities import resolve_action, run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from ..auth import get_client

ACTIONS = {
    "get_item",
    "set_item",
    "help",
    "tuner_status",
    "tuner_vstatus",
    "tuner_streaminfo",
    "tuner_debug",
    "get_channel",
    "set_channel",
    "stop_tuner",
    "get_channelmap",
    "set_channelmap",
    "get_filter",
    "set_filter",
    "get_program",
    "set_program",
    "get_target",
    "set_target",
    "get_lockkey",
    "set_lockkey",
    "get_ir_target",
    "set_ir_target",
    "set_lineup_location",
    "disable_lineup_location",
    "sys_model",
    "sys_features",
    "sys_version",
    "sys_copyright",
    "sys_debug",
    "restart",
}


def register_config_tools(mcp: FastMCP):
    """Register config tag dynamic tools."""

    @mcp.tool(tags={"config"})
    async def config_operations(
        action: str = Field(
            description="Action to perform (mirrors the hdhomerun_config CLI's "
            "get/set item paths). One of: 'get_item', 'set_item', 'help', "
            "'tuner_status', 'tuner_vstatus', 'tuner_streaminfo', 'tuner_debug', "
            "'get_channel', 'set_channel', 'stop_tuner', 'get_channelmap', "
            "'set_channelmap', 'get_filter', 'set_filter', 'get_program', "
            "'set_program', 'get_target', 'set_target', 'get_lockkey', "
            "'set_lockkey', 'get_ir_target', 'set_ir_target', "
            "'set_lineup_location', 'disable_lineup_location', 'sys_model', "
            "'sys_features', 'sys_version', 'sys_copyright', 'sys_debug', 'restart'."
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters. Tuner-scoped actions take "
            "{tuner}. get_item/set_item take {name, value?, lockkey?}. "
            "set_channel: {tuner, modulation, freq_or_channel}. set_channelmap: "
            "{tuner, channelmap}. set_filter: {tuner, pid_filter}. set_program: "
            "{tuner, program_number}. set_target: {tuner, target}. set_lockkey: "
            "{tuner, lock, lockkey?}. set_ir_target: {target}. "
            "set_lineup_location: {country_code, postal_code}.",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Query/control a tuner via the binary hdhomerun_config TCP control
        protocol (port 65001) — a DIFFERENT wire protocol from the HTTP JSON
        API: tuner status/vstatus/streaminfo/debug, channel/channelmap/filter/
        program/target tuning, IR target, lineup location, and /sys/* info.
        Supported items are device/firmware-dependent — call 'help' first.
        CONCEPT:HDHR-config.protocol.tuner-control"""
        if ctx:
            await ctx.info("Executing config tool...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, ACTIONS, service="hdhomerun-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        method_map = {
            "get_item": client.get_item,
            "set_item": client.set_item,
            "help": client.get_help,
            "tuner_status": client.get_tuner_status,
            "tuner_vstatus": client.get_tuner_vstatus,
            "tuner_streaminfo": client.get_tuner_streaminfo,
            "tuner_debug": client.get_tuner_debug,
            "get_channel": client.get_channel,
            "set_channel": client.set_channel,
            "stop_tuner": client.stop_tuner,
            "get_channelmap": client.get_channelmap,
            "set_channelmap": client.set_channelmap,
            "get_filter": client.get_filter,
            "set_filter": client.set_filter,
            "get_program": client.get_program,
            "set_program": client.set_program,
            "get_target": client.get_target,
            "set_target": client.set_target,
            "get_lockkey": client.get_lockkey,
            "set_lockkey": client.set_lockkey,
            "get_ir_target": client.get_ir_target,
            "set_ir_target": client.set_ir_target,
            "set_lineup_location": client.set_lineup_location,
            "disable_lineup_location": client.disable_lineup_location,
            "sys_model": client.get_sys_model,
            "sys_features": client.get_sys_features,
            "sys_version": client.get_sys_version,
            "sys_copyright": client.get_sys_copyright,
            "sys_debug": client.get_sys_debug,
            "restart": client.restart_device,
        }
        method = method_map.get(action)
        if method is None:
            return {"error": f"Unhandled action: {action}"}
        result = await run_blocking(method, **kwargs)
        return {"value": result}
