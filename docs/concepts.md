# Concept Registry — hdhomerun-mcp

> **Prefix**: `CONCEPT:HDHR-*`
> **Version**: 0.1.0
> **Bridge**: ECO-4.0 ([Unified Toolkit Ingestion](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concepts.md), agent-utilities)

---

## Project-Specific Concepts

| Concept ID | Name | Description |
|------------|------|--------------|
| `CONCEPT:HDHR-http.api.json-interface` | HTTP API Operations | MCP tool domain `http` — discover.json/lineup.json/lineup_status.json/scan control/stream URLs (https://info.hdhomerun.com/info/http_api) |
| `CONCEPT:HDHR-discovery.network.device-location` | Discovery Operations | MCP tool domain `discovery` — local UDP broadcast (port 65001) + SiliconDust cloud discovery (https://info.hdhomerun.com/info/discovery_api) |
| `CONCEPT:HDHR-dvr.cloud.recording-rules` | DVR Operations | MCP tool domain `dvr` — SiliconDust cloud recording-rules API + local record-engine operations (https://info.hdhomerun.com/info/dvr_api) |
| `CONCEPT:HDHR-config.protocol.tuner-control` | Tuner Control Protocol | MCP tool domain `config` — the binary hdhomerun_config TCP control protocol (https://info.hdhomerun.com/info/hdhomerun_config), a different wire protocol from the HTTP API |
| `CONCEPT:HDHR-doctor.diagnostics.health-report` | Doctor Diagnostics | MCP tool domain `doctor` — device reachability, firmware/model, tuner-count-vs-Jellyfin, signal strength, DeviceAuth, discovery-cache-freshness checks |

## Cross-Project References (from agent-utilities)

| Concept ID | Name | Origin |
|------------|------|--------|
| `ECO-4.0` | Unified Toolkit Ingestion | agent-utilities |
| `ORCH-1.2` | Confidence-Gated Router | agent-utilities |
| `OS-5.1` | Prompt Injection Defense | agent-utilities |
