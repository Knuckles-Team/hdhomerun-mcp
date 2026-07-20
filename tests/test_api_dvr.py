"""DVR cloud recording-rules API tests (requests mocked). CONCEPT:HDHR-dvr.cloud.recording-rules"""

from unittest.mock import MagicMock, patch

import pytest

from hdhomerun_mcp.api.api_client_dvr import RECORDING_RULES_URL


@pytest.mark.concept("HDHR-dvr.cloud.recording-rules")
def test_list_recording_rules_uses_device_auth(client):
    """DeviceAuth defaults from the client when not passed explicitly. CONCEPT:HDHR-dvr.cloud.recording-rules"""
    response = MagicMock()
    response.json.return_value = []
    response.raise_for_status.return_value = None
    with patch.object(client._session, "get", return_value=response) as mock_get:
        client.list_recording_rules()
    assert mock_get.call_args.args[0] == RECORDING_RULES_URL
    assert mock_get.call_args.kwargs["params"] == {"DeviceAuth": "test-auth"}


@pytest.mark.concept("HDHR-dvr.cloud.recording-rules")
def test_add_series_rule_params(client):
    """add_series_rule builds the documented Cmd=add param set. CONCEPT:HDHR-dvr.cloud.recording-rules"""
    response = MagicMock()
    response.json.return_value = [{"RecordingRuleID": "1"}]
    response.raise_for_status.return_value = None
    with patch.object(client._session, "get", return_value=response) as mock_get:
        client.add_series_rule(series_id="11579711", channel_only="2.1|702", recent_only=True)
    params = mock_get.call_args.kwargs["params"]
    assert params["Cmd"] == "add"
    assert params["SeriesID"] == "11579711"
    assert params["ChannelOnly"] == "2.1|702"
    assert params["RecentOnly"] == 1


@pytest.mark.concept("HDHR-dvr.cloud.recording-rules")
def test_delete_rule_without_auth_raises(client):
    """Missing DeviceAuth (client + call site) raises a clear parameter error. CONCEPT:HDHR-dvr.cloud.recording-rules"""
    from agent_utilities.core.exceptions import ParameterError

    client.device_auth = None
    with pytest.raises(ParameterError):
        client.delete_rule(recording_rule_id="1")


@pytest.mark.concept("HDHR-dvr.cloud.recording-rules")
def test_delete_recording_requires_post(client):
    """delete_recording issues a POST (GET is rejected by the record engine). CONCEPT:HDHR-dvr.cloud.recording-rules"""
    response = MagicMock()
    response.raise_for_status.return_value = None
    with patch.object(client._session, "post", return_value=response) as mock_post:
        client.delete_recording("http://10.20.20.162:4999/recorded/cmd/1", rerecord=True)
    assert mock_post.call_args.kwargs["params"] == {"cmd": "delete", "rerecord": "1"}


@pytest.mark.concept("HDHR-dvr.cloud.recording-rules")
def test_build_live_tv_url(client):
    """Live TV URL includes ClientID/SessionID per the live_tv doc page. CONCEPT:HDHR-dvr.cloud.recording-rules"""
    url = client.build_live_tv_url(
        "http://10.20.20.162:4999", "2.1", client_id="abc-123", session_id="deadbeef"
    )
    assert url == (
        "http://10.20.20.162:4999/auto/v2.1?ClientID=abc-123&SessionID=deadbeef"
    )
