import importlib

import pytest


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_mcp_server_module_importable():
    """MCP server module imports cleanly at startup. CONCEPT:HDHR-http.api.json-interface"""
    assert importlib.import_module("hdhomerun_mcp.mcp_server") is not None
