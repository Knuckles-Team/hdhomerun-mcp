---
name: hdhr-jellyfin-livetv-setup
skill_type: workflow
description: >-
  Wire a real HDHomeRun tuner into Jellyfin Live TV end-to-end: add it as a
  TunerHost, add free XMLTV guide data for users without a Schedules Direct
  subscription, map the tuner's lineup to XMLTV channels by call sign/
  GuideNumber, and validate live playback. Grounded in a verified real setup
  (HDHomeRun FLEX 4K + Jellyfin 10.11.11, Austin TX OTA market) — not
  speculative. Use when the agent must onboard an HDHomeRun into Jellyfin
  Live TV or diagnose why channels/guide data aren't showing up. Do NOT use
  this to fix jellyfin-mcp's own dynamic-router bugs (out of scope; documented
  as a Gotcha with a workaround) or for SiliconDust cloud DVR recording rules
  (use hdhr-dvr-ops instead — this workflow is about Jellyfin's own Live TV/DVR).
license: MIT
tags: [hdhomerun, jellyfin, live-tv, xmltv, workflow]
metadata:
  author: Genius
  version: '1.0.0'
---
# HDHomeRun -> Jellyfin Live TV Setup

A verified, four-step workflow to wire an HDHomeRun tuner into Jellyfin Live
TV, including free (non-Schedules-Direct) guide data. Every step below was
run against a real HDHomeRun FLEX 4K (DeviceID `10ACFCDE`) and a real
Jellyfin 10.11.11 server serving an Austin, TX OTA market.

## When to use
- Onboarding a new HDHomeRun tuner into an existing Jellyfin server.
- The user has no Schedules Direct subscription and wants free XMLTV guide data.
- Diagnosing "channels show up but no guide data" or "tuner add fails" issues.

## When NOT to use
- Fixing the `jellyfin-mcp` dynamic-router bug itself (see Gotchas) — out of
  scope for this package; file/track it against `jellyfin-mcp`.
- SiliconDust cloud DVR recording rules — that's Jellyfin's *own* DVR
  scheduling once Live TV is wired (Jellyfin `/LiveTv/Timers` etc.), a
  separate system from the SiliconDust cloud rules in `hdhr-dvr-ops`.

## Prerequisites
- A reachable HDHomeRun tuner (`hdhr-http-api-ops`'s `discover` action
  confirms this) with its `DeviceID` and `TunerCount` known.
- A Jellyfin server with an API key (`X-Emby-Token`). If you don't have one,
  the `jellyfin-mcp` MCP server's `jell__system` tool exposes a `get_keys`
  action that returns one.
- Optional: a free XMLTV guide URL for US OTA/diginet coverage — verified
  working: `https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz`
  (confirmed to include call-sign-matched entries like `KVUE-DT`, `KLRU-DT`,
  `KEYE-DT`, `KAKW-DT`, `KNVA-DT`, `KBVO-DT`/`CD`, `KION-DT`).

## Execution
Steps 1 and 2 are independent of each other and can run in parallel; step 3
depends on both (it needs the tuner's lineup from step 1 and the XMLTV
channel list pulled in by step 2); step 4 depends on step 3.

- **In parallel:** Step 1 (add tuner host) and Step 2 (add XMLTV guide data).
- **Then:** Step 3 (channel mapping), once both above have completed.
- **Then:** Step 4 (validate playback).

If graph-os is reachable, offload the whole DAG via
`graph_orchestrate action=execute_workflow` (or the `kg-delegate` skill) for
true parallel/swarm execution. Otherwise execute the steps natively in
dependency order: run steps with no unmet `depends_on` in parallel, then
their dependents.

### Step 1: add_tuner_host [depends_on: none]
`POST /LiveTv/TunerHosts` on the Jellyfin server, authenticated via the
`X-Emby-Token` header:
```json
{
  "Type": "hdhomerun",
  "Url": "http://10.0.132.114",
  "DeviceId": "10ACFCDE",
  "FriendlyName": "HDHomeRun FLEX 4K",
  "TunerCount": 4,
  "AllowHWTranscoding": true,
  "AllowStreamSharing": true,
  "IgnoreDts": true
}
```
Prefer `http://hdhomerun.arpa` (a stable hostname) over the raw device IP
when one is available on your network — the IP is often a DHCP lease that
can change; `Url` accepts either.

### Step 2: add_guide_data [depends_on: none]
For users without Schedules Direct, add a free XMLTV source:
`POST /LiveTv/ListingProviders`:
```json
{"Type": "xmltv", "Path": "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz"}
```

### Step 3: map_channels [depends_on: add_tuner_host, add_guide_data]
Match the tuner's lineup (`hdhr-http-api-ops`'s `lineup` action —
`GuideNumber`/`GuideName`) to the XMLTV feed's `<channel>` entries by call
sign. Jellyfin does most of this automatically once both the tuner and the
XMLTV listing provider are configured, matching on call sign / channel
number where the feed provides it; verify the mapping in Jellyfin's Live TV
setup UI (or `GET /LiveTv/Channels`) rather than assuming a 1:1 match,
especially for diginet subchannels (see Gotchas).

