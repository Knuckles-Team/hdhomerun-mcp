# Deployment

This page covers running `hdhomerun-mcp` as long-lived servers.

> `hdhomerun-mcp` ships both an **MCP server** (console script `hdhomerun-mcp`) and an
> **A2A agent server** (console script `hdhomerun-agent`).

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`hdhomerun-mcp` exposes its MCP server (console script `hdhomerun-mcp`) four ways. Pick the
row that matches where the server runs relative to your MCP client, then copy the
matching `mcp_config.json` below.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container / uv | `stdio` or `streamable-http` | Docker / Podman / uv on this host | `command` or `url` |
| 4 | Remote URL | `streamable-http` | a remote host behind Caddy | `url` |

### 1. stdio (local subprocess)

```json
{
  "mcpServers": {
    "hdhomerun-mcp": {
      "command": "uvx",
      "args": ["--from", "hdhomerun-mcp[mcp]", "hdhomerun-mcp"],
      "env": {
        "HDHOMERUN_URL": "https://service.example.com",
        "HDHOMERUN_DEVICE_AUTH": "your_token"
      }
    }
  }
}
```

### 2. Streamable-HTTP (local process)

```bash
uvx --from "hdhomerun-mcp[mcp]" hdhomerun-mcp --transport streamable-http --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health        # {"status":"OK"}
```

Connect to the running process by URL:

```json
{
  "mcpServers": {
    "hdhomerun-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 3. Local container / uv

Launch a container directly from `mcp_config.json` (swap `docker` for `podman` for a
daemonless runtime):

```json
{
  "mcpServers": {
    "hdhomerun-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRANSPORT=stdio",
        "-e", "HDHOMERUN_URL=https://service.example.com",
        "-e", "HDHOMERUN_DEVICE_AUTH=your_token",
        "knucklessg1/hdhomerun-mcp:1.1.0"
      ]
    }
  }
}
```

Or run a local streamable-http container and connect by URL:

```bash
docker compose -f docker/mcp.compose.yml up -d
```

```json
{
  "mcpServers": {
    "hdhomerun-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 4. Remote URL (deployed behind Caddy)

When the server is deployed remotely and published through Caddy on the internal
a deployment-selected HTTPS hostname, connect with the `"url"` key — no local process or image required:

```json
{
  "mcpServers": {
    "hdhomerun-mcp": { "url": "https://hdhomerun-mcp.example.invalid/mcp" }
  }
}
```

Caddy reverse-proxies `https://hdhomerun-mcp.example.invalid` to the container's `:8000`
streamable-http listener.
<!-- END GENERATED: deployment-options -->

## Docker Compose

Both Compose definitions load the tracked `.env.example` defaults and then
overlay an optional repository-root `.env`. Copy `.env.example` to `.env` only
when the deployment needs local overrides or credentials; Compose validation
does not require secrets.

```bash
docker compose -f docker/mcp.compose.yml up -d      # MCP server only
docker compose -f docker/agent.compose.yml up -d    # MCP + agent
```

## Run the A2A agent server

```bash
hdhomerun-agent --mcp-config mcp_config.json --web
```
