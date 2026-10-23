# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` | **Skill checks on every runner.** `.pre-commit-config.yaml` declares `check-atomicity`, `check-frontmatter-portability` and `check-path-portability`. Each calls `scripts/universal_skills_check.sh`, which falls back to the published universal-skills gate scripts when the workspace checkout is absent. Proving test: `tests/test_skill_check_hooks.py`. | The three hooks are declared, none names an absolute workspace path, and the helper runs the packaged skills through the atomicity check. |
