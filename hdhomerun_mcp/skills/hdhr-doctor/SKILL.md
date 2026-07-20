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
  author: Genius
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
| `DOCTORTOOL` | optional | Toggle this tool domain (default enabled) |

## Tools & actions
| Condensed tool | Actions |
|----------------|---------|
| `doctor_operations` | `run` (full suite, recommended), or a single check: `device_reachable`, `firmware_model`, `tuner_count_vs_jellyfin`, `signal_strength`, `device_auth`, `cache_freshness` |

### Checks performed by `run`
1. **device_reachable** — `GET discover.json` succeeds.
2. **firmware_model** — reports ModelNumber/FirmwareName/FirmwareVersion; warns
   if either field is missing (very old/legacy firmware).
3. **tuner_count_vs_jellyfin** — compares the device's `TunerCount` to a
   paired Jellyfin `TunerHost` entry matched by `DeviceId`; **skipped** (not
   failed) when no `jellyfin_url`/`jellyfin_api_key` is supplied.
4. **signal_strength** — for each requested channel: briefly tunes it, reads
   `ss`/`snq`/`seq` via the control protocol, then releases the tuner; warns
   on `ss < 40`. **Skipped** when no channels are requested (it is invasive —
   it uses a tuner — so it is opt-in).
5. **device_auth** — DeviceAuth present in `discover.json`; optionally
   validated live against the cloud recording-rules API.
6. **discovery_cache_freshness** — age of
   `~/.config/agent-utilities/hdhomerun_discovery_cache.json`; warns past 24h.

## Recipes (`params_json`)
Full sweep, no Jellyfin pairing, no invasive signal check:
```json
{"action": "run", "params_json": "{}"}
```
Full sweep including the Jellyfin tuner-count comparison:
```json
{"action": "run", "params_json": "{\"jellyfin_url\": \"http://jellyfin.arpa\", \"jellyfin_api_key\": \"<key>\"}"}
```
Full sweep including a signal-strength sample on two channels (interrupts
whatever tuner 0 is doing):
```json
{"action": "run", "params_json": "{\"signal_channels\": [\"24.1\", \"18.1\"]}"}
```
Just check DeviceAuth, and validate it against the live cloud API:
```json
{"action": "device_auth", "params_json": "{\"validate_cloud\": true}"}
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
