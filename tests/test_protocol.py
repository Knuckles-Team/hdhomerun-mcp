"""Wire protocol framing/TLV tests — mirrors the packet shapes confirmed live
against a HDHomeRun FLEX 4K during development. CONCEPT:HDHR-config.protocol.tuner-control"""

import pytest

from hdhomerun_mcp.api import protocol


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_var_length_round_trip_short():
    """Lengths <=127 encode as a single byte. CONCEPT:HDHR-config.protocol.tuner-control"""
    encoded = protocol.write_var_length(11)
    assert encoded == bytes([11])
    length, consumed = protocol.read_var_length(encoded, 0)
    assert (length, consumed) == (11, 1)


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_var_length_round_trip_long():
    """Lengths >=128 encode as a 2-byte 7-bit-continuation sequence. CONCEPT:HDHR-config.protocol.tuner-control"""
    encoded = protocol.write_var_length(200)
    length, consumed = protocol.read_var_length(encoded, 0)
    assert (length, consumed) == (200, 2)


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_build_and_parse_packet_round_trip():
    """A built packet parses back with a valid CRC and the original TLVs. CONCEPT:HDHR-config.protocol.tuner-control"""
    payload = protocol.encode_tlv(protocol.TAG_GETSET_NAME, b"/sys/model\x00")
    packet = protocol.build_packet(protocol.TYPE_GETSET_REQ, payload)
    parsed = protocol.parse_packet(packet)
    assert parsed.crc_valid
    assert parsed.pkt_type == protocol.TYPE_GETSET_REQ
    assert protocol.cstr(parsed.tags[protocol.TAG_GETSET_NAME][0]) == "/sys/model"


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_parse_packet_detects_bad_crc():
    """A corrupted packet fails the CRC check. CONCEPT:HDHR-config.protocol.tuner-control"""
    payload = protocol.encode_tlv(protocol.TAG_GETSET_NAME, b"/sys/model\x00")
    packet = bytearray(protocol.build_packet(protocol.TYPE_GETSET_REQ, payload))
    packet[-1] ^= 0xFF
    parsed = protocol.parse_packet(bytes(packet))
    assert not parsed.crc_valid


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_build_getset_request_get_vs_set():
    """A get request carries only NAME; a set request also carries VALUE. CONCEPT:HDHR-config.protocol.tuner-control"""
    get_pkt = protocol.parse_packet(protocol.build_getset_request("/tuner0/channel"))
    assert protocol.TAG_GETSET_VALUE not in get_pkt.tags

    set_pkt = protocol.parse_packet(
        protocol.build_getset_request("/tuner0/channel", "auto:60")
    )
    assert protocol.cstr(set_pkt.tags[protocol.TAG_GETSET_VALUE][0]) == "auto:60"


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_build_discover_request_tags():
    """A discover request carries DEVICE_TYPE=TUNER and the given DEVICE_ID. CONCEPT:HDHR-config.protocol.tuner-control"""
    pkt = protocol.parse_packet(protocol.build_discover_request(0x10ACFCDE))
    assert pkt.pkt_type == protocol.TYPE_DISCOVER_REQ
    device_type = int.from_bytes(pkt.tags[protocol.TAG_DEVICE_TYPE][0], "big")
    device_id = int.from_bytes(pkt.tags[protocol.TAG_DEVICE_ID][0], "big")
    assert device_type == protocol.DEVICE_TYPE_TUNER
    assert device_id == 0x10ACFCDE


@pytest.mark.concept("HDHR-config.protocol.tuner-control")
def test_decode_tlvs_matches_live_device_capture():
    """Matches a real GETSET_RPY payload byte-capture from a live FLEX 4K
    (get /sys/model): NAME then VALUE tags, both NUL-terminated. CONCEPT:HDHR-config.protocol.tuner-control"""
    payload = bytes.fromhex(
        "030b2f7379732f6d6f64656c0004146864686f6d6572756e5f6476725f617473633300"
    )
    tags = protocol.decode_tlvs(payload)
    assert protocol.cstr(tags[protocol.TAG_GETSET_NAME][0]) == "/sys/model"
    assert protocol.cstr(tags[protocol.TAG_GETSET_VALUE][0]) == "hdhomerun_dvr_atsc3"
