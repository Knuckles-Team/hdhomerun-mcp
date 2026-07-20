from .api_client_base import HDHomeRunApiBase
from .api_client_config import HDHomeRunApiConfig, HDHomeRunControlError
from .api_client_discovery import HDHomeRunApiDiscovery
from .api_client_doctor import HDHomeRunApiDoctor
from .api_client_dvr import HDHomeRunApiDvr
from .api_client_http import HDHomeRunApiHttp


class ApiClientSystem(
    HDHomeRunApiDoctor,
    HDHomeRunApiDiscovery,
    HDHomeRunApiHttp,
    HDHomeRunApiDvr,
    HDHomeRunApiConfig,
):
    """Unified HDHomeRun client: HTTP JSON API + Discovery + DVR + hdhomerun_config
    control protocol + doctor diagnostics, all over one device connection."""

    __slots__ = ()


__all__ = [
    "ApiClientSystem",
    "HDHomeRunApiBase",
    "HDHomeRunControlError",
]
