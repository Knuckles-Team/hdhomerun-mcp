---
name: hdhr-dvr-ops
skill_type: skill
description: >-
  Manage HDHomeRun DVR recording rules (SiliconDust cloud API,
  api.hdhomerun.com/api/recording_rules) and local record-engine operations
  (status, recorded_files listing, poke-after-rule-change, delete-a-recording,
  buffered Live TV URLs) via the hdhomerun-mcp MCP server. Use when the agent
  must add/change/delete a Series/Movie/DateTimeOnly recording rule, list or
  delete recordings, or build a Live TV playback URL against a SiliconDust
  cloud DVR (Scribe/Server/Connect+storage) setup. Do NOT use for tuner-only
  hardware with no DVR/record-engine (this package's own test device is
  tuner-only) — that's a hard prerequisite failure, not a usage error.
license: MIT
tags: [hdhomerun, dvr, recording-rules, record-engine, mcp]
metadata:
  author: Genius
  version: '1.0.0'
---
# HDHomeRun DVR Operations

Two distinct DVR surfaces per https://info.hdhomerun.com/info/dvr_api:
SiliconDust's **cloud recording-rules API**, and the **local record-engine**
API (a separate box/software from the tuner — HDHomeRun SCRIBE, SERVIO, or
desktop/NAS record-engine software).

## When to use
- Add/change/reprioritize/delete a recording rule (Series, Movie, or a
  one-off DateTimeOnly-ChannelOnly rule).
- List or delete recordings from a record engine's `recorded_files.json`.
- Poke the record engine after a rule change so it recomputes tasks.
- Build a buffered Live TV URL against the record engine.

## When NOT to use
- The household has tuner-only hardware with no DVR/record-engine present —
  the cloud recording-rules calls will still work (cloud-side), but
  `record_engine_status`/`recorded_files`/`poke`/`delete_recording`/
  `live_tv_url` all require a **local record-engine BaseURL**, which won't
  exist. Confirm a record engine is on the network first (its own
  `discover.json`, distinct from a tuner's).
- Direct channel lineup / tuner scan → `hdhr-http-api-ops`.
- Per-tuner signal/status → `hdhr-tuner-control`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`hdhomerun-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `HDHOMERUN_DEVICE_AUTH` | ✅ (rule actions) | Concatenation of every household tuner's `DeviceAuth` (from each tuner's `discover.json`) |
| `DVRTOOL` | optional | Toggle this tool domain (default enabled) |

## Tools & actions
| Condensed tool | Actions |
|----------------|---------|
| `dvr_operations` | `list_rules`, `add_series_rule`, `add_datetime_rule`, `change_rule`, `delete_rule`, `record_engine_status`, `recorded_files`, `poke`, `delete_recording`, `live_tv_url` |

### Key parameters
- Rule actions share `device_auth` (optional — defaults to the client's
  configured `HDHOMERUN_DEVICE_AUTH`), `series_id`/`recording_rule_id`,
  `channel_only`, `team_only`, `recent_only`, `after_original_airdate_only`,
  `start_padding`/`end_padding` (seconds), and `date_time_only` (unixtime) for
  one-off rules.
- `record_engine_status`/`poke` take `{"storage_engine_base_url"}`.
- `recorded_files` takes `{"storage_url"}` (from `record_engine_status`'s
  `StorageURL` field).
- `delete_recording` takes `{"cmd_url", "rerecord"?}` — `cmd_url` comes from
  the recording's own entry in `recorded_files`, **must be POSTed** (GET is
  rejected with 400).
- `live_tv_url` takes `{"storage_engine_base_url", "channel", "client_id",
  "session_id"}` — `client_id` stable per app instance, `session_id` unique
  per new channel request.

## Recipes (`params_json`)
Add a series recording rule:
```json
{"action": "add_series_rule", "params_json": "{\"series_id\": \"11579711\", \"recent_only\": true}"}
```
Add a one-off DateTimeOnly-ChannelOnly rule:
```json
{"action": "add_datetime_rule", "params_json": "{\"series_id\": \"11579711\", \"date_time_only\": 1751328000, \"channel_only\": \"24.1\"}"}
```
List current rules:
```json
{"action": "list_rules", "params_json": "{}"}
```
Delete a recording (no re-record):
```json
{"action": "delete_recording", "params_json": "{\"cmd_url\": \"<CmdURL from recorded_files>\"}"}
```

## Gotchas
- `DeviceAuth` **rotates** (SiliconDust tokens are short-lived and rotate on
  reboot/firmware update) — never hardcode it; always resolve it fresh from
  the tuner's own `discover.json` (or `HDHOMERUN_DEVICE_AUTH`/config), which
  is exactly what this client's `get_client()`/`_require_device_auth` does.
- A household with multiple tuners must **concatenate** every tuner's
  `DeviceAuth` for the cloud rules API to see the whole household correctly.
- `delete_recording` **must be a POST** — an HTTP GET on the `CmdURL` is
  rejected with 400 Bad Request (documented API behavior, not a bug).
- After any rule add/change/delete, call `poke` so the record engine
  recomputes upcoming tasks promptly (it will eventually notice on its own,
  but poke makes the UI feel instant).

## Related
- `hdhr-http-api-ops` — the tuner-side `discover.json`/lineup used to source
  `channel_only` values and per-tuner `DeviceAuth`.
- `hdhr-jellyfin-livetv-setup` — the end-to-end workflow for wiring a tuner
  into Jellyfin Live TV (a different consumption path from the SiliconDust
  cloud DVR covered here).
- `hdhr-doctor` — `device_auth` check validates the DeviceAuth this skill needs.
