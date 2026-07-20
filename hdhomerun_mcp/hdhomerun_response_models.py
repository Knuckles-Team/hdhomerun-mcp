#!/usr/bin/python
"""Pydantic response models for HDHomeRun MCP API payloads.

Documentation/validation aids describing the JSON shapes returned by the
device HTTP API and the doctor diagnostics; the api client methods return
plain dicts (the device's own JSON), so these are opt-in for callers that
want typed parsing.
"""

from typing import Any

from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    """``discover.json`` — basic device identity/capability info."""

    FriendlyName: str | None = None
    ModelNumber: str | None = None
    FirmwareName: str | None = None
    FirmwareVersion: str | None = None
    DeviceID: str | None = None
    DeviceAuth: str | None = None
    BaseURL: str | None = None
    LineupURL: str | None = None
    TunerCount: int | None = None


class LineupChannel(BaseModel):
    """One entry from ``lineup.json``."""

    GuideNumber: str | None = None
    GuideName: str | None = None
    VideoCodec: str | None = None
    AudioCodec: str | None = None
    HD: int | None = None
    Favorite: int | None = None
    DRM: int | None = None
    URL: str | None = None


class LineupStatus(BaseModel):
    """``lineup_status.json`` — scan state (idle or in-progress)."""

    ScanInProgress: int | None = None
    ScanPossible: int | None = None
    Source: str | None = None
    SourceList: list[str] | None = None
    Progress: int | None = None
    Found: int | None = None


class RecordingRule(BaseModel):
    """One entry from the DVR ``recording_rules`` API."""

    RecordingRuleID: str | None = None
    SeriesID: str | None = None
    Title: str | None = None
    Synopsis: str | None = None
    ImageURL: str | None = None
    ChannelOnly: str | None = None
    TeamOnly: str | None = None
    AfterOriginalAirdateOnly: int | None = None
    DateTimeOnly: int | None = None
    Priority: int | None = None
    StartPadding: int | None = None
    EndPadding: int | None = None


class TunerStatus(BaseModel):
    """Parsed ``/tuner<n>/status`` line: ch/lock/ss/snq/seq/bps/pps."""

    ch: str | None = None
    lock: str | None = None
    ss: str | None = None
    snq: str | None = None
    seq: str | None = None
    bps: str | None = None
    pps: str | None = None


class DoctorCheckResult(BaseModel):
    """One check result from the doctor diagnostic suite."""

    check: str = Field(description="Check name.")
    status: str = Field(description="'pass' | 'fail' | 'warn' | 'skip'.")
    detail: Any | None = Field(
        default=None, description="Check-specific detail payload."
    )
    action: str | None = Field(
        default=None, description="Actionable next step (present on fail/warn)."
    )


class DoctorReport(BaseModel):
    """Aggregate result of ``run_doctor()``."""

    overall: str = Field(description="'pass' | 'fail' | 'warn'.")
    checks: list[DoctorCheckResult] = Field(default_factory=list)
