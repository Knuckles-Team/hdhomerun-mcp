"""hdhomerun_config binary control-protocol client tests (TCP socket mocked).
CONCEPT:HDHR-config.protocol.tuner-control"""

from unittest.mock import MagicMock, patch

import pytest

from hdhomerun_mcp.api import protocol
from hdhomerun_mcp.api.api_client_config import HDHomeRunControlError


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_control_ip_derived_from_url(client):
    """control_ip defaults to the host portion of the device URL. CONCEPT:HDHR-config.protocol.tuner-control"""
    assert client.control_ip == "10.0.132.114"


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_get_sys_model_success(client):
    """A successful get returns the decoded VALUE. CONCEPT:HDHR-config.protocol.tuner-control"""
    reply = protocol.build_packet(
        protocol.TYPE_GETSET_RPY,
        protocol.encode_tlv(protocol.TAG_GETSET_NAME, b"/sys/model\x00")
        + protocol.encode_tlv(protocol.TAG_GETSET_VALUE, b"hdhomerun_dvr_atsc3\x00"),
    )
    mock_sock = MagicMock()
    mock_sock.recv.return_value = reply
    with patch("socket.socket", return_value=mock_sock):
        value = client.get_sys_model()
    assert value == "hdhomerun_dvr_atsc3"
    mock_sock.connect.assert_called_once_with(("10.0.132.114", 65001))


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_get_item_raises_on_device_error(client):
    """An ERROR_MESSAGE tag in the reply raises HDHomeRunControlError. CONCEPT:HDHR-config.protocol.tuner-control"""
    reply = protocol.build_packet(
        protocol.TYPE_GETSET_RPY,
        protocol.encode_tlv(protocol.TAG_GETSET_NAME, b"/tuner0/vstatus\x00")
        + protocol.encode_tlv(
            protocol.TAG_ERROR_MESSAGE, b"ERROR: unknown getset variable\x00"
        ),
    )
    mock_sock = MagicMock()
    mock_sock.recv.return_value = reply
    with patch("socket.socket", return_value=mock_sock):
        with pytest.raises(HDHomeRunControlError, match="unknown getset variable"):
            client.get_tuner_vstatus(0)


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_set_channel_sends_name_and_value(client):
    """set_channel encodes both NAME and VALUE TLVs. CONCEPT:HDHR-config.protocol.tuner-control"""
    reply = protocol.build_packet(
        protocol.TYPE_GETSET_RPY,
        protocol.encode_tlv(protocol.TAG_GETSET_NAME, b"/tuner0/channel\x00")
        + protocol.encode_tlv(protocol.TAG_GETSET_VALUE, b"auto:60\x00"),
    )
    mock_sock = MagicMock()
    mock_sock.recv.return_value = reply
    with patch("socket.socket", return_value=mock_sock):
        value = client.set_channel(0, "auto", "60")
    assert value == "auto:60"
    sent = mock_sock.sendall.call_args.args[0]
    parsed = protocol.parse_packet(sent)
    assert parsed.crc_valid
    assert protocol.cstr(parsed.tags[protocol.TAG_GETSET_NAME][0]) == "/tuner0/channel"
    assert protocol.cstr(parsed.tags[protocol.TAG_GETSET_VALUE][0]) == "auto:60"


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_parse_tuner_status():
    """parse_tuner_status splits a real status line into a dict. CONCEPT:HDHR-config.protocol.tuner-control"""
    from hdhomerun_mcp.api import ApiClientSystem

    c = ApiClientSystem(url="http://10.0.132.114")
    parsed = c.parse_tuner_status("ch=none lock=none ss=0 snq=0 seq=0 bps=0 pps=0")
    assert parsed == {
        "ch": "none",
        "lock": "none",
        "ss": "0",
        "snq": "0",
        "seq": "0",
        "bps": "0",
        "pps": "0",
    }
