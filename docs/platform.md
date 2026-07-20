# Backing Platform — HDHomeRun MCP

`hdhomerun-mcp` is a client of **real HDHomeRun hardware**, not a deployable
software service — there is no Docker recipe here, by design (matching the
PARITY_MANIFEST convention of documenting the omission for
managed/hardware-only backing systems, e.g. `clarity-api`).

## The backing platform is a physical network tuner

A [SiliconDust HDHomeRun](https://www.silicondust.com/) unit (FLEX, CONNECT,
PRIME, SCRIBE, SERVIO, EXTEND, EXPAND, or DUAL) sits on your LAN and exposes:

- The **HTTP JSON API** on its normal HTTP port (discover.json/lineup.json/etc).
- Streaming video on **TCP 5004**.
- Local UDP **discovery** and the binary **hdhomerun_config control protocol**,
  both on **port 65001** (UDP for discovery, TCP for control).

Point `HDHOMERUN_URL` at the device's IP or a stable hostname
(`http://10.0.132.114` or `http://hdhomerun.arpa` behind an ingress/reverse
proxy) — no software install is required on the network side.

## Optional: SiliconDust DVR record engine

If you also run a SiliconDust DVR record engine (HDHomeRun SCRIBE/SERVIO
hardware, or the desktop/NAS record-engine software), it is itself another
device on the network with its own `BaseURL`/`discover.json` — see
`hdhr-dvr-ops` for its local API surface. There is likewise no container image
for it; it is either dedicated hardware or a vendor-distributed installer, not
a Dockerized service this package deploys.

## Local development without real hardware

For unit tests, mock the client's HTTP/socket calls (see `tests/`) rather than
standing up a fake device — the wire protocols (binary TLV framing, UDP
discovery, TCP control) are validated in this package's own test suite
against captures from a real HDHomeRun FLEX 4K, so mocking at the
`requests`/`socket` boundary is representative.
