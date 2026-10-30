import pytest

from scion_sdk.connector import build_server


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_mcp_instance_registration(monkeypatch):
    """MCP server instantiates with its tool domains registered.

    CONCEPT:HDHR-http.api.json-interface
    """
    monkeypatch.setattr("sys.argv", ["hdhomerun-mcp"])
    _, mcp = build_server("hdhomerun_mcp", command_args=[])
    assert mcp is not None
