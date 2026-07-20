"""HDHomeRun binary wire protocol (packet framing + TLV encoding).

Shared by the local UDP discovery client (``api_client_discovery.py``) and the
TCP control-protocol client (``api_client_config.py`` — the same protocol the
official ``hdhomerun_config`` CLI tool speaks). Both protocols listen on port
``65001`` (UDP for discovery, TCP for control) and use an identical packet
format, per ``hdhomerun_pkt.h`` in the official libhdhomerun source
(https://github.com/Silicondust/libhdhomerun):

    uint16_t  Packet type       (big-endian)
    uint16_t  Payload length    (big-endian, bytes)
    uint8_t[] Payload           (tag-length-value sequence)
    uint32_t  CRC               (little-endian, Ethernet-style CRC32)

TLV length is 1 byte for values <=127 bytes, else a 2-byte little-endian-ish
7-bit-continuation encoding (see ``read_var_length``/``write_var_length``).

CONCEPT:HDHR-config.protocol.wire-framing — validated byte-for-byte against a live HDHomeRun FLEX 4K
(TCP get on ``/sys/model``, ``/tuner0/status``, etc. and UDP discovery both
round-tripped with correct CRC during development of this package).
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field

HDHOMERUN_DISCOVER_UDP_PORT = 65001
HDHOMERUN_CONTROL_TCP_PORT = 65001

HDHOMERUN_MAX_PACKET_SIZE = 1460

# Packet types
TYPE_DISCOVER_REQ = 0x0002
TYPE_DISCOVER_RPY = 0x0003
TYPE_GETSET_REQ = 0x0004
TYPE_GETSET_RPY = 0x0005
TYPE_UPGRADE_REQ = 0x0006
TYPE_UPGRADE_RPY = 0x0007

# TLV tags
TAG_DEVICE_TYPE = 0x01
TAG_DEVICE_ID = 0x02
TAG_GETSET_NAME = 0x03
TAG_GETSET_VALUE = 0x04
TAG_ERROR_MESSAGE = 0x05
TAG_TUNER_COUNT = 0x10
TAG_GETSET_LOCKKEY = 0x15
TAG_LINEUP_URL = 0x27
TAG_STORAGE_URL = 0x28
TAG_DEVICE_AUTH_BIN_DEPRECATED = 0x29
TAG_BASE_URL = 0x2A
TAG_DEVICE_AUTH_STR = 0x2B
TAG_STORAGE_ID = 0x2C
TAG_MULTI_TYPE = 0x2D

DEVICE_TYPE_WILDCARD = 0xFFFFFFFF
DEVICE_TYPE_TUNER = 0x00000001
DEVICE_TYPE_STORAGE = 0x00000005
DEVICE_ID_WILDCARD = 0xFFFFFFFF


def write_var_length(value: int) -> bytes:
    """Encode a TLV length per the libhdhomerun variable-length rule."""
    if value <= 0x7F:
        return bytes([value])
    if value > 0x3FFF:
        raise ValueError(f"TLV length {value} exceeds the 14-bit maximum")
    low = (value & 0x7F) | 0x80
    high = value >> 7
    return bytes([low, high])


def read_var_length(buf: bytes, offset: int) -> tuple[int, int]:
    """Decode a TLV length starting at ``offset``. Returns (length, bytes_consumed)."""
    b0 = buf[offset]
    if b0 & 0x80:
        b1 = buf[offset + 1]
        return (b0 & 0x7F) | (b1 << 7), 2
    return b0, 1


def encode_tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + write_var_length(len(value)) + value


def decode_tlvs(payload: bytes) -> dict[int, list[bytes]]:
    """Parse a TLV sequence into {tag: [values]} (a tag may repeat)."""
    tags: dict[int, list[bytes]] = {}
    i = 0
    n = len(payload)
    while i < n:
        tag = payload[i]
        i += 1
        length, consumed = read_var_length(payload, i)
        i += consumed
        value = payload[i : i + length]
        i += length
        tags.setdefault(tag, []).append(value)
    return tags


def build_packet(pkt_type: int, payload: bytes) -> bytes:
    """Frame a payload into a full packet: type + length + payload + CRC32."""
    header = pkt_type.to_bytes(2, "big") + len(payload).to_bytes(2, "big")
    body = header + payload
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return body + crc.to_bytes(4, "little")


@dataclass
class ParsedPacket:
    pkt_type: int
    payload: bytes
    crc_valid: bool
    tags: dict[int, list[bytes]] = field(default_factory=dict)


def parse_packet(data: bytes) -> ParsedPacket:
    """Parse a full received packet (type+length+payload+crc) and verify its CRC."""
    if len(data) < 8:
        raise ValueError(f"Packet too short ({len(data)} bytes)")
    pkt_type = int.from_bytes(data[0:2], "big")
    plen = int.from_bytes(data[2:4], "big")
    payload = data[4 : 4 + plen]
    crc_received = data[4 + plen : 4 + plen + 4]
    crc_calc = (zlib.crc32(data[: 4 + plen]) & 0xFFFFFFFF).to_bytes(4, "little")
    return ParsedPacket(
        pkt_type=pkt_type,
        payload=payload,
        crc_valid=crc_received == crc_calc,
        tags=decode_tlvs(payload),
    )


def cstr(value: bytes) -> str:
    """Decode a NUL-terminated TLV string value."""
    return value.split(b"\x00", 1)[0].decode("utf-8", errors="replace")


def build_getset_request(name: str, value: str | None = None) -> bytes:
    """Build a GETSET_REQ packet (get if value is None, else set)."""
    payload = encode_tlv(TAG_GETSET_NAME, name.encode() + b"\x00")
    if value is not None:
        payload += encode_tlv(TAG_GETSET_VALUE, value.encode() + b"\x00")
    return build_packet(TYPE_GETSET_REQ, payload)


def build_discover_request(device_id: int = DEVICE_ID_WILDCARD) -> bytes:
    """Build a DISCOVER_REQ packet (tuner devices, matching the given device id)."""
    payload = encode_tlv(TAG_DEVICE_TYPE, DEVICE_TYPE_TUNER.to_bytes(4, "big"))
    payload += encode_tlv(TAG_DEVICE_ID, device_id.to_bytes(4, "big"))
    return build_packet(TYPE_DISCOVER_REQ, payload)
