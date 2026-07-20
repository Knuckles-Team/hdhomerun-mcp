"""HDHomeRun DVR API (https://info.hdhomerun.com/info/dvr_api).

Two distinct surfaces documented on the DVR API page and its wiki-mirrored
sub-pages (dvr_recording_rules, record_engine_status, live_tv,
poke_record_engine, deleting_recordings):

1. **SiliconDust cloud recording-rules API** — ``https://api.hdhomerun.com/api/
   recording_rules``, authenticated by concatenating the ``DeviceAuth`` strings
   of every tuner in the household (from each tuner's ``discover.json``).
2. **Local record-engine API** — a separate service (the DVR "record engine",
   e.g. HDHomeRun SCRIBE or the desktop/NAS record-engine software) reachable
   on the local network at its own ``BaseURL``: ``discover.json`` (status),
   ``StorageURL`` → ``recorded_files.json`` (recordings list), Live TV
   buffered playback, "poke" (recompute record tasks), and per-recording
   delete.

Note: this package's paired FLEX 4K test device is tuner-only hardware with no
record engine present on the LAN, so the record-engine methods below are
implemented strictly per the documented wire format and exercised with mocks
in ``tests/`` — not against a live record engine.
"""

from __future__ import annotations

from typing import Any

from .api_client_base import HDHomeRunApiBase

RECORDING_RULES_URL = "https://api.hdhomerun.com/api/recording_rules"


