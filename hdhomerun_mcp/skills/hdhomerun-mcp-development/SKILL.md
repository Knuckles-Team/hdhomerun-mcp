---
name: hdhomerun-mcp-development
skill_type: skill
domain: development
description: >-
  Develop, test, gate, and release the HDHomeRun connector while preserving its
  local tuner and cloud DVR boundaries, SDK connector wiring, packaged content,
  and source-backed Pages publication.
license: MIT
tags: [hdhomerun, mcp, connector, sdk, development, test, gates]
tier: repository
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---

# hdhomerun-mcp development

This repository owns the HDHomeRun device and cloud DVR API calls, MCP action
mapping, connector source declarations, ontology mappings, and packaged
content. The connector SDK owns shared transports, TLS policy, credential
helpers, and artifact contracts; admission and durable graph state belong to
their owning repositories. Read `AGENTS.md` and the focused tests before
changing a surface. Keep credentials, private endpoints, tuner records, and
generated runtime state out of source, fixtures, logs, and this skill.

## Repository and runtime map

- `hdhomerun_mcp/__init__.py` declares the one SDK `Connector`, its API facade,
  client factory, and `hdhomerun_mcp.mcp` tool module. Preserve this identity
  and the existing stdio/HTTP serving boundary.
- `hdhomerun_mcp/api/` owns the modular HTTP, discovery, DVR, doctor, and
  protocol clients. `hdhomerun_mcp/api_client.py` is only the compatibility
  facade; do not create a second client plane.
- `hdhomerun_mcp/mcp/` owns action-routed tools. Keep tool names, request and
  response models, device discovery, lineup, tuner, DVR, and doctor behavior
  aligned with the API modules.
- `hdhomerun_mcp/auth.py` resolves `HDHOMERUN_URL`,
  `HDHOMERUN_DEVICE_AUTH`, `HDHOMERUN_TLS_PROFILE`, and
  `HDHOMERUN_TLS_PROFILE_REF` through the SDK. The local tuner API is normally
  unauthenticated while cloud DVR recording rules use the device auth value;
  preserve that distinction and never disable TLS verification.
- `hdhomerun_mcp/connector_sources.py`, `kg_ingest.py`, and
  `ontology/hdhomerun.ttl` are the source, ingestion, and ontology boundaries.
  Extend those declarations instead of duplicating IDs or mappings in tools.
- `hdhomerun_mcp/skills/`, `ontology/`, `connectors/`, prompts, and
  `mcp_config.json` are package data. Inspect a built wheel when changing
  packaged content.

## Rapid delivery: the 5-minute contract

1. Find the owning row with `git grep -n "<term>" -- specs`, read this skill,
   `AGENTS.md`, and the directly bound tests before editing.
2. Inspect the SDK `Connector`, action dispatch, API wrapper, auth/TLS path,
   source declarations, ingestion mapping, and package-data declaration before
   changing runtime or packaged content.
3. Make the smallest connector-owned change. Preserve public tool names and
   payload schemas, HDHomeRun API paths, `HDHOMERUN_*` settings, TLS
   verification, stable source IDs, ontology mappings, and the SDK boundary.
4. Run the smallest focused tests with the locked environment, then run the
   repository hooks normally. Never bypass a hook or failing gate.
5. When packaged content changes, advance the patch version and refresh
   `uv.lock`; inspect the wheel and sdist for the intended skill and other
   declared resources before publication.
6. Treat Pages and package publication as separate proof. After the exact main
   SHA succeeds, verify `/spec-delivery/`, its `index.html`, and `snapshot.json`
   over HTTPS. Do not claim publication from local source inspection alone.

## Focused commands

From the repository root:

```bash
uv sync --locked
uv run --locked --extra test pytest -q \
  tests/test_hdhomerun_development_skill.py tests/test_pages_workflow.py
uvx pre-commit run --all-files
uvx pre-commit run --all-files --hook-stage pre-push
```

The normal hooks own connector-standard, secrets, spec, fast tests, and
dependency-readiness checks. Do not copy those hooks into this package, add a
live tuner call, or use credentials in a focused test.

## Publication and change discipline

`.github/workflows/pages.yml` is the sole Pages caller. It invokes
`pages_pipeline.yml@main` with `content_source: docs`,
`spec_dashboard_enabled: true`, and `.github/spec-dashboard.json`; its path
filters include documentation, specs, the dashboard, and the caller. The
package workflow delegates connector wheel and image publication to the shared
Pipelines callers. Preserve those boundaries and require exact hosted evidence
for package, container, and Pages claims.

Use injected `HDHOMERUN_*` settings only. Never commit device auth, provider
records, private hostnames, or a TLS bypass. Keep local HTTP discovery separate
from cloud DVR authentication, preserve idempotent action behavior, and keep
source metadata tenant-neutral. Generated `specs/*/status.json` files are owned
by the Pipelines hooks; never edit them by hand.

Work in a real Git worktree based on `origin/main`. Inspect the complete diff,
stage only reviewed paths, and never use `git stash`, `git add -A`, or `git add
.`. Keep runtime and generated artifacts outside this bounded documentation
and delivery slice.
