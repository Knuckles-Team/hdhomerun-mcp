# CONN-HDHOMERUN-MCP-SKILL-CHECKS — The skill checks run on every runner

Owner: hdhomerun-mcp. Cross-repo IDs: none.

## Purpose and user stories

The packaged skills must pass the atomicity, frontmatter-portability and path-portability checks of the pipelines `connector-standard` hook on a developer machine and on a CI runner.

## Why a new spec

The specs of this repository were read; none owns this capability. This spec states it for this connector only.

## Scope and interfaces

In scope: the rows of [requirements.md](requirements.md). Out of scope: the SDK modules and the engine, which own the shared capabilities.

## User Scenarios & Testing

### User Story 1 - The skill checks run on every runner (Priority: P1)

The packaged skills must pass the atomicity, frontmatter-portability and path-portability checks of the pipelines `connector-standard` hook on a developer machine and on a CI runner.

**Acceptance Scenarios**:

1. **Given** the connector is configured, **When** the behaviour of row `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` (skill checks on every runner) is exercised, **Then** `connector-standard` is declared, no hook names an absolute workspace path, and every packaged skill has a name equal to its directory. Test: `tests/test_skill_check_hooks.py::test_the_central_standard_hook_is_declared`.

### Edge Cases

- If `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` is not met, its proving test fails: skill checks on every runner.

## Requirements

- **FR-001**: Skill checks on every runner. Rows: `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001`.

## Success Criteria

- **SC-001**: `connector-standard` is declared, no hook names an absolute workspace path, and every packaged skill has a name equal to its directory. Rows: `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001`.

## Assumptions

- The external system is reachable with operator-supplied credentials.
- The SDK and engine contracts the rows cite are at the floors declared in `pyproject.toml`.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` | [plan.md](plan.md) | T-001 | [test-spec.md](test-spec.md) |