class HDHomeRunApiDvr(HDHomeRunApiBase):
    """SiliconDust cloud recording-rules API + local record-engine API."""

    # -- Cloud recording rules -------------------------------------------------

    def list_recording_rules(self, device_auth: str | None = None) -> Any:
        """List all recording rules for the household's DeviceAuth(s)."""
        return self._get_json(
            RECORDING_RULES_URL,
            params={"DeviceAuth": self._require_device_auth(device_auth)},
        )

    def add_series_rule(
        self,
        series_id: str,
        device_auth: str | None = None,
        channel_only: str | None = None,
        team_only: str | None = None,
        recent_only: bool | None = None,
        after_original_airdate_only: int | None = None,
        start_padding: int | None = None,
        end_padding: int | None = None,
    ) -> Any:
        """Add a Series (or Movie) recording rule for a SeriesID."""
        params = self._rule_params(
            device_auth=device_auth,
            cmd="add",
            SeriesID=series_id,
            ChannelOnly=channel_only,
            TeamOnly=team_only,
            RecentOnly=int(recent_only) if recent_only is not None else None,
            AfterOriginalAirdateOnly=after_original_airdate_only,
            StartPadding=start_padding,
            EndPadding=end_padding,
        )
        return self._get_json(RECORDING_RULES_URL, params=params)

    def add_datetime_rule(
        self,
        series_id: str,
        date_time_only: int,
        channel_only: str,
        device_auth: str | None = None,
        start_padding: int | None = None,
        end_padding: int | None = None,
    ) -> Any:
        """Add a DateTimeOnly-ChannelOnly rule (record one specific airing)."""
        params = self._rule_params(
            device_auth=device_auth,
            cmd="add",
            SeriesID=series_id,
            DateTimeOnly=date_time_only,
            ChannelOnly=channel_only,
            StartPadding=start_padding,
            EndPadding=end_padding,
        )
        return self._get_json(RECORDING_RULES_URL, params=params)

    def change_rule(
        self,
        device_auth: str | None = None,
        recording_rule_id: str | None = None,
        series_id: str | None = None,
        date_time_only: int | None = None,
        channel_only: str | None = None,
        team_only: str | None = None,
        recent_only: bool | None = None,
        after_original_airdate_only: int | None = None,
        start_padding: int | None = None,
        end_padding: int | None = None,
        after_recording_rule_id: str | None = None,
    ) -> Any:
        """Modify a rule, or reprioritize it via ``after_recording_rule_id``."""
        params = self._rule_params(
            device_auth=device_auth,
            cmd="change",
            RecordingRuleID=recording_rule_id,
            SeriesID=series_id,
            DateTimeOnly=date_time_only,
            ChannelOnly=channel_only,
            TeamOnly=team_only,
            RecentOnly=int(recent_only) if recent_only is not None else None,
            AfterOriginalAirdateOnly=after_original_airdate_only,
            StartPadding=start_padding,
            EndPadding=end_padding,
            AfterRecordingRuleID=after_recording_rule_id,
        )
        return self._get_json(RECORDING_RULES_URL, params=params)

    def delete_rule(
        self,
        device_auth: str | None = None,
        recording_rule_id: str | None = None,
        series_id: str | None = None,
        date_time_only: int | None = None,
        channel_only: str | None = None,
    ) -> Any:
        """Delete a Series/Movie rule (by RecordingRuleID or SeriesID) or a
        DateTimeOnly-ChannelOnly rule (RecordingRuleID, or SeriesID+DateTimeOnly+ChannelOnly)."""
        params = self._rule_params(
            device_auth=device_auth,
            cmd="delete",
            RecordingRuleID=recording_rule_id,
            SeriesID=series_id,
            DateTimeOnly=date_time_only,
            ChannelOnly=channel_only,
        )
        return self._get_json(RECORDING_RULES_URL, params=params)

    def _require_device_auth(self, device_auth: str | None) -> str:
        auth = device_auth or self.device_auth
        if not auth:
            from agent_utilities.core.exceptions import ParameterError

            raise ParameterError(
                "DeviceAuth is required for the DVR cloud API. Set HDHOMERUN_DEVICE_AUTH "
                "or pass device_auth= (concatenate every tuner's DeviceAuth if there is "
                "more than one in the household)."
            )
        return auth

    def _rule_params(self, device_auth: str | None, cmd: str, **fields: Any) -> dict:
        params: dict[str, Any] = {
            "DeviceAuth": self._require_device_auth(device_auth),
            "Cmd": cmd,
        }
        params.update({k: v for k, v in fields.items() if v is not None})
        return params

    # -- Local record engine ----------------------------------------------------

    def get_record_engine_status(self, storage_engine_base_url: str) -> Any:
        """GET <storage engine BaseURL>/discover.json — FriendlyName/Version/
        BaseURL/StorageURL/FreeSpace of the local record engine."""
        return self._get_json(f"{storage_engine_base_url.rstrip('/')}/discover.json")

    def get_recorded_files(self, storage_url: str) -> Any:
        """GET <StorageURL> (``recorded_files.json``) — the list of recordings
        available for playback, each including its own ``CmdURL``/``PlayURL``."""
        return self._get_json(storage_url)

    def poke_record_engine(self, storage_engine_base_url: str) -> None:
        """POST <storage engine BaseURL>/recording_events.post?sync.

        Tells the record engine to recompute upcoming record tasks — call
        after adding/changing/deleting a recording rule.
        """
        self._post(
            f"{storage_engine_base_url.rstrip('/')}/recording_events.post",
            params={"sync": ""},
        )

    def delete_recording(self, cmd_url: str, rerecord: bool = False) -> None:
        """POST <CmdURL from recorded_files.json> cmd=delete[&rerecord=1].

        Must be POST (HTTP GET is rejected with 400). Set ``rerecord=True`` to
        tell the DVR to record the episode again on a future airing.
        """
        params = {"cmd": "delete"}
        if rerecord:
            params["rerecord"] = "1"
        self._post(cmd_url, params=params)

    def build_live_tv_url(
        self,
        storage_engine_base_url: str,
        channel: str,
        client_id: str,
        session_id: str,
    ) -> str:
        """Build a record-engine buffered Live TV URL.

        ``ClientID`` must be stable per app instance/picture-in-picture pane;
        ``SessionID`` must be unique per new channel request (reused only when
        seeking within the same session) — see the ``live_tv`` doc page.
        """
        base = storage_engine_base_url.rstrip("/")
        return f"{base}/auto/v{channel}?ClientID={client_id}&SessionID={session_id}"
