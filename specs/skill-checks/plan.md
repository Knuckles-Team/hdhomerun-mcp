# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

`connector-standard` in `.pre-commit-config.yaml` runs the pipelines skill gates (atomicity, frontmatter portability, path portability) over the packaged skills; the repository holds no hook and no helper script. No hook names an absolute workspace path.

## Technical Context

- **Language/Version**: Python 3.14 (floor 3.12)
- **Primary Dependencies**: scion-sdk, fastmcp
- **Storage**: N/A; the connector stores nothing
- **Testing**: pytest; the proof level each row names
- **Target Platform**: Linux containers
- **Project Type**: connector (MCP server)
- **Performance Goals**: N/A
- **Constraints**: one tool per API operation; shared capabilities come from the SDK
- **Scale/Scope**: 1 rows

## Constitution Check

- One owner per concept: pass. The connector owns one external system's calls, mappings and tools only.
- Connectors depend on the SDK and are called through arbora: pass.
- No ratchets: pass. The rows add no suppression.

## Project Structure

```text
.pre-commit-config.yaml  existing
tests/test_skill_check_hooks.py  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

The rows are delivered in place; the design is the caller chain below.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001`: A developer commit or a CI run executes pre-commit, which runs the `connector-standard` hook declared in `.pre-commit-config.yaml` from the shared pipelines repository at `rev: main`; the hook checks the skills under `hdhomerun_mcp/skills/`.

## Cross-repo seams

none
