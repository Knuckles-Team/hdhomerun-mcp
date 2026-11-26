---
name: hdhr-discovery-ops
skill_type: skill
description: >-
  Find HDHomeRun tuners on the network via the hdhomerun-mcp MCP server: local
  UDP broadcast, targeted UDP to a known IP, or the SiliconDust cloud endpoint
  when broadcast cannot cross VLANs. Use when a device IP is unknown or may
  have changed. Do NOT use once a device URL works (hdhr-http-api-ops) or for
  DVR record engines (hdhr-dvr-ops).
license: MIT
tags: [hdhomerun, discovery, udp, network, mcp]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---
# HDHomeRun Discovery Operations

Scope: Find HDHomeRun tuner devices on the network via the hdhomerun-mcp MCP server — local UDP broadcast/targeted discovery on port 65001, and the SiliconDust cloud discovery endpoint (http://ipv4-api.hdhomerun.com/discover) for when broadcast can't reach the device (different VLAN/subnet). Use when the agent doesn't yet know a device's IP, or a previously-known IP may have changed (DHCP re-lease). Do NOT use once you have a working device URL — go straight to hdhr-http-api-ops/hdhr-tuner-control; and do NOT use for DVR record-engine discovery (that is a per-record-engine discover.json call documented under hdhr-dvr-ops).

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

## Steps

1. Run `hdhomerun_discover_local_broadcast` with `timeout` 2.0, and verify the result lists a device with a DeviceID and IP.
2. If the list is empty, run `hdhomerun_discover_cloud` with the known `device_id`, and verify the response carries the device LAN IP.
3. Confirm a stale IP with `hdhomerun_discover_local_targeted` and `ip`, and verify the device answers with the same DeviceID.
4. Read `hdhomerun_read_discovery_cache` to confirm what was stored, and verify the cached entry matches the device just found.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Broadcast returns an empty list | Router does not forward UDP broadcast across VLANs | Call `hdhomerun_discover_cloud` with the DeviceID, or `hdhomerun_discover_local_targeted` with the last known IP |
| Targeted discovery times out | The IP changed after a DHCP re-lease | Run `hdhomerun_discover_cloud` to get the current LAN IP and repeat the targeted call with it |
| Cloud discovery returns no device | DeviceID mistyped or device never registered | Omit `device_id` to list every device seen, and copy the correct hex DeviceID |

## Tools
One typed tool per discovery path; pass each argument by name.

| Tool | Use |
|------|-----|
| `hdhomerun_discover_local_broadcast` | Local UDP broadcast on port 65001 |
| `hdhomerun_discover_local_targeted` | Targeted UDP to a known IP |
| `hdhomerun_discover_cloud` | The SiliconDust cloud discovery endpoint |
| `hdhomerun_read_discovery_cache` | The on-disk cache of the last discovery |

### Key parameters
- `broadcast`: `{"timeout": 2.0, "device_id": <int, optional wildcard match>}`.
- `targeted`: `{"ip": "<known ip>", "timeout": 2.0}` — sends the same UDP
  discover packet directly to a known address (works across VLANs where
  broadcast doesn't).
- `cloud`: `{"device_id": "<hex DeviceID, optional>"}` — omit to list every
  device SiliconDust has ever seen register from this account/network.
- `cache`: `{}` — reads the last cached discovery result (used by
  `hdhr-doctor`'s freshness check) without hitting the network.

## Recipes (tool arguments)
Broadcast discovery on the local subnet:
```json
{"tool": "hdhomerun_discover_local_broadcast", "arguments": {"timeout": 2.0}}
```
Rediscover a device you know the (possibly stale) IP for:
```json
{"tool": "hdhomerun_discover_local_targeted", "arguments": {"ip": "10.0.132.114"}}
```
Cloud discovery by DeviceID (works across VLANs, no broadcast needed):
```json
{"tool": "hdhomerun_discover_cloud", "arguments": {"device_id": "10ACFCDE"}}
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
  `~/.config/scion-sdk/hdhomerun_discovery_cache.json`; `hdhr-doctor`'s
  `cache_freshness` check reads this file's age.

## Related
- `hdhr-http-api-ops` — once you have a URL, query the device's HTTP API.
- `hdhr-doctor` — the `cache_freshness`/`device_reachable` checks build on
  this skill's cache and `targeted`/`broadcast` calls.
