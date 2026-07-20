---
name: hdhr-http-api-ops
skill_type: skill
description: >-
  Query and control an HDHomeRun tuner's HTTP JSON API via the hdhomerun-mcp
  MCP server — discover.json device identity, the lineup.json/lineup_status.json
  channel list and scan state, scan start/abort control, and building
  auto/tuner<n> live-stream URLs. Use when the agent needs the channel lineup,
  device firmware/tuner-count info, or to kick off/monitor a channel scan on a
  known device URL. Do NOT use for local network discovery of an unknown
  device (use hdhr-discovery-ops), DVR recording rules/record-engine calls
  (use hdhr-dvr-ops), per-tuner signal/status/tuning via the binary control
  protocol (use hdhr-tuner-control), or aggregate health checks (use hdhr-doctor).
license: MIT
tags: [hdhomerun, http-api, lineup, scan, mcp]
metadata:
  author: Genius
  version: '1.0.0'
---
# HDHomeRun HTTP API Operations

Direct access to the HDHomeRun **HTTP JSON API**
(https://info.hdhomerun.com/info/http_api) for a device at a known URL:
device identity, channel lineup, and scan control.

## When to use
- Fetch the channel lineup (`lineup.json`) or check scan progress
  (`lineup_status.json`).
- Start or abort a channel scan.
- Get device identity/firmware/tuner-count (`discover.json`).
- Build a live-stream URL for a virtual channel or RF frequency.

## When NOT to use
- You don't know the device's IP/hostname yet → `hdhr-discovery-ops` first.
- DVR recording rules or record-engine calls → `hdhr-dvr-ops`.
- Per-tuner signal strength / raw get-set (`status`, `vstatus`, `streaminfo`,
  `channel`, `filter`, `target`, `program`) → `hdhr-tuner-control` (a
  **different, binary** wire protocol on port 65001 — these items are
  **not** HTTP endpoints; confirmed 404 against a real FLEX 4K).
- A single pass/fail health report → `hdhr-doctor` (composes this skill).

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`hdhomerun-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `HDHOMERUN_URL` | ✅ | Device base URL, e.g. `http://10.0.132.114` or `http://hdhomerun.arpa` |
| `HDHOMERUN_SSL_VERIFY` | optional | TLS verification (local devices are plain HTTP) |
| `HTTPTOOL` | optional | Toggle this tool domain (default enabled) |

## Tools & actions
| Condensed tool | Actions |
|----------------|---------|
| `http_operations` | `discover`, `lineup`, `lineup_status`, `scan_start`, `scan_abort`, `stream_url` |

### Key parameters
- `lineup`: `{"fmt": "json"\|"xml"\|"m3u"}` (default `json`).
- `scan_start`: `{"source": "Antenna"|"Cable"}` (optional; omit to use the
  device's current source).
- `stream_url`: `{"channel", "tuner"?, "by_frequency"?, "program"?,
  "duration"?, "transcode"?}`. `transcode` (EXTEND models only) must be one of
  `heavy`/`mobile`/`internet540`/`internet480`/`internet360`/`internet240`.

## Recipes (`params_json`)
Get device identity:
```json
{"action": "discover", "params_json": "{}"}
```
List the channel lineup:
```json
{"action": "lineup", "params_json": "{\"fmt\": \"json\"}"}
```
Check/monitor a scan:
```json
{"action": "lineup_status", "params_json": "{}"}
```
Start a fresh antenna scan:
```json
{"action": "scan_start", "params_json": "{\"source\": \"Antenna\"}"}
```
Build a stream URL for a specific tuner and duration-limited test clip:
```json
{"action": "stream_url", "params_json": "{\"channel\": \"24.1\", \"tuner\": 1, \"duration\": 30}"}
```

## Gotchas
- `lineup_status.json` fields differ between idle
  (`ScanInProgress`,`ScanPossible`,`Source`,`SourceList`) and mid-scan
  (`ScanInProgress`:1,`Progress`,`Found`) — confirmed against a live FLEX 4K.
- The streaming port is **5004**, not the device's HTTP port (80) —
  `build_stream_url`/`stream_url` append it automatically; don't hardcode
  `:80` when constructing URLs by hand.
- `X-HDHomeRun-Error` response header codes 801-811 (Unknown Channel, System
  Busy, All Tuners In Use, …) explain a non-2xx stream request — surface the
  header value to the user rather than a bare status code.
- Starting a scan retunes every tuner in sequence; it will interrupt any
  in-progress recording/stream on the device. Confirm with the user before
  calling `scan_start` on a device that may be in active use.

## Related
- `hdhr-discovery-ops` — find the device's URL in the first place.
- `hdhr-tuner-control` — the binary hdhomerun_config protocol for per-tuner
  status/tuning (a separate wire protocol, not this HTTP surface).
- `hdhr-doctor` — composes this skill's `discover`/`lineup_status` into a
  full health report.
