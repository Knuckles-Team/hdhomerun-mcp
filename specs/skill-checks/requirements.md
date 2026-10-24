# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` | **Skill checks on every runner.** The `connector-standard` hook that `.pre-commit-config.yaml` declares runs the pipelines skill gates (atomicity, frontmatter portability, path portability) over the packaged skills, on a developer machine and on a CI runner alike. Proving test: `tests/test_skill_check_hooks.py`. | `connector-standard` is declared, no hook names an absolute workspace path, and every packaged skill has a name equal to its directory. |
