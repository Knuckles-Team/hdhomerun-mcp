#!/usr/bin/python

"""Authentication.

HDHomeRun tuner devices need no credential for the local HTTP JSON API or the
hdhomerun_config control protocol — anyone on the LAN can reach them. Only the
SiliconDust cloud DVR API (recording rules) is authenticated, and it uses the
vendor's own ``DeviceAuth`` string (from ``discover.json``) rather than a
bearer token, so the credential resolution here is simpler than a typical
connector's two-tier OIDC/token flow:

1. **OIDC Delegation** (RFC 8693 Token Exchange) — when ``ENABLE_DELEGATION``
   is active, exchanges the IdP-issued user token for a downstream access
   token via ``agent_connector_sdk.auth.delegation`` (kept for fleet
   consistency; not required for local-LAN device access).
2. **Fixed credentials** — ``HDHOMERUN_URL`` (required) + optional
   ``HDHOMERUN_DEVICE_AUTH`` (only needed for cloud DVR recording-rules calls).

For a multi-tuner household, add an ``instances.py`` resolving a named
instance from ``hdhomerun_instances`` in
``~/.config/agent-utilities/config.json`` — see ``gitlab_api.instances``
(concept KG-2.9g) for the golden pattern.
"""

import logging

from agent_connector_sdk.config import setting
from agent_connector_sdk.exceptions import AuthError, UnauthorizedError
from agent_connector_sdk.tls.profile import ResolvedTLSProfile
from agent_connector_sdk.tls.resolve import resolve_tls_profile

from .api import ApiClientSystem

logger = logging.getLogger(__name__)
_client = None


def _is_delegation_enabled(config: dict | None) -> bool:
    """Whether the OIDC delegation path should be attempted.

    An explicit ``config`` dict (test injection only -- no production caller
    passes one) wins outright; otherwise reads the real ``ENABLE_DELEGATION``
    setting through ``agent_connector_sdk.auth.delegation.DelegationSettings``.
    """
    if config is not None:
        return bool(config.get("enable_delegation", False))
    from agent_connector_sdk.auth.delegation import DelegationSettings

    return DelegationSettings.from_settings().enabled


def _resolve_delegated_client(
    base_url: str, tls_profile: ResolvedTLSProfile
) -> ApiClientSystem:
    """Path 1: OIDC Delegation (RFC 8693 Token Exchange).

    Reads delegation settings (``OIDC_TOKEN_URL``/``OIDC_CLIENT_ID``/
    ``OIDC_CLIENT_SECRET_REF``/``AUDIENCE``/``DELEGATED_SCOPES``) from the
    process settings via ``agent_connector_sdk.auth.delegation.DelegationSettings``;
    unlike the old ``agent_utilities`` helper, this has no per-call ``config``
    override for those fields, only for whether delegation is attempted at all
    (see :func:`_is_delegation_enabled`).
    """
    import httpx
    from agent_connector_sdk.auth.delegation import (
        DelegationSettings,
        current_user_token,
        exchange_token,
    )
    from agent_connector_sdk.exceptions import LoginRequiredError

    try:
        settings = DelegationSettings.from_settings()
        subject_token = current_user_token()
        if not subject_token:
            raise LoginRequiredError("no verified caller token to delegate")
        with httpx.Client(timeout=30) as http_client:
            access_token = exchange_token(
                settings, subject_token=subject_token, http_client=http_client
            )
        logger.info("Using OIDC delegated token", extra={"url": base_url})
        return ApiClientSystem(
            url=base_url, device_auth=access_token.value, tls_profile=tls_profile
        )
    except Exception as e:
        logger.error(
            "OIDC delegation failed",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
        )
        raise RuntimeError(f"Token exchange failed: {str(e)}") from e


def _resolve_fixed_credentials_client(
    base_url: str, device_auth: str, tls_profile: ResolvedTLSProfile
) -> ApiClientSystem:
    """Path 2: Fixed Credentials (HDHOMERUN_URL + optional HDHOMERUN_DEVICE_AUTH)."""
    logger.info("Using fixed credentials")
    try:
        return ApiClientSystem(
            url=base_url, device_auth=device_auth, tls_profile=tls_profile
        )
    except (AuthError, UnauthorizedError) as e:
        raise RuntimeError(
            f"AUTHENTICATION ERROR: The credentials provided are not valid for '{base_url}'. "
            f"Please check your HDHOMERUN_DEVICE_AUTH and HDHOMERUN_URL environment variables. "
            f"Error details: {str(e)}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"AUTHENTICATION ERROR: Failed to instantiate client. "
            f"Error details: {str(e)}"
        ) from e


def get_client(
    url: str | None = None,
    token: str | None = None,
    tls_profile: ResolvedTLSProfile | None = None,
    config: dict | None = None,
) -> ApiClientSystem:
    """Get or create a singleton API client (OIDC delegation or fixed credentials).

    Credentials resolve through the shared config layer (the one XDG
    ``config.json`` / env) at call time, not frozen at import. ``token`` here
    doubles as the device's ``DeviceAuth`` string (cloud DVR calls only). TLS
    only matters for the SiliconDust cloud recording-rules API — local tuner
    devices are plain HTTP — and is resolved through the shared AgentConfig
    transport profile (``HDHOMERUN_TLS_PROFILE``/``HDHOMERUN_TLS_PROFILE_REF``);
    verification is always on.
    """
    global _client
    if _client is not None:
        return _client

    base_url = url or setting("HDHOMERUN_URL", "http://hdhomerun.local")
    device_auth = token or setting("HDHOMERUN_DEVICE_AUTH", "")
    if tls_profile is None:
        tls_profile = resolve_tls_profile(
            "hdhomerun",
            profile_name=setting("HDHOMERUN_TLS_PROFILE", "") or None,
            profile_ref=setting("HDHOMERUN_TLS_PROFILE_REF", "") or None,
        )

    if _is_delegation_enabled(config):
        _client = _resolve_delegated_client(base_url, tls_profile)
        return _client

    _client = _resolve_fixed_credentials_client(base_url, device_auth, tls_profile)
    return _client
