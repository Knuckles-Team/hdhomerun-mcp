import pytest

from hdhomerun_mcp.mcp_server import get_mcp_instance


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_mcp_instance_registration(monkeypatch):
    """MCP server instantiates with its tool domains registered.

    CONCEPT:HDHR-http.api.json-interface
    """
    monkeypatch.setattr("sys.argv", ["hdhomerun-mcp"])
    mcp, args, middlewares = get_mcp_instance()
    assert mcp is not None
