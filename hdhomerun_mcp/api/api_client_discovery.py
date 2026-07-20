"""HDHomeRun Discovery API (https://info.hdhomerun.com/info/discovery_api).

Two independent discovery paths, both implemented here:

1. **Local UDP broadcast** on port 65001 — the wire protocol used internally
   by ``libhdhomerun``'s ``hdhomerun_discover2_find_devices_broadcast()``. Not
   guaranteed to succeed from every host/VLAN (broadcast may not cross subnet
   boundaries/firewalls) — this is expected, not a client bug.
2. **Cloud discovery HTTP endpoint** — ``http://ipv4-api.hdhomerun.com/discover``
   (optionally filtered by ``DeviceID``), which SiliconDust's own apps use when
   local broadcast discovery is unavailable (e.g. across VLANs/VPNs). Confirmed
   live during development: returns
   ``[{"DeviceID","LocalIP","BaseURL","DiscoverURL","LineupURL"}]``.

A lightweight on-disk discovery cache (used by the ``doctor`` domain's
freshness check) is also maintained here.
"""

from __future__ import annotations

import json
import socket
import time
from pathlib import Path
from typing import Any

import requests
from agent_utilities.base_utilities import get_logger

from . import protocol
from .api_client_base import HDHomeRunApiBase

logger = get_logger(__name__)

CLOUD_DISCOVER_URL = "http://ipv4-api.hdhomerun.com/discover"

#: Discovery-cache location: `~/.config/agent-utilities/hdhomerun_discovery_cache.json`.
DISCOVERY_CACHE_PATH = (
    Path.home() / ".config" / "agent-utilities" / "hdhomerun_discovery_cache.json"
)


def _write_cache(devices: list[dict[str, Any]], source: str) -> None:
    DISCOVERY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERY_CACHE_PATH.write_text(
        json.dumps({"ts": time.time(), "source": source, "devices": devices})
    )


def read_discovery_cache() -> dict[str, Any] | None:
    """Read the last-known discovery result, or None if no cache exists."""
    if not DISCOVERY_CACHE_PATH.exists():
        return None
    try:
        return json.loads(DISCOVERY_CACHE_PATH.read_text())
    except (ValueError, OSError):
        return None


class HDHomeRunApiDiscovery(HDHomeRunApiBase):
    """Local UDP broadcast discovery + SiliconDust cloud discovery."""

    def discover_local_broadcast(
        self, timeout: float = 2.0, device_id: int = protocol.DEVICE_ID_WILDCARD
    ) -> list[dict[str, Any]]:
        """Broadcast a DISCOVER_REQ on UDP port 65001 and collect DISCOVER_RPY replies.

        May legitimately return an empty list — broadcast discovery does not
        cross VLAN/subnet boundaries on most networks. Use
        ``discover_cloud()`` or a known IP + ``get_discover()`` as a fallback.
        """
        request = protocol.build_discover_request(device_id)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        devices: list[dict[str, Any]] = []
        try:
            sock.sendto(
                request, ("255.255.255.255", protocol.HDHOMERUN_DISCOVER_UDP_PORT)
            )
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    data, addr = sock.recvfrom(protocol.HDHOMERUN_MAX_PACKET_SIZE)
                except TimeoutError:
                    break
                try:
                    pkt = protocol.parse_packet(data)
                except ValueError:
                    continue
                if pkt.pkt_type != protocol.TYPE_DISCOVER_RPY or not pkt.crc_valid:
                    continue
                devices.append(self._device_from_tags(pkt.tags, addr[0]))
        finally:
            sock.close()
        _write_cache(devices, source="local_broadcast")
        return devices

    def discover_local_targeted(
        self,
        ip: str,
        timeout: float = 2.0,
        device_id: int = protocol.DEVICE_ID_WILDCARD,
    ) -> dict[str, Any] | None:
        """Send a DISCOVER_REQ directly to a known IP (works across VLANs)."""
        request = protocol.build_discover_request(device_id)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            sock.sendto(request, (ip, protocol.HDHOMERUN_DISCOVER_UDP_PORT))
            data, addr = sock.recvfrom(protocol.HDHOMERUN_MAX_PACKET_SIZE)
        except (TimeoutError, OSError):
            return None
        finally:
            sock.close()
        pkt = protocol.parse_packet(data)
        if pkt.pkt_type != protocol.TYPE_DISCOVER_RPY or not pkt.crc_valid:
            return None
        device = self._device_from_tags(pkt.tags, addr[0])
        _write_cache([device], source="local_targeted")
        return device

    @staticmethod
    def _device_from_tags(tags: dict[int, list[bytes]], ip: str) -> dict[str, Any]:
        device: dict[str, Any] = {"ip": ip}
        if protocol.TAG_DEVICE_ID in tags:
            device["device_id"] = tags[protocol.TAG_DEVICE_ID][0].hex().upper()
        if protocol.TAG_TUNER_COUNT in tags:
            device["tuner_count"] = int.from_bytes(
                tags[protocol.TAG_TUNER_COUNT][0], "big"
            )
        if protocol.TAG_BASE_URL in tags:
            device["base_url"] = protocol.cstr(tags[protocol.TAG_BASE_URL][0])
        if protocol.TAG_LINEUP_URL in tags:
            device["lineup_url"] = protocol.cstr(tags[protocol.TAG_LINEUP_URL][0])
        if protocol.TAG_STORAGE_URL in tags:
            device["storage_url"] = protocol.cstr(tags[protocol.TAG_STORAGE_URL][0])
        if protocol.TAG_DEVICE_AUTH_STR in tags:
            device["device_auth"] = protocol.cstr(tags[protocol.TAG_DEVICE_AUTH_STR][0])
        if protocol.TAG_STORAGE_ID in tags:
            device["storage_id"] = protocol.cstr(tags[protocol.TAG_STORAGE_ID][0])
        return device

    def discover_cloud(self, device_id: str | None = None) -> list[dict[str, Any]]:
        """GET http://ipv4-api.hdhomerun.com/discover[?DeviceID=<id>].

        SiliconDust's cloud discovery endpoint — resolves a device's current
        LAN IP by its DeviceID even when local broadcast can't reach it
        (e.g. client on a different VLAN). Returns
        ``[{"DeviceID","LocalIP","BaseURL","DiscoverURL","LineupURL"}]``.
        """
        params = {"DeviceID": device_id} if device_id else None
        response = requests.get(CLOUD_DISCOVER_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        devices = response.json()
        _write_cache(devices, source="cloud")
        return devices
