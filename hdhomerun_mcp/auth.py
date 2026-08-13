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
   token via ``agent_utilities.mcp.delegated_auth`` (kept for fleet
   consistency; not required for local-LAN device access).
2. **Fixed credentials** — ``HDHOMERUN_URL`` (required) + optional
   ``HDHOMERUN_DEVICE_AUTH`` (only needed for cloud DVR recording-rules calls).

For a multi-tuner household, add an ``instances.py`` resolving a named
instance from ``hdhomerun_instances`` in
``~/.config/agent-utilities/config.json`` — see ``gitlab_api.instances``
(concept KG-2.9g) for the golden pattern.
"""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting
from agent_utilities.core.exceptions import AuthError, UnauthorizedError

from .api import ApiClientSystem

logger = get_logger(__name__)
_client = None


def get_client(
    url: str | None = None,
    token: str | None = None,
    verify: bool | None = None,
    config: dict | None = None,
) -> ApiClientSystem:
    """Get or create a singleton API client (OIDC delegation or fixed credentials).

    Credentials resolve through the shared config layer (the one XDG
    ``config.json`` / env) at call time, not frozen at import. ``token`` here
    doubles as the device's ``DeviceAuth`` string (cloud DVR calls only).
    """
    global _client
    if _client is not None:
        return _client

    base_url = url or setting("HDHOMERUN_URL", "http://hdhomerun.local")
    device_auth = token or setting("HDHOMERUN_DEVICE_AUTH", "")
    if verify is None:
        verify = setting("HDHOMERUN_SSL_VERIFY", True)

    from agent_utilities.mcp.delegated_auth import (
        get_delegated_token,
        get_user_identity,
        is_delegation_enabled,
    )

    # --- Path 1: OIDC Delegation (RFC 8693 Token Exchange) ---
    if is_delegation_enabled(config):
        try:
            delegated_token = get_delegated_token(
                config=config,
                audience=(config or {}).get("audience", base_url),
                scopes=(config or {}).get("delegated_scopes", "api"),
            )
            identity = get_user_identity()
            logger.info(
                "Using OIDC delegated token",
                extra={"user_email": identity.get("email"), "url": base_url},
            )
            _client = ApiClientSystem(
                url=base_url, device_auth=delegated_token, verify=verify
            )
            return _client
        except Exception as e:
            logger.error(
                "OIDC delegation failed",
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )
            raise RuntimeError(f"Token exchange failed: {str(e)}") from e

    # --- Path 2: Fixed Credentials (HDHOMERUN_URL + optional HDHOMERUN_DEVICE_AUTH) ---
    logger.info("Using fixed credentials")
    try:
        _client = ApiClientSystem(url=base_url, device_auth=device_auth, verify=verify)
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

    return _client
