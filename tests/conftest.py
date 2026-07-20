from unittest.mock import MagicMock

import pytest

from hdhomerun_mcp.api import ApiClientSystem


@pytest.fixture
def mock_api_client():
    client = MagicMock()
    client.get_discover.return_value = {
        "FriendlyName": "HDHomeRun FLEX 4K",
        "ModelNumber": "HDFX-4K",
        "DeviceID": "10ACFCDE",
        "DeviceAuth": "test-auth",
        "TunerCount": 4,
    }
    return client


@pytest.fixture
def client():
    """A real ApiClientSystem instance against a fake local URL (no network calls
    unless a test explicitly mocks requests/sockets)."""
    return ApiClientSystem(url="http://10.0.132.114", device_auth="test-auth")
