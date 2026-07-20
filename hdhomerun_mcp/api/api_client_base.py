"""Base HTTP wrapper shared by every HDHomeRun API domain.

HDHomeRun tuner devices on the local network do not require authentication for
the HTTP JSON API (``discover.json``/``lineup.json``/etc.) — anyone on the LAN
can query/tune them, matching every other vendor tool (Kodi, Plex, Channels
DVR). The SiliconDust **cloud** DVR API (``dvr_api.py``) authenticates instead
via the device's own ``DeviceAuth`` string(s) passed as a request parameter —
there is no bearer token.
"""

from __future__ import annotations

from typing import Any

import requests
from agent_utilities.base_utilities import get_logger
from agent_utilities.core.exceptions import ParameterError

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 10


class HDHomeRunApiBase:
    """Base HTTP session wrapper for a single HDHomeRun device.

    Parameters:
        url: Device base URL, e.g. ``http://10.0.132.114`` (no trailing slash).
        device_auth: Optional ``DeviceAuth`` string(s) for cloud DVR calls
            (concatenated when a device has multiple tuners' auth strings).
        verify: TLS certificate verification (local devices are plain HTTP;
            kept for parity with the fleet's env-var convention).
        timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        url: str | None = None,
        device_auth: str | None = None,
        verify: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.url = (url or "").rstrip("/")
        self.device_auth = device_auth
        self.verify = verify
        self.timeout = timeout
        self._session = requests.Session()

    def _get(self, path_or_url: str, **kwargs) -> requests.Response:
        url = (
            path_or_url
            if path_or_url.startswith("http")
            else f"{self.url}{path_or_url}"
        )
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify)
        response = self._session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def _post(self, path_or_url: str, **kwargs) -> requests.Response:
        url = (
            path_or_url
            if path_or_url.startswith("http")
            else f"{self.url}{path_or_url}"
        )
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify)
        response = self._session.post(url, **kwargs)
        response.raise_for_status()
        return response

    def _get_json(self, path_or_url: str, **kwargs) -> Any:
        response = self._get(path_or_url, **kwargs)
        try:
            return response.json()
        except ValueError as e:
            raise ParameterError(
                f"Expected JSON from {path_or_url}, got: {response.text[:200]!r}"
            ) from e

    def require_url(self) -> str:
        if not self.url:
            raise ParameterError(
                "Device URL is required. Set HDHOMERUN_URL or pass url= explicitly "
                "(discover one with the discovery domain first)."
            )
        return self.url
