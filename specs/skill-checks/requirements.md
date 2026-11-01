# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001` | **Skill checks on every runner.** The `connector-standard` hook that `.pre-commit-config.yaml` declares runs the pipelines skill gates (atomicity, frontmatter portability, path portability) over the packaged skills, on a developer machine and on a CI runner alike. Proving test: `tests/test_skill_check_hooks.py`. Caller chain: A developer commit or a CI run executes pre-commit, which runs the `connector-standard` hook declared in `.pre-commit-config.yaml` from the shared pipelines repository at `rev: main`; the hook checks the skills under `hdhomerun_mcp/skills/`. Shape: `.pre-commit-config.yaml` declares only the central `connector-standard` hook and names no workspace path, and each `hdhomerun_mcp/skills/<name>/SKILL.md` carries `name:` equal to its directory; no local gate code is added. | `connector-standard` is declared, no hook names an absolute workspace path, and every packaged skill has a name equal to its directory. Test: `tests/test_skill_check_hooks.py::test_the_central_standard_hook_is_declared`. |
