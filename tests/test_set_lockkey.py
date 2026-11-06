"""CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R003: tuner lock and release."""

from unittest.mock import patch


def test_lock_sets_the_key_and_release_presents_it(client):
    with patch.object(type(client), "set_item", return_value="") as set_item:
        key = client.set_lockkey(2, True)
        assert key.isdigit() and 0 < int(key) < 2**32
        set_item.assert_called_once_with("/tuner2/lockkey", key)

        set_item.reset_mock()
        client.set_lockkey(2, False, lockkey=int(key))
        set_item.assert_called_once_with("/tuner2/lockkey", "none", lockkey=int(key))
