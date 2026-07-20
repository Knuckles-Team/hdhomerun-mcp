---
name: hdhr-discovery-ops
skill_type: skill
description: >-
  Find HDHomeRun tuner devices on the network via the hdhomerun-mcp MCP
  server — local UDP broadcast/targeted discovery on port 65001, and the
  SiliconDust cloud discovery endpoint (http://ipv4-api.hdhomerun.com/discover)
  for when broadcast can't reach the device (different VLAN/subnet). Use when
  the agent doesn't yet know a device's IP, or a previously-known IP may have
  changed (DHCP re-lease). Do NOT use once you have a working device URL — go
  straight to hdhr-http-api-ops/hdhr-tuner-control; and do NOT use for DVR
  record-engine discovery (that is a per-record-engine discover.json call
  documented under hdhr-dvr-ops).
license: MIT
tags: [hdhomerun, discovery, udp, network, mcp]
metadata:
  author: Genius
  version: '1.0.0'
---
# HDHomeRun Discovery Operations

Locates HDHomeRun tuner devices per
https://info.hdhomerun.com/info/discovery_api — local UDP broadcast (port
65001) and the SiliconDust cloud discovery HTTP endpoint.

## When to use
- You don't know a device's current IP (first-time setup, DHCP re-lease).
- Local broadcast discovery fails (client on a different VLAN/subnet from the
  tuner) and you need the cloud fallback.
- You want to refresh the on-disk discovery cache before a doctor run.

## When NOT to use
- You already have a working device URL → go directly to `hdhr-http-api-ops`
  or `hdhr-tuner-control`.
- Discovering a DVR **record engine** (separate software/hardware, its own
  `discover.json`) → that's documented under `hdhr-dvr-ops`, not here.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`hdhomerun-mcp`** MCP server.
No credentials are required for discovery.

| Variable | Required | Notes |
|----------|----------|-------|
| `DISCOVERYTOOL` | optional | Toggle this tool domain (default enabled) |

## Tools & actions
| Condensed tool | Actions |
|----------------|---------|
| `discovery_operations` | `broadcast`, `targeted`, `cloud`, `cache` |

### Key parameters
- `broadcast`: `{"timeout": 2.0, "device_id": <int, optional wildcard match>}`.
- `targeted`: `{"ip": "<known ip>", "timeout": 2.0}` — sends the same UDP
  discover packet directly to a known address (works across VLANs where
  broadcast doesn't).
- `cloud`: `{"device_id": "<hex DeviceID, optional>"}` — omit to list every
  device SiliconDust has ever seen register from this account/network.
- `cache`: `{}` — reads the last cached discovery result (used by
  `hdhr-doctor`'s freshness check) without hitting the network.

## Recipes (`params_json`)
Broadcast discovery on the local subnet:
```json
{"action": "broadcast", "params_json": "{\"timeout\": 2.0}"}
```
Rediscover a device you know the (possibly stale) IP for:
```json
{"action": "targeted", "params_json": "{\"ip\": \"10.0.132.114\"}"}
```
Cloud discovery by DeviceID (works across VLANs, no broadcast needed):
```json
{"action": "cloud", "params_json": "{\"device_id\": \"10ACFCDE\"}"}
```

## Gotchas
- **Broadcast discovery legitimately returns an empty list on many
  networks** — most routers/switches don't forward UDP broadcast across
  VLAN boundaries. An empty `broadcast` result is not a bug; fall back to
  `cloud` (by DeviceID) or a `targeted` call to a last-known IP.
- The cloud endpoint (`http://ipv4-api.hdhomerun.com/discover`) resolves a
  device's **current LAN IP** by DeviceID — genuinely useful after a DHCP
  re-lease moved the device to a new address.
- Every successful discovery call refreshes
  `~/.config/agent-utilities/hdhomerun_discovery_cache.json`; `hdhr-doctor`'s
  `cache_freshness` check reads this file's age.

## Related
- `hdhr-http-api-ops` — once you have a URL, query the device's HTTP API.
- `hdhr-doctor` — the `cache_freshness`/`device_reachable` checks build on
  this skill's cache and `targeted`/`broadcast` calls.
