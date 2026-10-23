"""CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001: the three skill-check hooks are declared and runner-independent."""

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("CONN-HDHOMERUN-MCP-SKILL-CHECKS-R001")

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ("check-atomicity", "check-frontmatter-portability", "check-path-portability")


def _config() -> str:
    return (ROOT / ".pre-commit-config.yaml").read_text()


@pytest.mark.parametrize("hook", HOOKS)
def test_hook_is_declared(hook):
    assert f"id: {hook}" in _config()


def test_no_hook_names_an_absolute_workspace_path():
    assert "/home/apps/workspace" not in _config()
    assert "scripts/universal_skills_check.sh" in _config()


def test_helper_falls_back_to_the_published_scripts():
    helper = (ROOT / "scripts/universal_skills_check.sh").read_text()
    assert re.search(
        r"raw\.githubusercontent\.com/Knuckles-Team/universal-skills/main/scripts/",
        helper,
    )


def test_helper_runs_the_atomicity_check_on_the_packaged_skills():
    result = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/universal_skills_check.sh"),
            "check_atomicity",
            "--root",
            str(ROOT / "hdhomerun_mcp/skills"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
