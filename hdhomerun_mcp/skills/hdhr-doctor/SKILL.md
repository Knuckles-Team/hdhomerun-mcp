---
name: hdhr-doctor
skill_type: skill
description: >-
  Run an actionable pass/fail health check on an HDHomeRun deployment via the
  hdhomerun-mcp MCP server's doctor tool — device reachability, firmware/model
  info, tuner count vs. a paired Jellyfin TunerHost, per-channel signal
  strength, DeviceAuth presence/validity, and discovery-cache freshness. Use
  when the agent must diagnose "Live TV isn't working" style problems, verify
  a fresh setup before wiring it into Jellyfin, or produce a status report for
  the user. Do NOT use for routine channel/tuning operations (use
  hdhr-http-api-ops/hdhr-tuner-control) — this skill is diagnostic-only and
  composes those, matching the fleet's cm_doctor convention (container-manager-mcp).
license: MIT
tags: [hdhomerun, doctor, diagnostics, health-check, mcp]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# HDHomeRun Doctor

A single diagnostic sweep over an HDHomeRun deployment, matching this fleet's
"doctor" pattern (e.g. `container-manager-mcp`'s `cm_doctor`). Every check
reports `pass`/`fail`/`warn`/`skip` plus an `action` (a concrete next step) on
anything short of a clean pass.

## When to use
- "Live TV isn't working" / "why are recordings missing" style troubleshooting.
- Before wiring a tuner into Jellyfin — confirm the device itself is healthy first.
- Producing a status report on an existing deployment (e.g. for a recurring check).

## When NOT to use
- Routine channel scan / lineup / tuning operations — this skill only reads
  status, it never scans/tunes except the opt-in `signal_strength` check
  (which briefly retunes and releases a tuner). Use `hdhr-http-api-ops` /
  `hdhr-tuner-control` for the operations themselves.
- Recording-rule management → `hdhr-dvr-ops`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`hdhomerun-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `HDHOMERUN_URL` | ✅ | Device to diagnose |
| `HDHOMERUN_DEVICE_AUTH` | optional | Enables deeper `device_auth` cloud validation |

## Tools
One typed tool per check; pass each argument by name.

| Tool | Check |
|------|-------|
| `hdhomerun_run_doctor` | The full suite (recommended) |
| `hdhomerun_check_device_reachable` | The device answers on its HTTP port |
| `hdhomerun_check_firmware_model` | Firmware and model against the supported set |
| `hdhomerun_check_tuner_count_vs_jellyfin` | Tuner count against the Live TV host |
| `hdhomerun_check_signal_strength` | Signal quality on the given channels |
| `hdhomerun_check_device_auth` | The household device authorization |
| `hdhomerun_check_discovery_cache_freshness` | Age of the discovery cache |

## Recipes (tool arguments)
Full sweep, no Jellyfin pairing, no invasive signal check:
```json
{"tool": "hdhomerun_run_doctor", "arguments": {}}
```
Full sweep including the Jellyfin tuner-count comparison:
```json
{"tool": "hdhomerun_run_doctor", "arguments": {"jellyfin_url": "http://jellyfin.example", "jellyfin_api_key": "<key>"}}
```
Full sweep including a signal-strength sample on two channels (interrupts
whatever tuner 0 is doing):
```json
{"tool": "hdhomerun_run_doctor", "arguments": {"signal_channels": ["24.1", "18.1"]}}
```
Just check DeviceAuth, and validate it against the live cloud API:
```json
{"tool": "hdhomerun_check_device_auth", "arguments": {"validate_cloud": true}}
```

## Gotchas
- `signal_strength` is the one check that **touches hardware** — it forces a
  brief tune on the tuner index you (implicitly, via the URL) or the default
  tuner own; don't run it against a device mid-recording without warning the
  user, and always pass a short, specific channel list rather than the whole
  lineup.
- `tuner_count_vs_jellyfin` needs the **Jellyfin API key**, obtainable from
  that server's own `get_keys` action if you don't already have one — see
  `hdhr-jellyfin-livetv-setup`'s Gotchas for the same caveat about
  jellyfin-mcp's dynamic router.
- A `skip` is not a failure — it means the check's prerequisite (Jellyfin
  pairing info, channels to sample) wasn't supplied, not that something is
  broken.
- `overall` is `fail` if any check failed, else `warn` if any warned, else `pass`.

## Related
- `hdhr-http-api-ops` / `hdhr-tuner-control` — the underlying operations this
  skill composes (`discover`, `lineup_status`-adjacent info, tuner status).
- `hdhr-jellyfin-livetv-setup` — the workflow this doctor's
  `tuner_count_vs_jellyfin` check verifies is still correctly wired.
