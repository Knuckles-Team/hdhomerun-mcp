"""PIPE-CONNSPEC-R127.4: the HDHomeRun development skill is packaged."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "hdhomerun_mcp/skills/hdhomerun-mcp-development/SKILL.md"

pytestmark = pytest.mark.spec("PIPE-CONNSPEC-R127.4")


def test_development_skill_has_rapid_contract_and_package_binding() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert SKILL.is_file()
    assert re.search(r"^name:\s*hdhomerun-mcp-development\s*$", frontmatter, re.M)
    assert re.search(r"^skill_type:\s*skill\s*$", frontmatter, re.M)
    assert "## Rapid delivery: the 5-minute contract" in text
    for term in (
        "hdhomerun_mcp/__init__.py",
        "hdhomerun_mcp/api/",
        "hdhomerun_mcp/mcp/",
        "hdhomerun_mcp/auth.py",
        "hdhomerun_mcp/connector_sources.py",
        "HDHOMERUN_URL",
        "HDHOMERUN_DEVICE_AUTH",
        "HDHOMERUN_TLS_PROFILE",
        "skills/",
        "uv run --locked --extra test pytest",
        "spec_dashboard_enabled",
    ):
        assert term in text

    assert "verify=False" not in text
    assert "--no-verify" not in text
    package_data = project["tool"]["setuptools"]["package-data"]["hdhomerun_mcp"]
    assert "skills/**" in package_data
    assert project["project"]["entry-points"]["agent_connector_sdk.connector"] == {
        "hdhomerun-mcp": "hdhomerun_mcp:connector"
    }
