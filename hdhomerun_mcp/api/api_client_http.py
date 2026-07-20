"""HDHomeRun device HTTP JSON API (https://info.hdhomerun.com/info/http_api).

Covers ``discover.json``, ``lineup.json``/``lineup_status.json`` + scan
control, and the streaming-URL builder. Ground-truthed against a live
HDHomeRun FLEX 4K (DeviceID 10ACFCDE, FW hdhomerun_dvr_atsc3 20260326):
``discover.json``/``lineup.json``/``lineup_status.json`` and the
``lineup.post?scan=start``/``scan=abort`` control pair were all confirmed live
during development of this package.

Note: the per-tuner ``status``/``vstatus``/``target``/``channel``/``program``/
``streaminfo``/``debug`` items are **not** HTTP endpoints on real hardware —
confirmed by probing a live device (all returned HTTP 404). They are exposed
only via the binary ``hdhomerun_config`` TCP control protocol on port 65001;
see ``api_client_config.py``.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.exceptions import ParameterError

from .api_client_base import HDHomeRunApiBase

#: EXTEND-model transcode profiles (query param `transcode=<profile>`).
TRANSCODE_PROFILES = (
    "heavy",
    "mobile",
    "internet540",
    "internet480",
    "internet360",
    "internet240",
)

#: X-HDHomeRun-Error header codes (http_api doc).
HTTP_API_ERROR_CODES = {
    801: "Unknown Channel",
    802: "Unknown Transcode Profile (EXTEND only)",
    803: "System Busy (device is mid channel-scan)",
    804: "Tuner In Use (specific tuner requested)",
    805: "All Tuners In Use",
    806: "Tune Failed",
    807: "No Video Data",
    808: "DVR Failure",
    809: "Playback Connection Limit",
    810: "DVR Full",
    811: "Content Protection Required (PRIME only)",
}


class HDHomeRunApiHttp(HDHomeRunApiBase):
    """HTTP JSON API: discovery, channel lineup, scan control, stream URLs."""

    def get_discover(self) -> dict[str, Any]:
        """GET /discover.json — FriendlyName/ModelNumber/FirmwareVersion/DeviceID/
        DeviceAuth/BaseURL/LineupURL/TunerCount."""
        return self._get_json(f"{self.require_url()}/discover.json")

    def get_lineup(self, fmt: str = "json") -> Any:
        """GET /lineup.{json,xml,m3u} — the channel list.

        JSON entries: GuideNumber, GuideName, VideoCodec, AudioCodec, HD,
        Favorite, DRM, URL (per the http_api doc + observed live fields).
        """
        if fmt not in ("json", "xml", "m3u"):
            raise ParameterError(f"fmt must be one of json/xml/m3u, got {fmt!r}")
        if fmt == "json":
            return self._get_json(f"{self.require_url()}/lineup.json")
        response = self._get(f"{self.require_url()}/lineup.{fmt}")
        return response.text

    def get_lineup_status(self) -> dict[str, Any]:
        """GET /lineup_status.json — scan state.

        Idle: {ScanInProgress, ScanPossible, Source, SourceList}.
        Scanning: {ScanInProgress:1, Progress, Found}.
        """
        return self._get_json(f"{self.require_url()}/lineup_status.json")

    def start_scan(self, source: str | None = None) -> None:
        """POST /lineup.post?scan=start[&source=<Source>] — begin a channel scan."""
        params = {"scan": "start"}
        if source:
            params["source"] = source
        self._post(f"{self.require_url()}/lineup.post", params=params)

    def abort_scan(self) -> None:
        """POST /lineup.post?scan=abort — cancel an in-progress channel scan."""
        self._post(f"{self.require_url()}/lineup.post", params={"scan": "abort"})

    def build_stream_url(
        self,
        channel: str,
        tuner: str | int | None = None,
        by_frequency: bool = False,
        program: int | None = None,
        duration: int | None = None,
        transcode: str | None = None,
    ) -> str:
        """Build a live-stream URL: /{auto|tuner<n>}/{v<channel>|ch<freq>[-<program>]}.

        Args:
            channel: virtual channel number (e.g. "24.1") or RF frequency in Hz
                when ``by_frequency`` is True.
            tuner: tuner index (0-3) to force a specific tuner, or None for
                ``/auto/`` (first available tuner).
            by_frequency: use ``ch<frequency>`` addressing instead of ``v<channel>``.
            program: sub-channel program number (only with ``by_frequency``).
            duration: optional stream duration limit in seconds.
            transcode: optional EXTEND-model transcode profile.
        """
        if transcode is not None and transcode not in TRANSCODE_PROFILES:
            raise ParameterError(
                f"transcode must be one of {TRANSCODE_PROFILES}, got {transcode!r}"
            )
        tuner_segment = f"tuner{tuner}" if tuner is not None else "auto"
        if by_frequency:
            chan_segment = f"ch{channel}"
            if program is not None:
                chan_segment += f"-{program}"
        else:
            chan_segment = f"v{channel}"
        url = f"{self.require_url()}:5004/{tuner_segment}/{chan_segment}"
        params = []
        if duration is not None:
            params.append(f"duration={duration}")
        if transcode is not None:
            params.append(f"transcode={transcode}")
        if params:
            url += "?" + "&".join(params)
        return url
