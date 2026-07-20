# Usage — API / CLI / MCP

`hdhomerun-mcp` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** you import, and as a **CLI**.

## As an MCP server

Once [deployed](deployment.md), the server registers five action-routed tool
modules, each independently togglable with a `*TOOL` environment flag:

| Tool | Toggle env var | Default | Actions |
|------|-----------------|---------|---------|
| `http_operations` | `HTTPTOOL` | `True` | `discover`, `lineup`, `lineup_status`, `scan_start`, `scan_abort`, `stream_url`, `ingest_device`, `ingest_lineup` |
| `discovery_operations` | `DISCOVERYTOOL` | `True` | `broadcast`, `targeted`, `cloud`, `cache` |
| `dvr_operations` | `DVRTOOL` | `True` | `list_rules`, `add_series_rule`, `add_datetime_rule`, `change_rule`, `delete_rule`, `record_engine_status`, `recorded_files`, `poke`, `delete_recording`, `live_tv_url`, `ingest_rules` |
| `config_operations` | `CONFIGTOOL` | `True` | `get_item`, `set_item`, `help`, `tuner_status`, `tuner_vstatus`, `tuner_streaminfo`, `tuner_debug`, `get_channel`, `set_channel`, `stop_tuner`, `get_channelmap`, `set_channelmap`, `get_filter`, `set_filter`, `get_program`, `set_program`, `get_target`, `set_target`, `get_lockkey`, `set_lockkey`, `get_ir_target`, `set_ir_target`, `set_lineup_location`, `disable_lineup_location`, `sys_model`, `sys_features`, `sys_version`, `sys_copyright`, `sys_debug`, `restart` |
| `doctor_operations` | `DOCTORTOOL` | `True` | `run`, `device_reachable`, `firmware_model`, `tuner_count_vs_jellyfin`, `signal_strength`, `device_auth`, `cache_freshness` |

Every tool takes `action` plus a JSON string `params_json`. See
`hdhomerun_mcp/skills/hdhr-*` for per-domain recipes and gotchas.

## As a Python API

```python
from hdhomerun_mcp.auth import get_client

client = get_client()  # reads HDHOMERUN_URL / HDHOMERUN_DEVICE_AUTH / HDHOMERUN_SSL_VERIFY

# HTTP JSON API
info = client.get_discover()
lineup = client.get_lineup()
status = client.get_lineup_status()
client.start_scan(source="Antenna")
url = client.build_stream_url("24.1", tuner=0, duration=30)

# Discovery
devices = client.discover_local_broadcast(timeout=2.0)     # may be empty across VLANs
devices = client.discover_cloud(device_id="10ACFCDE")       # cloud fallback

# hdhomerun_config binary control protocol (TCP :65001)
tuner_status = client.get_tuner_status(0)
parsed = client.parse_tuner_status(tuner_status)

# DVR (cloud recording rules)
rules = client.list_recording_rules()

# Doctor
report = client.run_doctor(signal_channels=["24.1"])
```

## As a CLI

```bash
export HDHOMERUN_URL="http://10.0.132.114"
export HDHOMERUN_DEVICE_AUTH="your_device_auth"   # only needed for DVR cloud calls
hdhomerun-mcp --transport stdio
```
