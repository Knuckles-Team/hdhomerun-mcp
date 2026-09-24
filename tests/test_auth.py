import os
from unittest.mock import patch

import pytest
from agent_connector_sdk.auth.delegation import DelegationSettings
from agent_connector_sdk.auth.tokens import AccessToken

import hdhomerun_mcp.auth as auth_module
from hdhomerun_mcp.auth import get_client

_DELEGATION_SETTINGS = DelegationSettings(
    enabled=True,
    token_endpoint="https://idp.example/token",
    client_id="hdhomerun-mcp",
    client_secret_ref="env://HDHOMERUN_OIDC_CLIENT_SECRET",
    audience="https://hdhomerun.example/api",
    scopes="dvr.read",
)


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
    """Delegation leaves TLS policy to the SDK's canonical OIDC client."""
    auth_module._client = None
    fake_token = AccessToken("delegated-token", 300.0, 0.0)
    with (
        patch.object(
            DelegationSettings, "from_settings", return_value=_DELEGATION_SETTINGS
        ),
        patch("hdhomerun_mcp.auth.current_user_token", return_value="user-token"),
        patch("hdhomerun_mcp.auth.current_user_identity", return_value="actor:test"),
        patch(
            "hdhomerun_mcp.auth.exchange_token", return_value=fake_token
        ) as delegated,
        patch("hdhomerun_mcp.auth.ApiClientSystem") as client_cls,
    ):
        get_client(url="http://hdhomerun.local")

    delegated.assert_called_once()
    _, delegated_kwargs = delegated.call_args
    assert delegated_kwargs["subject_token"] == "user-token"
    _, client_kwargs = client_cls.call_args
    assert client_kwargs["url"] == "http://hdhomerun.local"
    assert client_kwargs["device_auth"] == "delegated-token"
    assert client_kwargs["tls_profile"].verify_enabled is True
    auth_module._client = None
    with patch("hdhomerun_mcp.auth.setting") as mock_setting:
        mock_setting.side_effect = lambda name, default=None: {
            "HDHOMERUN_URL": "http://10.0.132.114",
            "HDHOMERUN_DEVICE_AUTH": "abc",
        }.get(name, default)
        client_a = get_client()
        client_b = get_client()
        assert client_a is client_b
        assert client_a.url == "http://10.0.132.114"
    auth_module._client = None


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_verifies_by_default():
    """No TLS env vars configured -> the resolved profile still verifies."""
    auth_module._client = None
    with patch.dict(
        os.environ, {"HDHOMERUN_URL": "https://hdhomerun.local"}, clear=True
    ):
        client = get_client()
        assert client.tls_profile.verify_enabled is True
        assert client._session.verify is True
    auth_module._client = None


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_honors_named_tls_profile():
    """``HDHOMERUN_TLS_PROFILE`` selects a named profile from the catalog —
    proving the documented env var is actually wired end-to-end (this only
    matters for the SiliconDust cloud recording-rules API)."""
    auth_module._client = None
    catalog = (
        '{"profiles": {"private-pki": {"system_trust": false, '
        '"ca_directory": "/etc/ssl/certs"}}}'
    )
    with patch.dict(
        os.environ,
        {
            "HDHOMERUN_URL": "http://10.0.132.114",
            "HDHOMERUN_TLS_PROFILE": "private-pki",
            "TLS_PROFILES": catalog,
        },
        clear=True,
    ):
        client = get_client()
        assert client.tls_profile.verify_enabled is True
        assert client.tls_profile.name == "private-pki"
        assert client.tls_profile.system_trust is False
    auth_module._client = None


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_delegation_failure_raises_token_exchange_error():
    """A broken OIDC token exchange surfaces as a clear RuntimeError, not a
    raw exception or a silently-cached partial client.

    CONCEPT:HDHR-http.api.json-interface
    """
    auth_module._client = None
    with (
        patch.object(
            DelegationSettings, "from_settings", return_value=_DELEGATION_SETTINGS
        ),
        patch("hdhomerun_mcp.auth.current_user_token", return_value="user-token"),
        patch(
            "hdhomerun_mcp.auth.exchange_token",
            side_effect=Exception("token exchange broke"),
        ),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            get_client()
    assert "Token exchange failed" in str(exc_info.value)
    assert auth_module._client is None
    auth_module._client = None
