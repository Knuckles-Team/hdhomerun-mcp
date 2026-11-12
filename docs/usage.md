# Usage — API / CLI / MCP

`hdhomerun-mcp` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** the operator import, and as a **CLI**.

## As an MCP server

Once [deployed](deployment.md), the server registers one typed tool per HDHomeRun
operation, named `hdhomerun_<operation>`:

| Area | Tools |
|------|-------|
| HTTP API | `hdhomerun_get_discover`, `hdhomerun_get_lineup`, `hdhomerun_get_lineup_status`, `hdhomerun_start_scan`, `hdhomerun_abort_scan`, `hdhomerun_build_stream_url` |
| Discovery | `hdhomerun_discover_local_broadcast`, `hdhomerun_discover_local_targeted`, `hdhomerun_discover_cloud`, `hdhomerun_read_discovery_cache` |
| Cloud DVR | `hdhomerun_list_recording_rules`, `hdhomerun_add_series_rule`, `hdhomerun_add_datetime_rule`, `hdhomerun_change_rule`, `hdhomerun_delete_rule`, `hdhomerun_get_record_engine_status`, `hdhomerun_get_recorded_files`, `hdhomerun_poke_record_engine`, `hdhomerun_delete_recording`, `hdhomerun_build_live_tv_url` |
| Tuner control | `hdhomerun_get_item`, `hdhomerun_set_item`, `hdhomerun_get_help`, `hdhomerun_get_tuner_status`, `hdhomerun_set_channel`, `hdhomerun_stop_tuner`, `hdhomerun_get_lockkey`, `hdhomerun_set_lockkey`, and the other tuner and device items |
| Doctor | `hdhomerun_run_doctor`, `hdhomerun_check_device_reachable`, `hdhomerun_check_firmware_model`, `hdhomerun_check_tuner_count_vs_jellyfin`, `hdhomerun_check_signal_strength`, `hdhomerun_check_device_auth`, `hdhomerun_check_discovery_cache_freshness` |
| Knowledge graph | `hdhomerun_ingest_device`, `hdhomerun_ingest_lineup`, `hdhomerun_ingest_recording_rules` |

Every tool takes its arguments by name. See
`hdhomerun_mcp/skills/hdhr-*` for per-domain recipes and gotchas.

## As a Python API

```python
from hdhomerun_mcp.auth import get_client

client = (
    get_client()
)  # reads HDHOMERUN_URL / HDHOMERUN_DEVICE_AUTH / HDHOMERUN_TLS_PROFILE

# HTTP JSON API
info = client.get_discover()
lineup = client.get_lineup()
status = client.get_lineup_status()
client.start_scan(source="Antenna")
url = client.build_stream_url("24.1", tuner=0, duration=30)

# Discovery
devices = client.discover_local_broadcast(timeout=2.0)  # may be empty across VLANs
devices = client.discover_cloud(device_id="10ACFCDE")  # cloud fallback

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
