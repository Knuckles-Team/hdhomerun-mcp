# HDHomeRun MCP
## CLI or API | MCP | Agent

![PyPI - Version](https://img.shields.io/pypi/v/hdhomerun-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/hdhomerun-mcp)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/hdhomerun-mcp)
![PyPI - License](https://img.shields.io/pypi/l/hdhomerun-mcp)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/hdhomerun-mcp)

*Version: 1.0.0*

> **Documentation** — Installation, deployment, usage across the API, CLI, and MCP
> interfaces, the integrated A2A agent server, and guidance for provisioning the
> backing platform are maintained in the
> [official documentation](https://knuckles-team.github.io/hdhomerun-mcp/).

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Available MCP Tools](#available-mcp-tools)
- [Installation](#installation)
- [Usage](#usage)
- [MCP](#mcp)
- [Documentation](#documentation)

---

## Overview

**HDHomeRun MCP MCP Server + A2A Agent**

A complete client + MCP server + A2A agent for SiliconDust HDHomeRun network TV
tuners, covering all four of SiliconDust's documented interfaces: the **HTTP JSON
API** (device discovery, channel lineup, scan control), the **DVR API**
(SiliconDust cloud recording rules + local record-engine operations), the
**Discovery API** (local UDP broadcast on port 65001 + the cloud discovery
endpoint), and the binary **hdhomerun_config control protocol** (TCP port
65001 — a *different* wire protocol from the HTTP API, used for per-tuner
status/vstatus/streaminfo/tuning/filters). Also ships a `doctor` diagnostic
tool matching this fleet's `cm_doctor` convention.

This repository is actively maintained - Contributions are welcome!

## Key Features

- **All four HDHomeRun interfaces, one package** — HTTP JSON API, DVR API,
  Discovery API (local UDP + cloud), and the binary hdhomerun_config control
  protocol, each its own action-routed tool domain.
- **`doctor` diagnostics** — one call checks device reachability, firmware/model,
  tuner count vs. a paired Jellyfin instance, per-channel signal strength,
  DeviceAuth presence/validity, and discovery-cache freshness — pass/fail with an
  actionable next step per check.
- **Action-routed MCP tools** — each domain is exposed as a single MCP tool that routes
  to many underlying operations via an `action` argument, keeping the tool surface small.
- **Three interfaces, one package** — use it as a Python **API client**, an **MCP server**
  (`stdio` / `streamable-http` / `sse`), or a Pydantic-AI **A2A agent**.
- **`agent-utilities` native** — built on the shared framework (auth, action router,
  telemetry, governance) for fleet consistency.
- **Per-tool toggles** — enable or disable each tool domain with environment switches.
- **Enterprise-ready** — OTEL/Langfuse telemetry and optional Eunomia access governance.

## Available MCP Tools

Each tool is **action-routed**: pass an `action` and a JSON `params_json` payload. Tool
domains can be toggled on or off with the listed environment variable. The table below is
**auto-generated from the live server** by the `mcp-readme-table` pre-commit hook
(`python -m agent_utilities.mcp.readme_tools`) — do not edit it by hand.

<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (`MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `config_operations` | `CONFIGTOOL` | Query/control a tuner via the binary hdhomerun_config TCP control |
| `discovery_operations` | `DISCOVERYTOOL` | Discover HDHomeRun devices on the network — local UDP broadcast |
| `doctor_operations` | `DOCTORTOOL` | Diagnose an HDHomeRun deployment: device reachability, firmware/model, |
| `dvr_operations` | `DVRTOOL` | Manage the SiliconDust cloud DVR recording-rules API and the local |
| `http_operations` | `HTTPTOOL` | Query the HDHomeRun device HTTP JSON API — discover.json, channel |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>57 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `hdhomerun_abort_scan` | `HTTPTOOL` | POST /lineup.post?scan=abort — cancel an in-progress channel scan. |
| `hdhomerun_add_datetime_rule` | `DVRTOOL` | Add a DateTimeOnly-ChannelOnly rule (record one specific airing). |
| `hdhomerun_add_series_rule` | `DVRTOOL` | Add a Series (or Movie) recording rule for a SeriesID. |
| `hdhomerun_build_live_tv_url` | `DVRTOOL` | Build a record-engine buffered Live TV URL. |
| `hdhomerun_build_stream_url` | `HTTPTOOL` | Build a live-stream URL: /{auto\|tuner<n>}/{v<channel>\|ch<freq>[-<program>]}. |
| `hdhomerun_change_rule` | `DVRTOOL` | Modify a rule, or reprioritize it via ``after_recording_rule_id``. |
| `hdhomerun_check_device_auth` | `DOCTORTOOL` | Invoke the check_device_auth operation. |
| `hdhomerun_check_device_reachable` | `DOCTORTOOL` | Invoke the check_device_reachable operation. |
| `hdhomerun_check_discovery_cache_freshness` | `DOCTORTOOL` | Invoke the check_discovery_cache_freshness operation. |
| `hdhomerun_check_firmware_model` | `DOCTORTOOL` | Invoke the check_firmware_model operation. |
| `hdhomerun_check_signal_strength` | `DOCTORTOOL` | Briefly tune each channel and sample ss/snq/seq, then release the tuner. |
| `hdhomerun_check_tuner_count_vs_jellyfin` | `DOCTORTOOL` | Invoke the check_tuner_count_vs_jellyfin operation. |
| `hdhomerun_delete_recording` | `DVRTOOL` | POST <CmdURL from recorded_files.json> cmd=delete[&rerecord=1]. |
| `hdhomerun_delete_rule` | `DVRTOOL` | Delete a Series/Movie rule (by RecordingRuleID or SeriesID) or a |
| `hdhomerun_disable_lineup_location` | `CONFIGTOOL` | Disable the lineup-server connection (``/lineup/location disabled``). |
| `hdhomerun_discover_cloud` | `DISCOVERYTOOL` | GET http://ipv4-api.hdhomerun.com/discover[?DeviceID=<id>]. |
| `hdhomerun_discover_local_broadcast` | `DISCOVERYTOOL` | Broadcast a DISCOVER_REQ on UDP port 65001 and collect DISCOVER_RPY replies. |
| `hdhomerun_discover_local_targeted` | `DISCOVERYTOOL` | Send a DISCOVER_REQ directly to a known IP (works across VLANs). |
| `hdhomerun_get_channel` | `CONFIGTOOL` | ``/tuner<n>/channel`` — current ``<modulation>:<frequency>`` or ``none``. |
| `hdhomerun_get_channelmap` | `CONFIGTOOL` | ``/tuner<n>/channelmap`` — the configured channel-to-frequency map. |
| `hdhomerun_get_discover` | `HTTPTOOL` | GET /discover.json — FriendlyName/ModelNumber/FirmwareVersion/DeviceID/ |
| `hdhomerun_get_filter` | `CONFIGTOOL` | ``/tuner<n>/filter`` — the current PID filter (default ``0x0000-0x1FFF``). |
| `hdhomerun_get_help` | `CONFIGTOOL` | ``get help`` — the list of get/set item paths this device supports. |
| `hdhomerun_get_ir_target` | `CONFIGTOOL` | ``/ir/target`` — the configured IR-blaster target IP:port. |
| `hdhomerun_get_item` | `CONFIGTOOL` | ``hdhomerun_config <id> get <item>`` — raw get of any supported item path. |
| `hdhomerun_get_lineup` | `HTTPTOOL` | GET /lineup.{json,xml,m3u} — the channel list. |
| `hdhomerun_get_lineup_status` | `HTTPTOOL` | GET /lineup_status.json — scan state. |
| `hdhomerun_get_lockkey` | `CONFIGTOOL` | ``/tuner<n>/lockkey`` — current tuner lock owner (``none`` if unlocked). |
| `hdhomerun_get_program` | `CONFIGTOOL` | ``/tuner<n>/program`` — the current MPEG program (sub-channel) filter. |
| `hdhomerun_get_record_engine_status` | `DVRTOOL` | GET <storage engine BaseURL>/discover.json — FriendlyName/Version/ |
| `hdhomerun_get_recorded_files` | `DVRTOOL` | GET <StorageURL> (``recorded_files.json``) — the list of recordings |
| `hdhomerun_get_sys_copyright` | `CONFIGTOOL` | ``/sys/copyright`` — the firmware copyright notice. |
| `hdhomerun_get_sys_debug` | `CONFIGTOOL` | ``/sys/debug`` — device-wide debug info. |
| `hdhomerun_get_sys_features` | `CONFIGTOOL` | ``/sys/features`` — supported channelmaps/modulations for this device. |
| `hdhomerun_get_sys_model` | `CONFIGTOOL` | ``/sys/model`` — the device model name. |
| `hdhomerun_get_sys_version` | `CONFIGTOOL` | ``/sys/version`` — the firmware version string. |
| `hdhomerun_get_target` | `CONFIGTOOL` | ``/tuner<n>/target`` — the current UDP/RTP streaming target. |
| `hdhomerun_get_tuner_debug` | `CONFIGTOOL` | ``/tuner<n>/debug`` — extended tun/dev/ts/flt/net diagnostic counters. |
| `hdhomerun_get_tuner_status` | `CONFIGTOOL` | ``/tuner<n>/status`` — ``ch=... lock=... ss=... snq=... seq=... bps=... pps=...``. |
| `hdhomerun_get_tuner_streaminfo` | `CONFIGTOOL` | ``/tuner<n>/streaminfo`` — detected programs: ``<num>: <major>.<minor> [name]``. |
| `hdhomerun_get_tuner_vstatus` | `CONFIGTOOL` | ``/tuner<n>/vstatus`` — virtual-channel auth/CCI/CGMS status (model/firmware |
| `hdhomerun_list_recording_rules` | `DVRTOOL` | List all recording rules for the household's DeviceAuth(s). |
| `hdhomerun_parse_tuner_status` | `CONFIGTOOL` | Parse a ``ch=... lock=... ss=... snq=... seq=... bps=... pps=...`` status line. |
| `hdhomerun_poke_record_engine` | `DVRTOOL` | POST <storage engine BaseURL>/recording_events.post?sync. |
| `hdhomerun_restart_device` | `CONFIGTOOL` | ``/sys/restart self`` — reboot the HDHomeRun. Destructive; use with care. |
| `hdhomerun_run_doctor` | `DOCTORTOOL` | Run every check and return the aggregate report. |
| `hdhomerun_set_channel` | `CONFIGTOOL` | ``/tuner<n>/channel`` set — e.g. ``auto:651000000`` or ``auto:60``; ``none`` to stop. |
| `hdhomerun_set_channelmap` | `CONFIGTOOL` | ``/tuner<n>/channelmap`` set — e.g. ``us-bcast``/``us-cable``/``us-hrc``/``us-irc``. |
| `hdhomerun_set_filter` | `CONFIGTOOL` | ``/tuner<n>/filter`` set — e.g. ``0x0000-0x1FFF`` or a space-separated PID list. |
| `hdhomerun_set_ir_target` | `CONFIGTOOL` | ``/ir/target`` set — ``<ip>:<port>``. |
| `hdhomerun_set_item` | `CONFIGTOOL` | ``hdhomerun_config <id> set <item> <value>`` — raw set (implicit get-back). |
| `hdhomerun_set_lineup_location` | `CONFIGTOOL` | ``/lineup/location`` set — ``<countrycode>:<postcode>`` (or set to "disabled"). |
| `hdhomerun_set_lockkey` | `CONFIGTOOL` | ``/tuner<n>/lockkey`` set/clear — pass ``lock=False`` to release. |
| `hdhomerun_set_program` | `CONFIGTOOL` | ``/tuner<n>/program`` set — filter to a single program (sub-channel) number. |
| `hdhomerun_set_target` | `CONFIGTOOL` | ``/tuner<n>/target`` set — e.g. ``udp://192.168.1.100:5000`` or ``rtp://...``. |
| `hdhomerun_start_scan` | `HTTPTOOL` | POST /lineup.post?scan=start[&source=<Source>] — begin a channel scan. |
| `hdhomerun_stop_tuner` | `CONFIGTOOL` | Set ``/tuner<n>/channel none`` — release the tuner. |

</details>

_5 action-routed tool(s) · 57 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (**`intent` default** — the six verb-tools, granular set loaded on demand · `condensed` action-routed · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

## Installation

### Install with `uvx` (no install — run on demand)

```bash
uvx --from "hdhomerun-mcp[mcp]" hdhomerun-mcp      # MCP server (slim deps)
uvx --from "hdhomerun-mcp[agent]" hdhomerun-agent  # A2A agent server (full runtime)
```

> The `[mcp]` extra installs only the FastMCP/FastAPI MCP-server tooling
> (`agent-utilities[mcp]`) — it excludes the heavy agent runtime (the
> epistemic-graph engine, `pydantic-ai`, `dspy`, `llama-index`), so it is far
> smaller. Use `[agent]` only when you run the integrated agent.

### Install with `pip`

```bash
python -m pip install hdhomerun-mcp            # core (API client)
python -m pip install "hdhomerun-mcp[all]"     # + MCP server + A2A agent + telemetry
```

### Console scripts

After installation the following entry points are available on your `PATH`:

| Command | Description |
|---------|-------------|
| `hdhomerun-mcp` | Launch the MCP server |
| `hdhomerun-agent` | Launch the A2A agent server |

## Usage

### As a Python API client

```python
from hdhomerun_mcp.auth import get_client

client = get_client()  # reads HDHOMERUN_URL / HDHOMERUN_DEVICE_AUTH
info = client.get_discover()          # device identity + tuner count
lineup = client.get_lineup()          # channel list
stream_url = client.build_stream_url("24.1")  # http://<device>:5004/auto/v24.1
report = client.run_doctor()          # full health-check sweep
```

### As an MCP server (CLI)

```bash
# Local stdio (for IDEs)
hdhomerun-mcp

# Networked streamable-http
hdhomerun-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

### Calling an MCP tool

Tools are action-routed — pass an `action` plus a JSON `params_json` string:

```json
{
  "tool": "http_operations",
  "arguments": {
    "action": "discover",
    "params_json": "{}"
  }
}
```

## MCP

### Using as an MCP Server

The MCP Server can be run in `stdio` (local), `streamable-http` (networked), or
`sse` mode.

#### Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` |  |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | options: stdio, streamable-http, sse |
| `ENABLE_OTEL` | `True` |  |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:8080/api/public/otel` |  |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` |  |
| `EUNOMIA_TYPE` | `none` | options: none, embedded, remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `EUNOMIA_REMOTE_URL` | `http://eunomia-server:8000` |  |
| `HDHOMERUN_URL` | `http://hdhomerun.local` |  |
| `HDHOMERUN_DEVICE_AUTH` | `your_device_auth_here` |  |
| `HDHOMERUN_SSL_VERIFY` | `True` |  |
| `MCP_TOOL_MODE` | `condensed` |  |
| `HTTPTOOL` | `True` |  |
| `DISCOVERYTOOL` | `True` |  |
| `DVRTOOL` | `True` |  |
| `CONFIGTOOL` | `True` |  |
| `DOCTORTOOL` | `True` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_18 package + 15 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


*   `HDHOMERUN_URL`: The HDHomeRun device base URL (e.g. `http://10.0.132.114` or `http://hdhomerun.arpa`).
*   `HDHOMERUN_DEVICE_AUTH`: The device's `DeviceAuth` token (only needed for SiliconDust cloud DVR calls; rotates on reboot/firmware update — do not hardcode).

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the connector-focused `[mcp]` extra.** Examples use `hdhomerun-mcp[mcp]` to add
> FastMCP / FastAPI through `agent-utilities[mcp]`; the required Agent Utilities core
> still carries `epistemic-graph[full]`. The `[agent-runtime]` extra additionally
> enables model orchestration.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "hdhomerun-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "hdhomerun-mcp[mcp]",
        "hdhomerun-mcp"
      ],
      "env": {
        "MCP_TOOL_MODE": "intent",
        "CONFIGTOOL": "True",
        "DISCOVERYTOOL": "True",
        "DOCTORTOOL": "True",
        "DVRTOOL": "True",
        "HDHOMERUN_DEVICE_AUTH": "your_device_auth_here",
        "HDHOMERUN_SSL_VERIFY": "True",
        "HDHOMERUN_URL": "http://hdhomerun.local",
        "HTTPTOOL": "True"
      }
    }
  }
}
```

Runtime references require an alias-aware launcher such as GraphOS. Other
launchers must omit those entries and inject the resolved values through their
own runtime secret boundary.

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "hdhomerun-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "hdhomerun-mcp[mcp]",
        "hdhomerun-mcp",
        "--transport",
        "streamable-http",
        "--port",
        "8000"
      ],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "MCP_TOOL_MODE": "intent",
        "CONFIGTOOL": "True",
        "DISCOVERYTOOL": "True",
        "DOCTORTOOL": "True",
        "DVRTOOL": "True",
        "HDHOMERUN_DEVICE_AUTH": "your_device_auth_here",
        "HDHOMERUN_SSL_VERIFY": "True",
        "HDHOMERUN_URL": "http://hdhomerun.local",
        "HTTPTOOL": "True"
      }
    }
  }
}
```

Alternatively, connect to a pre-deployed Streamable-HTTP instance by `url`:

```json
{
  "mcpServers": {
    "hdhomerun-mcp": {
      "url": "http://localhost:8000/hdhomerun-mcp/mcp"
    }
  }
}
```

Run a reviewed container image as a least-privilege stdio child (no
listener or published port):

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  -e MCP_TOOL_MODE=intent \
  -e CONFIGTOOL=True \
  -e DISCOVERYTOOL=True \
  -e DOCTORTOOL=True \
  -e DVRTOOL=True \
  -e HDHOMERUN_DEVICE_AUTH=your_device_auth_here \
  -e HDHOMERUN_SSL_VERIFY=True \
  -e HDHOMERUN_URL=http://hdhomerun.local \
  -e HTTPTOOL=True \
  registry.example.invalid/hdhomerun-mcp@sha256:<digest> hdhomerun-mcp
```

For containerized network HTTP, supply an authenticated TLS ingress (or
direct server TLS), exact `MCP_ALLOWED_HOSTS`, and an exact trusted-proxy
CIDR policy through the operator-owned deployment profile. The generator
does not emit an unauthenticated non-loopback listener.

_Auto-generated from the code-read env surface (`MCP_TOOL_MODE` + package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`hdhomerun-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/hdhomerun-mcp/deployment/) has full,
copy-paste `mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://hdhomerun-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

## Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `knucklessg1/hdhomerun-mcp:mcp` | `--target mcp` | `hdhomerun-mcp[mcp]` — **slim**, no engine/`pydantic-ai`/`dspy`/`llama-index` | `hdhomerun-mcp` |
| `knucklessg1/hdhomerun-mcp:latest` | `--target agent` (default) | `hdhomerun-mcp[agent]` — **full** agent runtime + epistemic-graph engine | `hdhomerun-agent` |

```bash
docker build --target mcp   -t knucklessg1/hdhomerun-mcp:mcp    docker/   # slim MCP server
docker build --target agent -t knucklessg1/hdhomerun-mcp:latest docker/   # full agent
```

## Knowledge-graph database (`epistemic-graph`)

The full agent (`[agent]` / `:latest`) embeds the **epistemic-graph** engine (pulled in via
`agent-utilities[agent]`). For production — or to share one knowledge graph across multiple
agents — run **epistemic-graph as its own database container** and point the agent at it.
Deployment recipes (single-node + Raft HA), connection config, and the full database
architecture (with diagrams) are in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).
The slim `[mcp]` server does **not** require the database.

## Documentation

Full documentation is published to the GitHub Pages site and mirrored under `docs/`:

- [Documentation site](https://knuckles-team.github.io/hdhomerun-mcp/)
- [Overview](docs/overview.md)
- [Installation](docs/installation.md)
- [Usage](docs/usage.md)
- [Deployment](docs/deployment.md)
- [Platform](docs/platform.md)
- [Concept Registry](docs/concepts.md)
