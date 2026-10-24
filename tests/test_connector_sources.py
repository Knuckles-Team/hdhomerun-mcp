"""The declared recording-rules source matches the shape the served tool returns."""

from __future__ import annotations

import pytest

from hdhomerun_mcp.connector_sources import declaration


@pytest.mark.spec("CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R002")
def test_recording_rules_source_reads_the_served_tool_result_list() -> None:
    source = next(s for s in declaration().sources if s.source_id == "hdhomerun-recording-rules")
    assert source.tools == ("hdhomerun_list_recording_rules",)
    assert source.records_path == ""
    assert source.id_field == "RecordingRuleID"
