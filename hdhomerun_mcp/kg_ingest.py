"""Native epistemic-graph ingestion for HDHomeRun MCP records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The package natively pushes
its OWN data into the ONE engine, in every modality that applies (the
"maximum ingestion" bar): typed OWL nodes (:DiscoveredDevice/:Lineup/
:Channel/:RecordingRule), documents (:Document), and raw blobs
(:Blob/:MediaAsset). Thin mapper over the shared primitive
``agent_utilities.knowledge_graph.memory.native_ingest`` — imported GUARDED so
it no-ops with no KG stack / no reachable engine (never raises). Node ids:
``hdhomerun:<class>:<id>``; ``type`` values match ``ontology/hdhomerun.ttl``.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("hdhomerun_mcp.kg")

_SOURCE = "hdhomerun-mcp"
_DOMAIN = "hdhomerun"


def _primitive():
    """The shared native_ingest module, or None when unavailable."""
    try:
        from agent_utilities.knowledge_graph.memory import native_ingest
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("native ingest unavailable: %s", e)
        return None
    return native_ingest


def ingest_device(info: dict[str, Any]) -> dict[str, int] | None:
    """Map a ``discover.json`` payload -> a :DiscoveredDevice node."""
    ni = _primitive()
    if ni is None:
        return None
    device_id = info.get("DeviceID")
    if not device_id:
        return None
    entity = {
        "id": f"{_DOMAIN}:device:{device_id}",
        "type": "DiscoveredDevice",
        "name": info.get("FriendlyName"),
        "deviceId": device_id,
        "tunerCount": info.get("TunerCount"),
        "modelNumber": info.get("ModelNumber"),
        "firmwareVersion": info.get("FirmwareVersion"),
    }
    return ni.ingest_entities([entity], [], source=_SOURCE, domain=_DOMAIN)


def ingest_lineup(
    device_id: str, channels: list[dict[str, Any]]
) -> dict[str, int] | None:
    """Map a device's ``lineup.json`` -> a :Lineup node + :Channel nodes + edges."""
    ni = _primitive()
    if ni is None:
        return None
    lineup_id = f"{_DOMAIN}:lineup:{device_id}"
    entities: list[dict[str, Any]] = [
        {"id": lineup_id, "type": "Lineup", "name": f"Lineup for {device_id}"}
    ]
    relationships: list[dict[str, Any]] = [
        {
            "source": f"{_DOMAIN}:device:{device_id}",
            "target": lineup_id,
            "type": "hasLineup",
        }
    ]
    for chan in channels or []:
        guide_number = chan.get("GuideNumber")
        if not guide_number:
            continue
        channel_id = f"{_DOMAIN}:channel:{device_id}:{guide_number}"
        entities.append(
            {
                "id": channel_id,
                "type": "Channel",
                "name": chan.get("GuideName"),
                "guideNumber": guide_number,
                "guideName": chan.get("GuideName"),
            }
        )
        relationships.append(
            {"source": lineup_id, "target": channel_id, "type": "includesChannel"}
        )
    return ni.ingest_entities(entities, relationships, source=_SOURCE, domain=_DOMAIN)


def ingest_recording_rules(rules: list[dict[str, Any]]) -> dict[str, int] | None:
    """Map DVR ``recording_rules`` entries -> :RecordingRule nodes."""
    ni = _primitive()
    if ni is None:
        return None
    entities = []
    for rule in rules or []:
        rule_id = rule.get("RecordingRuleID")
        if not rule_id:
            continue
        entities.append(
            {
                "id": f"{_DOMAIN}:rule:{rule_id}",
                "type": "RecordingRule",
                "name": rule.get("Title"),
                "seriesId": rule.get("SeriesID"),
            }
        )
    return ni.ingest_entities(entities, [], source=_SOURCE, domain=_DOMAIN)


def ingest_documents(docs: list[dict[str, Any]]) -> dict[str, int] | None:
    """Push text records ({id,text,title?,source_uri?}) as :Document nodes."""
    ni = _primitive()
    if ni is None:
        return None
    return ni.ingest_documents(docs, source=_SOURCE, domain=_DOMAIN)


def ingest_blob(
    data: bytes,
    *,
    name: str = "",
    mime_type: str = "",
    media_type: str = "file",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Store raw bytes (a recorded stream segment/attachment) as a :Blob + :MediaAsset."""
    ni = _primitive()
    if ni is None:
        return None
    store = ni.media_store()
    if store is None or not data:
        return None
    stored = store.store_media(
        data,
        media_type=media_type,
        mime_type=mime_type,
        source=_SOURCE,
        name=name,
        extra=extra or {},
    )
    return (
        None
        if stored is None
        else {"asset_id": stored.asset_id, "digest": stored.digest}
    )
