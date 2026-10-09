"""Native epistemic-graph ingestion — Wire-First coverage (fake SDK transport; no
engine). CONCEPT:HDHR-kg.ingest.native-push"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import KnowledgeIngest

from hdhomerun_mcp import kg_ingest


class _FakeTransport:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector: str, stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: Any) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data: bytes) -> str:
        raise AssertionError("not exercised by the typed-node tests")


@pytest.fixture
def ingest():
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


def _entities(transport: _FakeTransport) -> dict[str, dict[str, Any]]:
    return {r.record_id: dict(r.payload) for r in transport.requests[-1].records}


def _edges(transport: _FakeTransport) -> dict[tuple[str, str], str]:
    return {
        (r.source.record_id, r.target.record_id): r.relation_reference.rsplit("/", 1)[-1]
        for r in transport.requests[-1].relationships
    }


@pytest.mark.asyncio
@pytest.mark.concept("HDHR-kg.ingest.native-push")
async def test_ingest_device_maps_and_pushes(ingest):
    """A discover.json payload maps to a :DiscoveredDevice node. CONCEPT:HDHR-kg.ingest.native-push"""
    service, transport = ingest
    res = await kg_ingest.ingest_device(
        {"DeviceID": "10ACFCDE", "TunerCount": 4}, ingest=service
    )
    assert res == {"nodes": 1, "edges": 0}
    entities = _entities(transport)
    assert "hdhomerun:device:10ACFCDE" in entities
    assert entities["hdhomerun:device:10ACFCDE"]["deviceId"] == "10ACFCDE"


@pytest.mark.asyncio
@pytest.mark.concept("HDHR-kg.ingest.native-push")
async def test_ingest_lineup_maps_channels_and_edges(ingest):
    """A lineup maps to a :Lineup node + :Channel nodes + includesChannel edges. CONCEPT:HDHR-kg.ingest.native-push"""
    service, transport = ingest
    channels = [{"GuideNumber": "24.1", "GuideName": "KVUE-DT"}]
    res = await kg_ingest.ingest_lineup("10ACFCDE", channels, ingest=service)
    assert res == {"nodes": 3, "edges": 2}
    assert "hdhomerun:lineup:10ACFCDE" in _entities(transport)
    assert "hdhomerun:channel:10ACFCDE:24.1" in _entities(transport)
    edges = _edges(transport)
    assert edges[("hdhomerun:device:10ACFCDE", "hdhomerun:lineup:10ACFCDE")] == "hasLineup"
    assert (
        edges[("hdhomerun:lineup:10ACFCDE", "hdhomerun:channel:10ACFCDE:24.1")]
        == "includesChannel"
    )


@pytest.mark.asyncio
@pytest.mark.concept("HDHR-kg.ingest.native-push")
async def test_ingest_recording_rules_maps(ingest):
    """Recording rules map to :RecordingRule nodes. CONCEPT:HDHR-kg.ingest.native-push"""
    service, transport = ingest
    res = await kg_ingest.ingest_recording_rules(
        [{"RecordingRuleID": "403922", "Title": "Skyfall", "SeriesID": "11579711"}],
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 0}
    assert "hdhomerun:rule:403922" in _entities(transport)


@pytest.mark.asyncio
@pytest.mark.concept("HDHR-kg.ingest.native-push")
async def test_ingest_noops_without_engine():
    """Every ingest function is a clean no-op with no reachable engine. CONCEPT:HDHR-kg.ingest.native-push"""
    assert await kg_ingest.ingest_device({"DeviceID": "x"}) is None
    assert await kg_ingest.ingest_lineup("x", []) is None
    assert await kg_ingest.ingest_recording_rules([]) is None
    assert await kg_ingest.ingest_documents([]) is None
    assert await kg_ingest.ingest_blob(b"data") is None
