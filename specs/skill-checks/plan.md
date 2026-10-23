# CONN-HDHOMERUN-MCP-SKILL-CHECKS — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

Three local hooks in `.pre-commit-config.yaml` call `scripts/universal_skills_check.sh`. The helper runs the gate script from `UNIVERSAL_SKILLS_SCRIPTS`, then the workspace checkout, then the published universal-skills `main` downloaded to the cache. No hook names an absolute workspace path.
