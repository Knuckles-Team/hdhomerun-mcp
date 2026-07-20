from unittest.mock import MagicMock, patch

import pytest

from hdhomerun_mcp.api import ApiClientSystem


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_discover_returns_json(client):
    """discover.json is fetched and parsed as JSON. CONCEPT:HDHR-http.api.json-interface"""
    response = MagicMock()
    response.json.return_value = {"DeviceID": "10ACFCDE", "TunerCount": 4}
    response.raise_for_status.return_value = None
    with patch.object(client._session, "get", return_value=response) as mock_get:
        result = client.get_discover()
    assert result == {"DeviceID": "10ACFCDE", "TunerCount": 4}
    mock_get.assert_called_once()
    assert mock_get.call_args.args[0] == "http://10.0.132.114/discover.json"


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_lineup_status(client):
    """lineup_status.json round-trips the observed real-device field shape. CONCEPT:HDHR-http.api.json-interface"""
    response = MagicMock()
    response.json.return_value = {
        "ScanInProgress": 0,
        "ScanPossible": 1,
        "Source": "Antenna",
        "SourceList": ["Antenna", "Cable"],
    }
    response.raise_for_status.return_value = None
    with patch.object(client._session, "get", return_value=response):
        result = client.get_lineup_status()
    assert result["ScanInProgress"] == 0
    assert result["SourceList"] == ["Antenna", "Cable"]


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_build_stream_url_auto_tuner(client):
    """Stream URL builder matches the observed real lineup.json URL shape. CONCEPT:HDHR-http.api.json-interface"""
    url = client.build_stream_url("24.1")
    assert url == "http://10.0.132.114:5004/auto/v24.1"


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_build_stream_url_specific_tuner_and_params(client):
    """Stream URL builder supports tuner pinning + duration/transcode params. CONCEPT:HDHR-http.api.json-interface"""
    url = client.build_stream_url("24.1", tuner=1, duration=120, transcode="mobile")
    assert url == "http://10.0.132.114:5004/tuner1/v24.1?duration=120&transcode=mobile"


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_build_stream_url_by_frequency(client):
    """Stream URL builder supports ch<freq>[-<program>] addressing. CONCEPT:HDHR-http.api.json-interface"""
    url = client.build_stream_url("473000000", by_frequency=True, program=3)
    assert url == "http://10.0.132.114:5004/auto/ch473000000-3"


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_build_stream_url_rejects_unknown_transcode(client):
    """Unknown transcode profile is rejected before making a request. CONCEPT:HDHR-http.api.json-interface"""
    from agent_utilities.core.exceptions import ParameterError

    with pytest.raises(ParameterError):
        client.build_stream_url("24.1", transcode="bogus")


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_scan_start_and_abort_post(client):
    """Scan control issues POST requests with the correct query params. CONCEPT:HDHR-http.api.json-interface"""
    response = MagicMock()
    response.raise_for_status.return_value = None
    with patch.object(client._session, "post", return_value=response) as mock_post:
        client.start_scan(source="Antenna")
        client.abort_scan()
    assert mock_post.call_args_list[0].kwargs["params"] == {
        "scan": "start",
        "source": "Antenna",
    }
    assert mock_post.call_args_list[1].kwargs["params"] == {"scan": "abort"}


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_require_url_raises_without_url():
    """A client with no URL configured raises a clear parameter error. CONCEPT:HDHR-http.api.json-interface"""
    from agent_utilities.core.exceptions import ParameterError

    client = ApiClientSystem(url="")
    with pytest.raises(ParameterError):
        client.require_url()
