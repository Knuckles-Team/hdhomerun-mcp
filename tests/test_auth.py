import os
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


_DELEGATION_SETTINGS_ENV = {
    "ENABLE_DELEGATION": "true",
    "OIDC_TOKEN_URL": "https://idp.example.invalid/token",
    "OIDC_CLIENT_ID": "hdhomerun-mcp",
    "OIDC_CLIENT_SECRET_REF": "env://TEST_HDHOMERUN_OIDC_SECRET_UNUSED",
    "AUDIENCE": "https://hdhomerun.example/api",
}


def _set_delegation_settings_env(monkeypatch) -> None:
    for key, value in _DELEGATION_SETTINGS_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_delegation_uses_canonical_oidc_transport(monkeypatch):
    """Delegation leaves TLS policy to agent-connector-sdk's canonical OIDC client."""
    auth_module._client = None
    monkeypatch.setenv("HDHOMERUN_URL", "http://hdhomerun.local")
    _set_delegation_settings_env(monkeypatch)

    import agent_connector_sdk.auth.delegation as delegation
    from agent_connector_sdk.auth.tokens import AccessToken

    monkeypatch.setattr(delegation, "current_user_token", lambda: "caller-token")
    monkeypatch.setattr(
        delegation,
        "exchange_token",
        lambda settings, *, subject_token, http_client, resolver=None: AccessToken(
            value="delegated-token", ttl_seconds=3600, expires_at=0.0
        ),
    )
    with patch("hdhomerun_mcp.auth.ApiClientSystem") as client_cls:
        get_client(url="http://hdhomerun.local")

    _, client_kwargs = client_cls.call_args
    assert client_kwargs["url"] == "http://hdhomerun.local"
    assert client_kwargs["device_auth"] == "delegated-token"
    assert client_kwargs["tls_profile"].verify_enabled is True
    auth_module._client = None


@pytest.mark.concept("HDHR-http.api.json-interface")
def test_get_client_verifies_by_default():
    """No TLS env vars configured -> the resolved profile still verifies."""
    auth_module._client = None
    with patch.dict(os.environ, {"HDHOMERUN_URL": "https://hdhomerun.local"}, clear=True):
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
def test_get_client_delegation_failure_raises_token_exchange_error(monkeypatch):
    """A broken OIDC token exchange surfaces as a clear RuntimeError, not a
    raw exception or a silently-cached partial client.

    CONCEPT:HDHR-http.api.json-interface
    """
    auth_module._client = None
    monkeypatch.setenv("HDHOMERUN_URL", "http://hdhomerun.local")
    _set_delegation_settings_env(monkeypatch)

    import agent_connector_sdk.auth.delegation as delegation

    monkeypatch.setattr(delegation, "current_user_token", lambda: "caller-token")

    def _boom(settings, *, subject_token, http_client, resolver=None):
        raise ValueError("token exchange broke")

    monkeypatch.setattr(delegation, "exchange_token", _boom)

    with pytest.raises(RuntimeError, match="Token exchange failed"):
        get_client()
    assert auth_module._client is None
    auth_module._client = None
