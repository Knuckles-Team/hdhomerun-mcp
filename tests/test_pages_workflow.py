"""PIPE-CONNSPEC-R127.3: HDHomeRun Pages and spec-dashboard contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / ".github/spec-dashboard.json"

pytestmark = pytest.mark.spec("PIPE-CONNSPEC-R127.3")


def test_dashboard_reads_only_canonical_spec_status_files() -> None:
    config = json.loads(DASHBOARD.read_text(encoding="utf-8"))

    assert config == {
        "version": 1,
        "sources": [{"glob": "specs/*/status.json", "kind": "spec"}],
    }


def test_legacy_mkdocs_publisher_is_absent() -> None:
    assert not (ROOT / ".github/workflows/docs.yml").exists()
