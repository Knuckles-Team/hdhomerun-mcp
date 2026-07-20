"""hdhomerun_config binary control protocol (https://info.hdhomerun.com/info/hdhomerun_config).

This is a **different wire protocol** from the JSON HTTP API: the official
``hdhomerun_config`` CLI tool (and this client) speaks a binary TCP protocol
on port 65001 (get/set requests: packet type ``GETSET_REQ``/``GETSET_RPY``,
same TLV framing as UDP discovery — see ``protocol.py``).

Confirmed live against a HDHomeRun FLEX 4K (device 10ACFCDE) during
development of this package — every ``get`` below round-tripped with a
CRC-valid reply. Two items errored on this firmware/model exactly as the
device reported (not a client bug, kept here as ground truth):
``/tuner0/vstatus`` → "ERROR: unknown getset variable" (vstatus is not
exposed as a plain get on this firmware — the HTTP-era vstatus concept lives
in ``hdhomerun_tuner_vstatus_t`` but this device's control protocol doesn't
surface it as a bare get target), and ``/lineup/location`` → same error (get
is not supported for that item on this firmware; only ``set`` is).

Supported item paths are **device/firmware-dependent** — always start with
``get_help()`` (``get /help``) to discover what a given unit actually
supports before assuming an item exists.
"""

from __future__ import annotations

import socket

from agent_utilities.core.exceptions import ParameterError

from . import protocol
from .api_client_base import HDHomeRunApiBase

DEFAULT_CONTROL_TIMEOUT = 3.0

#: Standard US ATSC broadcast channelmaps (`get help` / `sys/features` on the fleet).
CHANNELMAPS_US = ("us-bcast", "us-cable", "us-hrc", "us-irc")
CHANNELMAPS_EU = (
    "au-bcast",
    "au-cable",
    "eu-bcast",
    "eu-cable",
    "tw-bcast",
    "tw-cable",
)


class HDHomeRunControlError(RuntimeError):
    """Raised when the device returns HDHOMERUN_TAG_ERROR_MESSAGE for a get/set."""


