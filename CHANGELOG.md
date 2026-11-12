# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.11] - 2026-11-12

### Changed
- The hand-written `action`-routed tools (`http_operations`, `discovery_operations`, `dvr_operations`, `config_operations`, `doctor_operations`) are removed. Every HDHomeRun operation is served as one typed tool per client method (`hdhomerun_get_lineup`, `hdhomerun_set_channel`, `hdhomerun_run_doctor`, ...). The discovery cache read and the device, lineup and recording-rule ingest operations are typed tools of their own (`hdhomerun_read_discovery_cache`, `hdhomerun_ingest_device`, `hdhomerun_ingest_lineup`, `hdhomerun_ingest_recording_rules`). The `HTTPTOOL`, `DISCOVERYTOOL`, `DVRTOOL`, `CONFIGTOOL` and `DOCTORTOOL` toggles are gone with the routers.
- Declare tool-use contracts, prompt and skill links, data locations and business roles; ship an operator and two business-role agent prompts; root every ontology class in a core class.
- Require `scion-sdk>=0.9.0,<0.10.0`.

## [1.3.10] - 2026-11-06

### Fixed
- `hdhomerun_set_lockkey` locks a tuner with the caller's 32-bit key (random when omitted, returned) and releases it with `none` plus that key; it previously sent the literal `set` and the device answered `invalid lockkey` (CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R003).
- Require `scion-sdk>=0.6.5` so destructive tools accept `confirm=true`.

## [Unreleased]

### Added
- Added the packaged `hdhomerun-mcp-development` skill and source-backed Pages
  spec dashboard publication contract.

## [1.3.9] - 2026-10-30

### Changed
- Require `scion-sdk>=0.6.4,<0.7.0`; `uv.lock` relocked.

## [1.3.6] - 2026-10-24

### Changed
- Central connector migration: requires `agent-connector-sdk>=0.5.4`; server bootstrap, version, containers, ontology artifacts, security scaffold and pre-commit config are provided centrally.

## [1.3.4] - 2026-10-23

### Changed
- Requires `agent-connector-sdk>=0.4.1`; data sources are declared in code (`connector_sources`).

## [0.1.0] - 2026-07-19

### Added
- Initial release.
- Modular subfolders for API wrappers (`api/`) and action-routed MCP tools (`mcp/`).
- Material-theme mkdocs documentation site (7 standard pages).
- Full pre-commit quality gate and flat `tests/` structure.
