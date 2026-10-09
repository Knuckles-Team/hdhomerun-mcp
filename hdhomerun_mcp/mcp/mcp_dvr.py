import json

from agent_connector_sdk.mcp.action_dispatch import resolve_action
from agent_connector_sdk.mcp.concurrency import run_blocking
from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from .. import kg_ingest
from ..auth import get_client

ACTIONS = {
    "list_rules",
    "add_series_rule",
    "add_datetime_rule",
    "change_rule",
    "delete_rule",
    "record_engine_status",
    "recorded_files",
    "poke",
    "delete_recording",
    "live_tv_url",
    "ingest_rules",
}


async def _list_recording_rules(client, kwargs: dict) -> dict:
    return {"rules": await run_blocking(client.list_recording_rules, **kwargs)}


async def _add_series_rule(client, kwargs: dict) -> dict:
    return {"rules": await run_blocking(client.add_series_rule, **kwargs)}


async def _add_datetime_rule(client, kwargs: dict) -> dict:
    return {"rules": await run_blocking(client.add_datetime_rule, **kwargs)}


async def _change_rule(client, kwargs: dict) -> dict:
    return {"rules": await run_blocking(client.change_rule, **kwargs)}


async def _delete_rule(client, kwargs: dict) -> dict:
    return {"rules": await run_blocking(client.delete_rule, **kwargs)}


async def _record_engine_status(client, kwargs: dict) -> dict:
    return await run_blocking(client.get_record_engine_status, **kwargs)


async def _recorded_files(client, kwargs: dict) -> dict:
    return {"files": await run_blocking(client.get_recorded_files, **kwargs)}


async def _poke_record_engine(client, kwargs: dict) -> dict:
    client.poke_record_engine(**kwargs)
    return {"status": "poked"}


async def _delete_recording(client, kwargs: dict) -> dict:
    client.delete_recording(**kwargs)
    return {"status": "deleted"}


async def _live_tv_url(client, kwargs: dict) -> dict:
    return {"url": client.build_live_tv_url(**kwargs)}


async def _ingest_recording_rules(client, kwargs: dict) -> dict:
    rules = await run_blocking(client.list_recording_rules, **kwargs)
    return {"ingested": await kg_ingest.ingest_recording_rules(rules)}


# Action name -> handler. Keeps `dvr_operations` itself to a single
# lookup-and-call instead of an N-way if/elif chain over `action`.
DVR_ACTION_HANDLERS = {
    "list_rules": _list_recording_rules,
    "add_series_rule": _add_series_rule,
    "add_datetime_rule": _add_datetime_rule,
    "change_rule": _change_rule,
    "delete_rule": _delete_rule,
    "record_engine_status": _record_engine_status,
    "recorded_files": _recorded_files,
    "poke": _poke_record_engine,
    "delete_recording": _delete_recording,
    "live_tv_url": _live_tv_url,
    "ingest_rules": _ingest_recording_rules,
}


def register_dvr_tools(mcp: FastMCP):
    """Register dvr tag dynamic tools."""

    @mcp.tool(tags={"dvr"})
    async def dvr_operations(
        action: str = Field(
            description="Action to perform. Must be one of: 'list_rules', "
            "'add_series_rule', 'add_datetime_rule', 'change_rule', "
            "'delete_rule', 'record_engine_status', 'recorded_files', 'poke', "
            "'delete_recording', 'live_tv_url', 'ingest_rules'."
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters. Rule actions: {device_auth?, "
            "series_id, channel_only?, team_only?, recent_only?, "
            "after_original_airdate_only?, start_padding?, end_padding?, "
            "date_time_only?, recording_rule_id?, after_recording_rule_id?}. "
            "record_engine_status/poke: {storage_engine_base_url}. "
            "recorded_files: {storage_url}. delete_recording: {cmd_url, "
            "rerecord?}. live_tv_url: {storage_engine_base_url, channel, "
            "client_id, session_id}. ingest_rules: {device_auth?} (fetches "
            "and pushes into the knowledge graph).",
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> dict:
        """Manage the SiliconDust cloud DVR recording-rules API and the local
        record-engine API (recordings list, poke, delete, buffered Live TV).
        CONCEPT:HDHR-dvr.cloud.recording-rules"""
        if ctx:
            await ctx.info("Executing dvr tool...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        resolved = resolve_action(action, ACTIONS, service="hdhomerun-mcp")
        if isinstance(resolved, dict):
            return resolved
        action = resolved

        handler = DVR_ACTION_HANDLERS.get(action)
        if handler is None:
            return {"error": f"Unhandled action: {action}"}
        return await handler(client, kwargs)
