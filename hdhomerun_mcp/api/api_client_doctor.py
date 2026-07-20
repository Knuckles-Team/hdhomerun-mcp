"""Doctor diagnostics — composes the http/discovery/dvr/config domains into a
single actionable health report, matching the fleet's "doctor" convention
(e.g. ``container-manager-mcp``'s ``cm_doctor``).

Checks performed by ``run_doctor()``:

1. **device_reachable** — ``GET /discover.json`` succeeds.
2. **firmware_model** — reports ModelNumber/FirmwareName/FirmwareVersion.
3. **tuner_count_vs_jellyfin** — compares the device's ``TunerCount`` against a
   paired Jellyfin instance's configured ``TunerHost`` entry for this device
   (optional; skipped — not a fail — when no Jellyfin URL/key is given).
4. **signal_strength** — per requested channel, briefly tunes and reads
   ``ss``/``snq``/``seq`` via the control protocol, then releases the tuner.
5. **device_auth** — DeviceAuth is present in discover.json and (optionally)
   validated against the DVR cloud API.
6. **discovery_cache_freshness** — age of the last on-disk discovery result.

Each check returns ``{"check": ..., "status": "pass"|"fail"|"warn"|"skip",
"detail": ..., "action": ...}`` — ``action`` is populated only on
fail/warn, with a concrete next step.
"""

from __future__ import annotations

import time
from typing import Any

import requests
from agent_utilities.base_utilities import get_logger

from .api_client_config import HDHomeRunApiConfig
from .api_client_discovery import DISCOVERY_CACHE_PATH, read_discovery_cache
from .api_client_dvr import HDHomeRunApiDvr
from .api_client_http import HDHomeRunApiHttp

logger = get_logger(__name__)

STALE_CACHE_SECONDS = 24 * 3600


