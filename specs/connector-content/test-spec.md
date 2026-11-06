# CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |
| T-002 | `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R003` | `tests/test_set_lockkey.py::test_lock_sets_the_key_and_release_presents_it` | Locking sends a numeric key and returns it; releasing sends `none` with that key. |
