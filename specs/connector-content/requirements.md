# CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `hdhomerun-mcp` as the single `agent_connector_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
| `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R002` | **Recording-rules source reads the served tool's own result.** The `hdhomerun-recording-rules` source names the served tool `hdhomerun_list_recording_rules`, which returns the rule list itself (not a `rules` wrapper like the retired action tool), so its `records_path` is empty. | `tests/test_connector_sources.py::test_recording_rules_source_reads_the_served_tool_result_list`. |
