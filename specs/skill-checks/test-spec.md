# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` | `tests/test_skill_check_hooks.py` | The hooks are declared without an absolute workspace path, and the helper has the download fallback. |
