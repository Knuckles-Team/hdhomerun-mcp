# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`connector-standard` in `.pre-commit-config.yaml` runs the pipelines skill gates (atomicity, frontmatter portability, path portability) over the packaged skills; the repository holds no hook and no helper script. No hook names an absolute workspace path.
