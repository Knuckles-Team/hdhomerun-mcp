"""Native epistemic-graph ingestion for HDHomeRun MCP records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The package natively pushes
its OWN data into the ONE engine, in every modality that applies (the
"maximum ingestion" bar): typed OWL nodes (:DiscoveredDevice/:Lineup/
:Channel/:RecordingRule), documents (:Document), and raw blobs
(:Blob/:MediaAsset). Thin mapper over the ``agent_connector_sdk.ingest``
knowledge-ingest facade — every entry point here is best-effort and
dependency-guarded: no reachable engine, no entities to write, or an engine
rejection all no-op (return ``None``, never raise). Node ids:
``hdhomerun:<class>:<id>``; ``node_type`` values match ``ontology/hdhomerun.ttl``.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_connector_sdk.ingest import (
    ChangeSet,
    Document,
    Entity,
    IngestBinding,
    IngestError,
    IngestUnavailableError,
    KnowledgeIngest,
    MediaAsset,
    Relationship,
    current_ingest,
)

logger = logging.getLogger("hdhomerun_mcp.kg")

_SOURCE = "hdhomerun-mcp"
_DOMAIN = "hdhomerun"
_BINDING = IngestBinding(connector=_SOURCE, stream=_DOMAIN)


def _to_entity(record: dict[str, Any]) -> Entity:
    return Entity(
        id=record.get("id"),
        node_type=record.get("node_type"),
        properties={k: v for k, v in record.items() if k not in ("id", "node_type")},
    )


def _to_relationship(record: dict[str, Any]) -> Relationship:
    properties = {
        k: v for k, v in record.items() if k not in ("source", "target", "relationship")
    }
    return Relationship(
        source=record["source"],
        target=record["target"],
        relationship=record["relationship"],
        properties=properties or None,
    )


async def _service(ingest: KnowledgeIngest | None) -> KnowledgeIngest | None:
    if ingest is not None:
        return ingest
    try:
        return current_ingest()
    except IngestUnavailableError as e:
        logger.debug("native ingest unavailable: %s", type(e).__name__)
        return None


async def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int] | None:
    """Write typed nodes (+ edges) into epistemic-graph. Best-effort; never raises."""
    if not entities:
        return None
    service = await _service(ingest)
    if service is None:
        return None
    change_set = ChangeSet(
        entities=tuple(_to_entity(e) for e in entities),
        relationships=tuple(_to_relationship(r) for r in relationships or ()),
    )
    try:
        receipt = await service.submit(_BINDING, change_set)
    except IngestError as e:  # noqa: BLE001 — engine/transport failure is non-fatal
        logger.warning("native ingest failed: %s", type(e).__name__)
        return None
    return {"nodes": receipt.affected_count, "edges": receipt.relationship_count}


async def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int] | None:
    """Push text records ({id,text,title?,source_uri?}) as :Document nodes."""
    documents = [
        Document(
            id=d["id"],
            text=d["text"],
            title=d.get("title"),
            source_uri=d.get("source_uri"),
        )
        for d in docs or []
        if d.get("id") and d.get("text")
    ]
    if not documents:
        return None
    service = await _service(ingest)
    if service is None:
        return None
    change_set = ChangeSet(documents=tuple(documents))
    try:
        receipt = await service.submit(_BINDING, change_set)
    except IngestError as e:  # noqa: BLE001 — engine/transport failure is non-fatal
        logger.warning("native ingest failed: %s", type(e).__name__)
        return None
    return {"nodes": receipt.affected_count, "edges": receipt.relationship_count}


async def ingest_device(
    info: dict[str, Any], *, ingest: KnowledgeIngest | None = None
) -> dict[str, int] | None:
    """Map a ``discover.json`` payload -> a :DiscoveredDevice node."""
    device_id = info.get("DeviceID")
    if not device_id:
        return None
    entity = {
        "id": f"{_DOMAIN}:device:{device_id}",
        "node_type": "DiscoveredDevice",
        "name": info.get("FriendlyName"),
        "deviceId": device_id,
        "tunerCount": info.get("TunerCount"),
        "modelNumber": info.get("ModelNumber"),
        "firmwareVersion": info.get("FirmwareVersion"),
    }
    return await ingest_entities([entity], [], ingest=ingest)


async def ingest_lineup(
    device_id: str,
    channels: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int] | None:
    """Map a device's ``lineup.json`` -> a :Lineup node + :Channel nodes + edges."""
    lineup_id = f"{_DOMAIN}:lineup:{device_id}"
    entities: list[dict[str, Any]] = [
        # A minimal stub so the hasLineup edge's source node_type resolves even when
        # ingest_device() was never called in this change set; the engine merges it
        # with any fuller :DiscoveredDevice node already on record.
        {"id": f"{_DOMAIN}:device:{device_id}", "node_type": "DiscoveredDevice"},
        {"id": lineup_id, "node_type": "Lineup", "name": f"Lineup for {device_id}"},
    ]
    relationships: list[dict[str, Any]] = [
        {
            "source": f"{_DOMAIN}:device:{device_id}",
            "target": lineup_id,
            "relationship": "hasLineup",
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
                "node_type": "Channel",
                "name": chan.get("GuideName"),
                "guideNumber": guide_number,
                "guideName": chan.get("GuideName"),
            }
        )
        relationships.append(
            {
                "source": lineup_id,
                "target": channel_id,
                "relationship": "includesChannel",
            }
        )
    return await ingest_entities(entities, relationships, ingest=ingest)


async def ingest_recording_rules(
    rules: list[dict[str, Any]], *, ingest: KnowledgeIngest | None = None
) -> dict[str, int] | None:
    """Map DVR ``recording_rules`` entries -> :RecordingRule nodes."""
    entities = []
    for rule in rules or []:
        rule_id = rule.get("RecordingRuleID")
        if not rule_id:
            continue
        entities.append(
            {
                "id": f"{_DOMAIN}:rule:{rule_id}",
                "node_type": "RecordingRule",
                "name": rule.get("Title"),
                "seriesId": rule.get("SeriesID"),
            }
        )
    return await ingest_entities(entities, [], ingest=ingest)


async def ingest_blob(
    data: bytes,
    *,
    name: str = "",
    mime_type: str = "",
    media_type: str = "file",
    extra: dict[str, Any] | None = None,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, Any] | None:
    """Store raw bytes (a recorded stream segment/attachment) as a :MediaAsset."""
    if not data:
        return None
    service = await _service(ingest)
    if service is None:
        return None
    properties = dict(extra or {})
    properties["media_type"] = media_type
    properties["source"] = _SOURCE
    asset = MediaAsset(data=data, mime_type=mime_type, name=name, properties=properties)
    change_set = ChangeSet(media=(asset,))
    try:
        await service.submit(_BINDING, change_set)
    except IngestError as e:  # noqa: BLE001 — engine/transport failure is non-fatal
        logger.warning("native media ingest failed: %s", type(e).__name__)
        return None
    import hashlib

    digest = hashlib.sha256(data).hexdigest()
    return {"asset_id": asset.id or f"blob:{digest}", "digest": digest}
