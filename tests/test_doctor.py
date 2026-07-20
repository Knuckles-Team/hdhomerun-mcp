"""Doctor diagnostic-suite tests. CONCEPT:HDHR-doctor.diagnostics.health-report"""

from unittest.mock import MagicMock, patch

import pytest
import requests


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_device_reachable_pass(client):
    """A reachable device reports a pass with the discover.json payload. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    info = {"DeviceID": "10ACFCDE", "TunerCount": 4}
    with patch.object(client, "get_discover", return_value=info):
        result = client.check_device_reachable()
    assert result["status"] == "pass"
    assert result["detail"] == info


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_device_reachable_fail_has_action(client):
    """An unreachable device fails with an actionable next step. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    with patch.object(
        client, "get_discover", side_effect=requests.ConnectionError("refused")
    ):
        result = client.check_device_reachable()
    assert result["status"] == "fail"
    assert "action" in result and result["action"]


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_device_auth_fail_when_missing(client):
    """Missing DeviceAuth in discover.json fails with an actionable message. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    result = client.check_device_auth(info={"DeviceID": "x"})
    assert result["status"] == "fail"
    assert "DeviceAuth" in result["action"]


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_device_auth_pass_when_present(client):
    """DeviceAuth present (no cloud validation requested) passes. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    result = client.check_device_auth(info={"DeviceAuth": "abc"})
    assert result["status"] == "pass"


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_tuner_count_vs_jellyfin_skip_without_config(client):
    """No Jellyfin URL/key configured => skip, not fail. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    result = client.check_tuner_count_vs_jellyfin(None, None, "10ACFCDE")
    assert result["status"] == "skip"


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_tuner_count_vs_jellyfin_mismatch_warns(client):
    """A TunerCount mismatch between the device and Jellyfin warns. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    response = MagicMock()
    response.json.return_value = [{"DeviceId": "10ACFCDE", "TunerCount": 2}]
    response.raise_for_status.return_value = None
    with patch("requests.get", return_value=response):
        result = client.check_tuner_count_vs_jellyfin(
            "http://jellyfin.arpa",
            "api-key",
            "10ACFCDE",
            info={"DeviceID": "10ACFCDE", "TunerCount": 4},
        )
    assert result["status"] == "warn"


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_check_discovery_cache_freshness_missing(client, monkeypatch, tmp_path):
    """No discovery cache on disk warns (not fail). CONCEPT:HDHR-doctor.diagnostics.health-report"""
    missing = tmp_path / "missing.json"
    # read_discovery_cache() reads api_client_discovery's own module-level
    # DISCOVERY_CACHE_PATH; api_client_doctor's imported name is used only for
    # the warning message, so both must be patched to isolate this test from
    # any real cache left on disk by prior discovery calls.
    monkeypatch.setattr(
        "hdhomerun_mcp.api.api_client_discovery.DISCOVERY_CACHE_PATH", missing
    )
    monkeypatch.setattr("hdhomerun_mcp.api.api_client_doctor.DISCOVERY_CACHE_PATH", missing)
    result = client.check_discovery_cache_freshness()
    assert result["status"] == "warn"


@pytest.mark.concept("HDHR-doctor.diagnostics.health-report")
def test_run_doctor_aggregates_overall_status(client):
    """run_doctor() reports 'fail' overall when device_reachable fails. CONCEPT:HDHR-doctor.diagnostics.health-report"""
    with patch.object(
        client, "get_discover", side_effect=requests.ConnectionError("refused")
    ):
        report = client.run_doctor()
    assert report["overall"] == "fail"
    assert any(c["check"] == "device_reachable" for c in report["checks"])
