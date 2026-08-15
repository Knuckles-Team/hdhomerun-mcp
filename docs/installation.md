# Installation

`hdhomerun-mcp` is a standard Python package and a prebuilt container image.

## Requirements

- **Python 3.11 – 3.14**.
- A reachable HDHomeRun tuner on the local network (no credential needed for
  the HTTP API or hdhomerun_config protocol; `DeviceAuth` is only needed for
  the SiliconDust cloud DVR recording-rules API).

## From PyPI (recommended)

```bash
pip install hdhomerun-mcp
```

### Optional extras

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "hdhomerun-mcp[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "hdhomerun-mcp[agent]"` | Pydantic-AI agent + Logfire tracing |
| `all` | `pip install "hdhomerun-mcp[all]"` | Everything above |

## From source

```bash
git clone https://github.com/Knuckles-Team/hdhomerun-mcp.git
cd hdhomerun-mcp
pip install -e ".[all]"
```

## Docker

```bash
docker pull knucklessg1/hdhomerun-mcp:1.1.0
```