class HDHomeRunApiConfig(HDHomeRunApiBase):
    """hdhomerun_config-equivalent get/set control protocol client (TCP :65001)."""

    def __init__(self, *args, control_ip: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # The control protocol addresses a device by bare IP/hostname, not a URL.
        self.control_ip = control_ip or self.url.split("://")[-1].split(":")[0]

    # -- Low-level get/set --------------------------------------------------

    def _control_transact(
        self,
        name: str,
        value: str | None = None,
        lockkey: int | None = None,
        timeout: float = DEFAULT_CONTROL_TIMEOUT,
    ) -> str:
        """Send a GETSET_REQ (get if value is None, else set) and return the value.

        Raises HDHomeRunControlError if the device returns an error tag.
        """
        if not self.control_ip:
            raise ParameterError(
                "No device IP known for the control protocol. Pass control_ip= or "
                "url= (an IP/hostname), or discover the device first."
            )
        payload = protocol.encode_tlv(protocol.TAG_GETSET_NAME, name.encode() + b"\x00")
        if value is not None:
            payload += protocol.encode_tlv(
                protocol.TAG_GETSET_VALUE, value.encode() + b"\x00"
            )
        if lockkey is not None:
            payload += protocol.encode_tlv(
                protocol.TAG_GETSET_LOCKKEY, lockkey.to_bytes(4, "big")
            )
        request = protocol.build_packet(protocol.TYPE_GETSET_REQ, payload)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((self.control_ip, protocol.HDHOMERUN_CONTROL_TCP_PORT))
            sock.sendall(request)
            data = sock.recv(protocol.HDHOMERUN_MAX_PACKET_SIZE)
        finally:
            sock.close()

        pkt = protocol.parse_packet(data)
        if pkt.pkt_type != protocol.TYPE_GETSET_RPY:
            raise HDHomeRunControlError(
                f"Unexpected reply packet type 0x{pkt.pkt_type:04x}"
            )
        if not pkt.crc_valid:
            raise HDHomeRunControlError("Reply packet failed CRC check")
        if protocol.TAG_ERROR_MESSAGE in pkt.tags:
            raise HDHomeRunControlError(
                protocol.cstr(pkt.tags[protocol.TAG_ERROR_MESSAGE][0])
            )
        if protocol.TAG_GETSET_VALUE not in pkt.tags:
            return ""
        return protocol.cstr(pkt.tags[protocol.TAG_GETSET_VALUE][0])

    def get_item(self, name: str) -> str:
        """``hdhomerun_config <id> get <item>`` — raw get of any supported item path."""
        return self._control_transact(name)

    def set_item(self, name: str, value: str, lockkey: int | None = None) -> str:
        """``hdhomerun_config <id> set <item> <value>`` — raw set (implicit get-back)."""
        return self._control_transact(name, value=value, lockkey=lockkey)

    def get_help(self) -> str:
        """``get help`` — the list of get/set item paths this device supports."""
        return self._control_transact("help")

    # -- Tuner status / diagnostics -----------------------------------------

    def get_tuner_status(self, tuner: int) -> str:
        """``/tuner<n>/status`` — ``ch=... lock=... ss=... snq=... seq=... bps=... pps=...``."""
        return self.get_item(f"/tuner{tuner}/status")

    def get_tuner_vstatus(self, tuner: int) -> str:
        """``/tuner<n>/vstatus`` — virtual-channel auth/CCI/CGMS status (model/firmware
        dependent; some devices report "unknown getset variable")."""
        return self.get_item(f"/tuner{tuner}/vstatus")

    def get_tuner_streaminfo(self, tuner: int) -> str:
        """``/tuner<n>/streaminfo`` — detected programs: ``<num>: <major>.<minor> [name]``."""
        return self.get_item(f"/tuner{tuner}/streaminfo")

    def get_tuner_debug(self, tuner: int) -> str:
        """``/tuner<n>/debug`` — extended tun/dev/ts/flt/net diagnostic counters."""
        return self.get_item(f"/tuner{tuner}/debug")

    # -- Tuning / filtering ---------------------------------------------------

    def get_channel(self, tuner: int) -> str:
        """``/tuner<n>/channel`` — current ``<modulation>:<frequency>`` or ``none``."""
        return self.get_item(f"/tuner{tuner}/channel")

    def set_channel(self, tuner: int, modulation: str, freq_or_channel: str) -> str:
        """``/tuner<n>/channel`` set — e.g. ``auto:651000000`` or ``auto:60``; ``none`` to stop."""
        return self.set_item(
            f"/tuner{tuner}/channel", f"{modulation}:{freq_or_channel}"
        )

    def stop_tuner(self, tuner: int) -> str:
        """Set ``/tuner<n>/channel none`` — release the tuner."""
        return self.set_item(f"/tuner{tuner}/channel", "none")

    def get_channelmap(self, tuner: int) -> str:
        """``/tuner<n>/channelmap`` — the configured channel-to-frequency map."""
        return self.get_item(f"/tuner{tuner}/channelmap")

    def set_channelmap(self, tuner: int, channelmap: str) -> str:
        """``/tuner<n>/channelmap`` set — e.g. ``us-bcast``/``us-cable``/``us-hrc``/``us-irc``."""
        return self.set_item(f"/tuner{tuner}/channelmap", channelmap)

    def get_filter(self, tuner: int) -> str:
        """``/tuner<n>/filter`` — the current PID filter (default ``0x0000-0x1FFF``)."""
        return self.get_item(f"/tuner{tuner}/filter")

    def set_filter(self, tuner: int, pid_filter: str) -> str:
        """``/tuner<n>/filter`` set — e.g. ``0x0000-0x1FFF`` or a space-separated PID list."""
        return self.set_item(f"/tuner{tuner}/filter", pid_filter)

    def get_program(self, tuner: int) -> str:
        """``/tuner<n>/program`` — the current MPEG program (sub-channel) filter."""
        return self.get_item(f"/tuner{tuner}/program")

    def set_program(self, tuner: int, program_number: int | str) -> str:
        """``/tuner<n>/program`` set — filter to a single program (sub-channel) number."""
        return self.set_item(f"/tuner{tuner}/program", str(program_number))

    def get_target(self, tuner: int) -> str:
        """``/tuner<n>/target`` — the current UDP/RTP streaming target."""
        return self.get_item(f"/tuner{tuner}/target")

    def set_target(self, tuner: int, target: str) -> str:
        """``/tuner<n>/target`` set — e.g. ``udp://192.168.1.100:5000`` or ``rtp://...``."""
        return self.set_item(f"/tuner{tuner}/target", target)

    def get_lockkey(self, tuner: int) -> str:
        """``/tuner<n>/lockkey`` — current tuner lock owner (``none`` if unlocked)."""
        return self.get_item(f"/tuner{tuner}/lockkey")

    def set_lockkey(self, tuner: int, lock: bool, lockkey: int | None = None) -> str:
        """``/tuner<n>/lockkey`` set/clear — pass ``lock=False`` to release."""
        return self.set_item(
            f"/tuner{tuner}/lockkey", "set" if lock else "none", lockkey=lockkey
        )

    # -- IR / lineup / system -------------------------------------------------

    def get_ir_target(self) -> str:
        """``/ir/target`` — the configured IR-blaster target IP:port."""
        return self.get_item("/ir/target")

    def set_ir_target(self, target: str) -> str:
        """``/ir/target`` set — ``<ip>:<port>``."""
        return self.set_item("/ir/target", target)

    def set_lineup_location(self, country_code: str, postal_code: str) -> str:
        """``/lineup/location`` set — ``<countrycode>:<postcode>`` (or set to "disabled")."""
        return self.set_item("/lineup/location", f"{country_code}:{postal_code}")

    def disable_lineup_location(self) -> str:
        """Disable the lineup-server connection (``/lineup/location disabled``)."""
        return self.set_item("/lineup/location", "disabled")

    def get_sys_model(self) -> str:
        """``/sys/model`` — the device model name."""
        return self.get_item("/sys/model")

    def get_sys_features(self) -> str:
        """``/sys/features`` — supported channelmaps/modulations for this device."""
        return self.get_item("/sys/features")

    def get_sys_version(self) -> str:
        """``/sys/version`` — the firmware version string."""
        return self.get_item("/sys/version")

    def get_sys_copyright(self) -> str:
        """``/sys/copyright`` — the firmware copyright notice."""
        return self.get_item("/sys/copyright")

    def get_sys_debug(self) -> str:
        """``/sys/debug`` — device-wide debug info."""
        return self.get_item("/sys/debug")

    def restart_device(self) -> str:
        """``/sys/restart self`` — reboot the HDHomeRun. Destructive; use with care."""
        return self.set_item("/sys/restart", "self")

    def parse_tuner_status(self, status_line: str) -> dict[str, str]:
        """Parse a ``ch=... lock=... ss=... snq=... seq=... bps=... pps=...`` status line."""
        parsed: dict[str, str] = {}
        for token in status_line.split():
            if "=" in token:
                key, _, val = token.partition("=")
                parsed[key] = val
        return parsed
