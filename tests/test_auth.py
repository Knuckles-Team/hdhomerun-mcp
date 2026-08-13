from unittest.mock import patch

import pytest

import hdhomerun_mcp.auth as auth_module
from hdhomerun_mcp.auth import get_client


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_auth_error():
    """Auth failure surfaces a clear error. CONCEPT:HDHR-http.api.json-interface"""
    auth_module._client = None
    with patch("hdhomerun_mcp.auth.ApiClientSystem") as mock_client_cls:
        mock_client_cls.side_effect = Exception("Auth Failure")
        with pytest.raises(RuntimeError) as exc_info:
            get_client()
        assert "AUTHENTICATION ERROR" in str(exc_info.value)
    auth_module._client = None


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_singleton():
    """get_client() memoizes a singleton instance. CONCEPT:HDHR-http.api.json-interface"""
    auth_module._client = None


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_delegation_uses_canonical_oidc_transport():
    """Delegation leaves TLS policy to agent-utilities' canonical OIDC client."""
    auth_module._client = None
    config = {
        "audience": "https://hdhomerun.example/api",
        "delegated_scopes": "dvr.read",
    }
    with (
        patch(
            "agent_utilities.mcp.delegated_auth.is_delegation_enabled",
            return_value=True,
        ),
        patch(
            "agent_utilities.mcp.delegated_auth.get_delegated_token",
            return_value="delegated-token",
        ) as delegated,
        patch(
            "agent_utilities.mcp.delegated_auth.get_user_identity",
            return_value={"identity_ref": "actor:test"},
        ),
        patch("hdhomerun_mcp.auth.ApiClientSystem") as client_cls,
    ):
        get_client(url="http://hdhomerun.local", config=config, verify=False)

    delegated.assert_called_once_with(
        config=config,
        audience="https://hdhomerun.example/api",
        scopes="dvr.read",
    )
    client_cls.assert_called_once_with(
        url="http://hdhomerun.local",
        device_auth="delegated-token",
        verify=False,
    )
    auth_module._client = None
    with patch("hdhomerun_mcp.auth.setting") as mock_setting:
        mock_setting.side_effect = lambda name, default=None: {
            "HDHOMERUN_URL": "http://10.0.132.114",
            "HDHOMERUN_DEVICE_AUTH": "abc",
            "HDHOMERUN_SSL_VERIFY": True,
        }.get(name, default)
        client_a = get_client()
        client_b = get_client()
        assert client_a is client_b
        assert client_a.url == "http://10.0.132.114"
    auth_module._client = None
