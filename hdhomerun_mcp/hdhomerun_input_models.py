#!/usr/bin/python
"""Pydantic input models for HDHomeRun MCP API request parameters.

These are documentation/validation aids for the higher-traffic operations;
the api client methods themselves accept plain keyword arguments (see
``hdhomerun_mcp/api/``) so callers are not forced through a model.
"""

from pydantic import BaseModel, Field


class StreamUrlInput(BaseModel):
    """Input model for building a live-stream URL."""

    channel: str = Field(
        description="Virtual channel (e.g. '24.1') or RF frequency in Hz."
    )
    tuner: int | None = Field(default=None, description="Force a specific tuner (0-3).")
    by_frequency: bool = Field(
        default=False, description="Use ch<frequency> addressing instead of v<channel>."
    )
    program: int | None = Field(
        default=None, description="Sub-channel program number (with by_frequency)."
    )
    duration: int | None = Field(
        default=None, description="Stream duration limit (seconds)."
    )
    transcode: str | None = Field(
        default=None, description="EXTEND-model transcode profile."
    )


class RecordingRuleInput(BaseModel):
    """Input model for adding/modifying a DVR recording rule."""

    device_auth: str | None = Field(
        default=None,
        description="DeviceAuth (defaults to the client's configured value).",
    )
    series_id: str | None = Field(default=None, description="SeriesID to record.")
    recording_rule_id: str | None = Field(
        default=None, description="Existing rule ID (for change/delete)."
    )
    channel_only: str | None = Field(
        default=None, description="Pipe-separated virtual channel numbers."
    )
    team_only: str | None = Field(
        default=None, description="Pipe-separated team names."
    )
    recent_only: bool | None = Field(
        default=None, description="Record only recent episodes."
    )
    after_original_airdate_only: int | None = Field(
        default=None, description="UTC unixtime floor on original airdate."
    )
    date_time_only: int | None = Field(
        default=None, description="UTC unixtime of the single airing to record."
    )
    start_padding: int | None = Field(
        default=None, description="Start early (seconds)."
    )
    end_padding: int | None = Field(
        default=None, description="Continue past end (seconds)."
    )


class TunerControlInput(BaseModel):
    """Input model for a tuner-scoped hdhomerun_config get/set."""

    tuner: int = Field(description="Tuner index (0-based).")
    value: str | None = Field(
        default=None, description="Value to set (omit for a get)."
    )


class DoctorRunInput(BaseModel):
    """Input model for the doctor's full diagnostic run."""

    signal_channels: list[str] | None = Field(
        default=None, description="Virtual channels to sample for signal strength."
    )
    jellyfin_url: str | None = Field(
        default=None, description="Paired Jellyfin base URL for the tuner-count check."
    )
    jellyfin_api_key: str | None = Field(default=None, description="Jellyfin API key.")
    validate_device_auth_cloud: bool = Field(
        default=False, description="Validate DeviceAuth against the live cloud DVR API."
    )