class HDHomeRunApiDoctor(HDHomeRunApiHttp, HDHomeRunApiDvr, HDHomeRunApiConfig):
    """Diagnostic composite: reachability, firmware, tuners, signal, auth, cache."""

    def check_device_reachable(self) -> dict[str, Any]:
        try:
            info = self.get_discover()
        except (requests.RequestException, ValueError) as e:
            return {
                "check": "device_reachable",
                "status": "fail",
                "detail": str(e),
                "action": (
                    f"Confirm the device is powered on and reachable at {self.url} "
                    "(it may have re-leased a new DHCP address on its VLAN — try "
                    "discover_cloud() or a UDP broadcast rediscovery)."
                ),
            }
        return {"check": "device_reachable", "status": "pass", "detail": info}

    def check_firmware_model(
        self, info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        info = info or self.get_discover()
        detail = {
            "ModelNumber": info.get("ModelNumber"),
            "FirmwareName": info.get("FirmwareName"),
            "FirmwareVersion": info.get("FirmwareVersion"),
            "TunerCount": info.get("TunerCount"),
        }
        if not info.get("ModelNumber") or not info.get("FirmwareVersion"):
            return {
                "check": "firmware_model",
                "status": "warn",
                "detail": detail,
                "action": "discover.json is missing ModelNumber/FirmwareVersion — "
                "check for very old firmware or a legacy (pre-JSON-API) device.",
            }
        return {"check": "firmware_model", "status": "pass", "detail": detail}

    def check_tuner_count_vs_jellyfin(
        self,
        jellyfin_url: str | None,
        jellyfin_api_key: str | None,
        device_id: str | None = None,
        info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not jellyfin_url or not jellyfin_api_key:
            return {
                "check": "tuner_count_vs_jellyfin",
                "status": "skip",
                "detail": "No paired Jellyfin instance configured (jellyfin_url/"
                "jellyfin_api_key not supplied).",
            }
        info = info or self.get_discover()
        device_id = device_id or info.get("DeviceID")
        device_tuner_count = info.get("TunerCount")
        try:
            resp = requests.get(
                f"{jellyfin_url.rstrip('/')}/LiveTv/TunerHosts",
                headers={"X-Emby-Token": jellyfin_api_key},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            hosts = resp.json()
        except (requests.RequestException, ValueError) as e:
            return {
                "check": "tuner_count_vs_jellyfin",
                "status": "fail",
                "detail": str(e),
                "action": f"Could not reach Jellyfin at {jellyfin_url}/LiveTv/TunerHosts "
                "— verify the URL and API key.",
            }
        matching = [h for h in hosts if h.get("DeviceId") == device_id]
        if not matching:
            return {
                "check": "tuner_count_vs_jellyfin",
                "status": "fail",
                "detail": {"jellyfin_tuner_hosts": hosts},
                "action": f"No Jellyfin TunerHost matches DeviceId {device_id!r} — "
                "add one via POST /LiveTv/TunerHosts (see the "
                "hdhr-jellyfin-livetv-setup skill).",
            }
        jf_tuner_count = matching[0].get("TunerCount")
        if jf_tuner_count != device_tuner_count:
            return {
                "check": "tuner_count_vs_jellyfin",
                "status": "warn",
                "detail": {
                    "device_tuner_count": device_tuner_count,
                    "jellyfin_tuner_count": jf_tuner_count,
                },
                "action": "Jellyfin's configured TunerCount doesn't match the device — "
                "update the TunerHost entry (PUT /LiveTv/TunerHosts).",
            }
        return {
            "check": "tuner_count_vs_jellyfin",
            "status": "pass",
            "detail": {"tuner_count": device_tuner_count},
        }

    def check_signal_strength(
        self, channels: list[str], tuner: int = 0
    ) -> dict[str, Any]:
        """Briefly tune each channel and sample ss/snq/seq, then release the tuner."""
        if not channels:
            return {
                "check": "signal_strength",
                "status": "skip",
                "detail": "No channels supplied to sample.",
            }
        results: dict[str, Any] = {}
        failures: list[str] = []
        for channel in channels:
            try:
                url = self.build_stream_url(channel, tuner=tuner, duration=2)
                with requests.get(url, stream=True, timeout=self.timeout) as resp:
                    resp.raise_for_status()
                    next(resp.iter_content(chunk_size=4096), None)
                status_line = self.get_tuner_status(tuner)
                parsed = self.parse_tuner_status(status_line)
                results[channel] = parsed
                ss = int(parsed.get("ss", 0))
                if ss < 40:
                    failures.append(f"{channel} (ss={ss})")
            except (requests.RequestException, ValueError) as e:
                results[channel] = {"error": str(e)}
                failures.append(f"{channel} (error)")
            finally:
                try:
                    self.stop_tuner(tuner)
                except Exception as release_err:  # best-effort tuner release
                    logger.warning(
                        "Failed to release tuner %s after signal check: %s",
                        tuner,
                        release_err,
                    )
        if failures:
            return {
                "check": "signal_strength",
                "status": "warn",
                "detail": results,
                "action": f"Weak/failed signal on: {', '.join(failures)} — check antenna "
                "alignment/cabling for those channels.",
            }
        return {"check": "signal_strength", "status": "pass", "detail": results}

    def check_device_auth(
        self, info: dict[str, Any] | None = None, validate_cloud: bool = False
    ) -> dict[str, Any]:
        info = info or self.get_discover()
        device_auth = info.get("DeviceAuth")
        if not device_auth:
            return {
                "check": "device_auth",
                "status": "fail",
                "detail": "discover.json has no DeviceAuth field.",
                "action": "DeviceAuth is required for DVR cloud/recording-rules calls — "
                "confirm the device has DVR firmware and is registered to a "
                "SiliconDust account.",
            }
        if not validate_cloud:
            return {
                "check": "device_auth",
                "status": "pass",
                "detail": "DeviceAuth present.",
            }
        try:
            self.list_recording_rules(device_auth=device_auth)
        except (requests.RequestException, ValueError) as e:
            return {
                "check": "device_auth",
                "status": "warn",
                "detail": str(e),
                "action": "DeviceAuth present but the cloud recording_rules API call "
                "failed — the auth string may be stale or the cloud API unreachable.",
            }
        return {
            "check": "device_auth",
            "status": "pass",
            "detail": "DeviceAuth present and accepted by the cloud DVR API.",
        }

    def check_discovery_cache_freshness(self) -> dict[str, Any]:
        cache = read_discovery_cache()
        if cache is None:
            return {
                "check": "discovery_cache_freshness",
                "status": "warn",
                "detail": f"No discovery cache at {DISCOVERY_CACHE_PATH}.",
                "action": "Run a discovery pass (local broadcast or cloud) at least once "
                "to populate the cache.",
            }
        age = time.time() - cache.get("ts", 0)
        if age > STALE_CACHE_SECONDS:
            return {
                "check": "discovery_cache_freshness",
                "status": "warn",
                "detail": {"age_seconds": age, "source": cache.get("source")},
                "action": f"Discovery cache is {age / 3600:.1f}h old — re-run discovery "
                "in case the device re-leased a new IP.",
            }
        return {
            "check": "discovery_cache_freshness",
            "status": "pass",
            "detail": {"age_seconds": age, "source": cache.get("source")},
        }

    def run_doctor(
        self,
        signal_channels: list[str] | None = None,
        jellyfin_url: str | None = None,
        jellyfin_api_key: str | None = None,
        validate_device_auth_cloud: bool = False,
    ) -> dict[str, Any]:
        """Run every check and return the aggregate report."""
        reachable = self.check_device_reachable()
        checks = [reachable]
        info = reachable.get("detail") if reachable["status"] == "pass" else None
        device_id = (info or {}).get("DeviceID", "")

        if info is not None:
            checks.append(self.check_firmware_model(info))
            checks.append(
                self.check_tuner_count_vs_jellyfin(
                    jellyfin_url, jellyfin_api_key, device_id, info
                )
            )
            checks.append(self.check_device_auth(info, validate_device_auth_cloud))
        else:
            checks.append(
                {
                    "check": "firmware_model",
                    "status": "skip",
                    "detail": "device unreachable",
                }
            )
            checks.append(
                {
                    "check": "tuner_count_vs_jellyfin",
                    "status": "skip",
                    "detail": "device unreachable",
                }
            )
            checks.append(
                {
                    "check": "device_auth",
                    "status": "skip",
                    "detail": "device unreachable",
                }
            )

        if signal_channels:
            checks.append(self.check_signal_strength(signal_channels))
        else:
            checks.append(
                {
                    "check": "signal_strength",
                    "status": "skip",
                    "detail": "no channels requested",
                }
            )

        checks.append(self.check_discovery_cache_freshness())

        overall = "pass"
        if any(c["status"] == "fail" for c in checks):
            overall = "fail"
        elif any(c["status"] == "warn" for c in checks):
            overall = "warn"
        return {"overall": overall, "checks": checks}
