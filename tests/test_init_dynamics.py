import importlib

import pytest


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_package_imports():
    """Top-level package exposes its public API. CONCEPT:HDHR-http.api.json-interface"""
    module = importlib.import_module("hdhomerun_mcp")
    assert hasattr(module, "__all__")
