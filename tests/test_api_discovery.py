"""Discovery domain tests — cloud endpoint (requests mocked) + cache. CONCEPT:HDHR-discovery.network.device-location"""

import json
from unittest.mock import MagicMock, patch

import pytest

from hdhomerun_mcp.api.api_client_discovery import read_discovery_cache


@pytest.mark.concept("HDHR-discovery.network.device-location")
def test_discover_cloud_parses_response(client, tmp_path, monkeypatch):
    """Cloud discovery hits ipv4-api.hdhomerun.com and caches the result. CONCEPT:HDHR-discovery.network.device-location"""
    cache_path = tmp_path / "hdhomerun_discovery_cache.json"
    monkeypatch.setattr(
        "hdhomerun_mcp.api.api_client_discovery.DISCOVERY_CACHE_PATH", cache_path
    )
    response = MagicMock()
    response.json.return_value = [
        {
            "DeviceID": "10ACFCDE",
            "LocalIP": "10.0.132.114",
            "BaseURL": "http://10.0.132.114",
            "DiscoverURL": "http://10.0.132.114/discover.json",
            "LineupURL": "http://10.0.132.114/lineup.json",
        }
    ]
    response.raise_for_status.return_value = None
    with patch("requests.get", return_value=response) as mock_get:
        devices = client.discover_cloud(device_id="10ACFCDE")
    assert devices[0]["DeviceID"] == "10ACFCDE"
    assert mock_get.call_args.kwargs["params"] == {"DeviceID": "10ACFCDE"}
    cached = json.loads(cache_path.read_text())
    assert cached["source"] == "cloud"
    assert cached["devices"] == devices


@pytest.mark.concept("HDHR-discovery.network.device-location")
def test_read_discovery_cache_missing(monkeypatch, tmp_path):
    """Reading a nonexistent cache returns None, not an error. CONCEPT:HDHR-discovery.network.device-location"""
    monkeypatch.setattr(
        "hdhomerun_mcp.api.api_client_discovery.DISCOVERY_CACHE_PATH",
        tmp_path / "does_not_exist.json",
    )
    assert read_discovery_cache() is None


@pytest.mark.concept("HDHR-discovery.network.device-location")
def test_device_from_tags_decodes_real_capture(client):
    """_device_from_tags decodes the TLV tag shape confirmed against a live
    FLEX 4K's UDP DISCOVER_RPY (device id/tuner count/base+lineup url/device
    auth). CONCEPT:HDHR-discovery.network.device-location"""
    from hdhomerun_mcp.api import protocol

    payload = (
        protocol.encode_tlv(protocol.TAG_DEVICE_TYPE, (1).to_bytes(4, "big"))
        + protocol.encode_tlv(protocol.TAG_DEVICE_ID, bytes.fromhex("10acfcde"))
        + protocol.encode_tlv(protocol.TAG_DEVICE_AUTH_STR, b"test-auth\x00")
        + protocol.encode_tlv(protocol.TAG_BASE_URL, b"http://10.0.132.114:80\x00")
        + protocol.encode_tlv(protocol.TAG_TUNER_COUNT, (4).to_bytes(1, "big"))
        + protocol.encode_tlv(
            protocol.TAG_LINEUP_URL, b"http://10.0.132.114:80/lineup.json\x00"
        )
    )
    tags = protocol.decode_tlvs(payload)
    device = client._device_from_tags(tags, "10.0.132.114")
    assert device["device_id"] == "10ACFCDE"
    assert device["tuner_count"] == 4
    assert device["base_url"] == "http://10.0.132.114:80"
    assert device["lineup_url"] == "http://10.0.132.114:80/lineup.json"
    assert device["device_auth"] == "test-auth"
