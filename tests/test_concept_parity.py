from pathlib import Path

import pytest

CONCEPTS_DOC = Path(__file__).resolve().parents[1] / "docs" / "concepts.md"


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_concepts_doc_exists():
    """Concept registry doc exists. CONCEPT:HDHR-http.api.json-interface"""
    assert CONCEPTS_DOC.is_file()


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_eco_bridge_present():
    """ECO-4.0 bridge concept is referenced. CONCEPT:HDHR-http.api.json-interface"""
    assert "ECO-4.0" in CONCEPTS_DOC.read_text(encoding="utf-8")


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_prefix_registered():
    """Project concept prefix is registered. CONCEPT:HDHR-http.api.json-interface"""
    assert "CONCEPT:HDHR-" in CONCEPTS_DOC.read_text(encoding="utf-8")
