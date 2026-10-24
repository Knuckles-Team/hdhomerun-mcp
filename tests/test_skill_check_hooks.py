"""CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001: the skill gates run through the central connector-standard hook."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001")

ROOT = Path(__file__).resolve().parents[1]


def _config() -> str:
    return (ROOT / ".pre-commit-config.yaml").read_text()


def test_the_central_standard_hook_is_declared():
    assert "id: connector-standard" in _config()


def test_no_hook_names_an_absolute_workspace_path():
    assert "/home/" + "apps/workspace" not in _config()


def test_every_packaged_skill_is_named_for_its_directory():
    skills = sorted((ROOT / "hdhomerun_mcp/skills").glob("*/SKILL.md"))
    assert skills
    for skill in skills:
        assert f"name: {skill.parent.name}\n" in skill.read_text()