### Step 4: validate_playback [depends_on: map_channels]
Confirm actual end-to-end playback, not just that the channel list populated:
- `GET /LiveTv/Channels` to confirm the channel list is non-empty and guide
  data (`CurrentProgram`) is attached where the XMLTV feed covers it.
- Open a live stream via the `open_live_stream` flow (or directly
  `GET /LiveTv/LiveStreamFiles/{streamId}/stream.ts` after opening a stream)
  and confirm bytes are actually flowing, not just a 200 response with an
  empty body.

## Gotchas
- **`jellyfin-mcp`'s `add_tuner_host` action can 404 against a real server**
  even though the underlying REST endpoint works fine. Confirmed against a
  real Jellyfin 10.11.11 instance: the actual endpoint (verified via that
  server's own authenticated OpenAPI spec at `/api-docs/openapi.json`) is
  `POST /LiveTv/TunerHosts` and it succeeds via direct authenticated REST —
  the 404 looks like a request-building bug in `jellyfin-mcp`'s dynamic
  router for this specific action. **Do not go fix `jellyfin-mcp`** (out of
  scope here) — the workaround is to call the REST endpoint directly with
  that MCP server's own API key (its `get_keys` action) whenever the dynamic
  router 404s on this action.
- **Free XMLTV guide data is a deliberate, acceptable tradeoff, not a bug.**
  Major-network affiliates (`KVUE-DT`, `KLRU-DT`, `KEYE-DT`, `KAKW-DT`,
  `KNVA-DT`, `KBVO-DT`/`CD`) map reliably from the epgshare01 US-LOCALS feed.
  **Diginet subchannels** (Bounce/Grit/Laff/CourtTV/Defy/Dabl/Nosey/ION/
  Mystery/Outlaw/Busted/ShopLC/T-Mundo/PBSKids, etc.) are inherently less
  reliably covered on free XMLTV than on a paid Schedules Direct
  subscription — when the user has explicitly chosen "free" over Schedules
  Direct, treat sparse/missing diginet guide data as expected, not a defect
  to chase.
- `DeviceAuth` (used elsewhere for SiliconDust cloud DVR calls) is **not**
  needed for this workflow — Jellyfin Live TV talks to the tuner's plain
  HTTP API, no device credential required.
- Verify playback with an actual byte-flowing stream request, not just a
  200 from the channel list — a channel can list correctly while tuning
  still fails (all tuners busy, weak signal, etc.); cross-check with
  `hdhr-doctor`'s `signal_strength` check if playback fails.

## Related
- `hdhr-http-api-ops` — source of the tuner's `DeviceId`/`TunerCount`/lineup used in steps 1 and 3.
- `hdhr-doctor` — `tuner_count_vs_jellyfin` check verifies this workflow's
  step 1 stayed correctly wired over time (e.g. after a tuner firmware
  update changes `TunerCount`).
- `hdhr-dvr-ops` — the separate SiliconDust cloud DVR recording-rules API
  (not Jellyfin's own DVR, which this workflow enables).

**Execution:** If graph-os is reachable, offload the whole DAG via
`graph_orchestrate action=execute_workflow` (or the `kg-delegate` skill) for
true parallel/swarm execution. Otherwise execute the steps natively in
dependency order: run steps with no unmet `depends_on` in parallel, then
their dependents.
