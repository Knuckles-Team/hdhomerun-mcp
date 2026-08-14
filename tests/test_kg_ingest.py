"""Native epistemic-graph ingestion — Wire-First coverage (fakes; no engine).
CONCEPT:HDHR-kg.ingest.native-push"""

from __future__ import annotations

from typing import Any

import pytest

from hdhomerun_mcp import kg_ingest


class _FakeNI:
    def __init__(self) -> None:
        self.entities: list[dict[str, Any]] = []
        self.relationships: list[dict[str, Any]] = []

    def ingest_entities(self, entities, relationships, *, source, domain):
        self.entities = entities
        self.relationships = relationships or []
        self.last_call = {"source": source, "domain": domain}
        return {"nodes": len(entities), "edges": len(relationships or [])}

    def ingest_documents(self, docs, *, source, domain):
        self.last_call = {"source": source, "domain": domain}
        return {"nodes": len(docs), "edges": 0}

    def media_store(self):
        return None


@pytest.mark.concept("HDHR-kg.ingest.native-push")
def test_ingest_device_maps_and_pushes(monkeypatch):
    """A discover.json payload maps to a :DiscoveredDevice node. CONCEPT:HDHR-kg.ingest.native-push"""
    fake = _FakeNI()
    monkeypatch.setattr(kg_ingest, "_primitive", lambda: fake)
    res = kg_ingest.ingest_device({"DeviceID": "10ACFCDE", "TunerCount": 4})
    assert res == {"nodes": 1, "edges": 0}
    assert fake.entities[0]["id"] == "hdhomerun:device:10ACFCDE"
    assert fake.entities[0]["node_type"] == "DiscoveredDevice"


@pytest.mark.concept("HDHR-kg.ingest.native-push")
def test_ingest_lineup_maps_channels_and_edges(monkeypatch):
    """A lineup maps to a :Lineup node + :Channel nodes + includesChannel edges. CONCEPT:HDHR-kg.ingest.native-push"""
    fake = _FakeNI()
    monkeypatch.setattr(kg_ingest, "_primitive", lambda: fake)
    channels = [{"GuideNumber": "24.1", "GuideName": "KVUE-DT"}]
    res = kg_ingest.ingest_lineup("10ACFCDE", channels)
    assert res == {"nodes": 2, "edges": 2}
    types = {e["id"]: e["node_type"] for e in fake.entities}
    assert types["hdhomerun:lineup:10ACFCDE"] == "Lineup"
    assert types["hdhomerun:channel:10ACFCDE:24.1"] == "Channel"
    rel_types = {(r["source"], r["target"]): r["relationship"] for r in fake.relationships}
    assert rel_types[("hdhomerun:device:10ACFCDE", "hdhomerun:lineup:10ACFCDE")] == "hasLineup"
    assert (
        rel_types[("hdhomerun:lineup:10ACFCDE", "hdhomerun:channel:10ACFCDE:24.1")]
        == "includesChannel"
    )


@pytest.mark.concept("HDHR-kg.ingest.native-push")
def test_ingest_recording_rules_maps(monkeypatch):
    """Recording rules map to :RecordingRule nodes. CONCEPT:HDHR-kg.ingest.native-push"""
    fake = _FakeNI()
    monkeypatch.setattr(kg_ingest, "_primitive", lambda: fake)
    res = kg_ingest.ingest_recording_rules(
        [{"RecordingRuleID": "403922", "Title": "Skyfall", "SeriesID": "11579711"}]
    )
    assert res == {"nodes": 1, "edges": 0}
    assert fake.entities[0]["id"] == "hdhomerun:rule:403922"


@pytest.mark.concept("HDHR-kg.ingest.native-push")
def test_ingest_noops_without_engine(monkeypatch):
    """Every ingest function is a clean no-op with no reachable engine. CONCEPT:HDHR-kg.ingest.native-push"""
    monkeypatch.setattr(kg_ingest, "_primitive", lambda: None)
    assert kg_ingest.ingest_device({"DeviceID": "x"}) is None
    assert kg_ingest.ingest_lineup("x", []) is None
    assert kg_ingest.ingest_recording_rules([]) is None
    assert kg_ingest.ingest_documents([]) is None
    assert kg_ingest.ingest_blob(b"data") is None
