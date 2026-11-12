---
name: hdhr-tuner-control
skill_type: skill
description: >-
  Query and control individual HDHomeRun tuners via the binary
  hdhomerun_config TCP control protocol (port 65001 — a DIFFERENT wire
  protocol from the HTTP JSON API) through the hdhomerun-mcp MCP server:
  per-tuner status/vstatus/streaminfo/debug, channel/channelmap/filter/program/
  target get-set, tuner lock, IR target, lineup location, and /sys/ firmware
  info. Use when the agent needs raw signal metrics (ss/snq/seq), to tune a
  physical RF channel directly, set a PID/program filter, or stream to a UDP/
  RTP target — the same operations the official hdhomerun_config CLI performs.
  Do NOT use for the channel lineup or HTTP streaming URLs (use
  hdhr-http-api-ops) or DVR recording rules (use hdhr-dvr-ops).
license: MIT
tags: [hdhomerun, control-protocol, tuner, signal, mcp]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# HDHomeRun Tuner Control (hdhomerun_config protocol)

Speaks the same binary get/set protocol as the official `hdhomerun_config` CLI
(https://info.hdhomerun.com/info/hdhomerun_config) — TCP port 65001, TLV
framing, CRC32-checked packets. **This is not the HTTP JSON API** — none of
these item paths (`/tuner<n>/status`, `vstatus`, `streaminfo`, `debug`,
`channel`, `target`, `program`, `filter`) exist as HTTP endpoints; confirmed
by probing a live FLEX 4K (every one returned HTTP 404). They exist only over
this control protocol.

## When to use
- Read raw signal metrics for a tuner (`ss`/`snq`/`seq`/`bps`/`pps`).
- Tune a physical RF channel/frequency directly (not via the HTTP stream URL).
- Set a PID filter, sub-channel program filter, or a UDP/RTP streaming target.
- Query/set the channelmap, IR target, lineup location, or `/sys/*` firmware info.
- Lock/unlock a tuner, or reboot the device (`restart`).

## When NOT to use
- Channel lineup, HTTP scan control, or building `/auto/v<ch>` stream URLs →
  `hdhr-http-api-ops`.
- DVR recording rules / record-engine → `hdhr-dvr-ops`.
- Finding the device's IP in the first place → `hdhr-discovery-ops`.
- A one-shot pass/fail read on several channels → `hdhr-doctor`'s
  `signal_strength` check (it already drives this protocol for you).

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`hdhomerun-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `HDHOMERUN_URL` | ✅ | Used to derive the control-protocol IP (host portion) |

**Supported item paths are device/firmware-dependent** — always call `help`
first on a device you haven't used before rather than assuming an item is
supported (e.g. `vstatus` and `get`-ting `lineup/location` both returned
"ERROR: unknown getset variable" on this package's own live FLEX 4K).

## Tools
One typed tool per control item; pass each argument by name.

| Area | Tools |
|------|-------|
| Raw items | `hdhomerun_get_item`, `hdhomerun_set_item`, `hdhomerun_get_help` |
| Tuner state | `hdhomerun_get_tuner_status`, `hdhomerun_get_tuner_vstatus`, `hdhomerun_get_tuner_streaminfo`, `hdhomerun_get_tuner_debug`, `hdhomerun_parse_tuner_status` |
| Tuning | `hdhomerun_get_channel`, `hdhomerun_set_channel`, `hdhomerun_stop_tuner`, `hdhomerun_get_channelmap`, `hdhomerun_set_channelmap` |
| Streams | `hdhomerun_get_filter`, `hdhomerun_set_filter`, `hdhomerun_get_program`, `hdhomerun_set_program`, `hdhomerun_get_target`, `hdhomerun_set_target` |
| Locking | `hdhomerun_get_lockkey`, `hdhomerun_set_lockkey` |
| Device | `hdhomerun_get_ir_target`, `hdhomerun_set_ir_target`, `hdhomerun_set_lineup_location`, `hdhomerun_disable_lineup_location`, `hdhomerun_get_sys_model`, `hdhomerun_get_sys_features`, `hdhomerun_get_sys_version`, `hdhomerun_get_sys_copyright`, `hdhomerun_get_sys_debug`, `hdhomerun_restart_device` |

### Key parameters
- Tuner-scoped tools take `{"tuner": <0-based index>}`.
- `set_channel`: `{"tuner", "modulation": "auto", "freq_or_channel": "60"}`
  (RF channel number or Hz frequency — **not** a virtual channel like `24.1`).
- `set_program`: `{"tuner", "program_number"}` — sub-channel MPEG filter.
- `set_target`: `{"tuner", "target": "udp://<ip>:<port>"}`.
- `get_item`/`set_item`: raw escape hatch — `{"name": "/tuner0/channelmap",
  "value"?}` for any item not covered by a typed tool.

## Recipes (tool arguments)
Discover what a device supports before assuming an item exists:
```json
{"tool": "hdhomerun_get_help", "arguments": {}}
```
Read current tuner status (signal strength etc.):
```json
{"tool": "hdhomerun_get_tuner_status", "arguments": {"tuner": 0}}
```
Tune to a physical RF channel:
```json
{"tool": "hdhomerun_set_channel", "arguments": {"tuner": 0, "modulation": "auto", "freq_or_channel": "60"}}
```
Release the tuner when done:
```json
{"tool": "hdhomerun_stop_tuner", "arguments": {"tuner": 0}}
```
Read firmware/model info:
```json
{"tool": "hdhomerun_get_sys_model", "arguments": {}}
```

## Gotchas
- **This is a different port-65001 wire protocol from UDP discovery** — same
  packet framing (type/length/TLV payload/CRC32), different packet types
  (`GETSET_REQ`/`GETSET_RPY` vs `DISCOVER_REQ`/`DISCOVER_RPY`) and it runs
  over **TCP**, not UDP.
- `set_channel` takes an **RF channel number or frequency in Hz**, not a
  virtual `GuideNumber` like `24.1` — to tune a virtual channel, use
  `hdhr-http-api-ops`'s stream URL instead, which resolves it automatically.
- Always `stop_tuner` (set channel to `none`) after a diagnostic tune —
  otherwise the tuner stays allocated and unavailable to other clients.
- `restart` reboots the whole HDHomeRun unit — confirm with the user before
  calling it; it will interrupt every active stream/recording.
- Item support is **firmware/model-dependent** — a get/set on an
  unsupported item returns an error string (`HDHomeRunControlError`), not a
  crash; check `help`'s output first on an unfamiliar device.

## Related
- `hdhr-http-api-ops` — channel lineup and virtual-channel stream URLs.
- `hdhr-doctor` — `signal_strength` check drives this skill's `tuner_status`
  under the hood after briefly tuning each requested channel.
