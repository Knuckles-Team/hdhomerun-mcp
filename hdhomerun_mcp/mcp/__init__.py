from .mcp_config import register_config_tools
from .mcp_discovery import register_discovery_tools
from .mcp_doctor import register_doctor_tools
from .mcp_dvr import register_dvr_tools
from .mcp_http import register_http_tools

__all__ = [
    "register_http_tools",
    "register_discovery_tools",
    "register_dvr_tools",
    "register_config_tools",
    "register_doctor_tools",
]
