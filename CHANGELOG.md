# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added the packaged `hdhomerun-mcp-development` skill and source-backed Pages
  spec dashboard publication contract.

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
