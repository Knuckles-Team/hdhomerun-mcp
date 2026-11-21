# CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |
| T-002 | `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R003` | `tests/test_set_lockkey.py::test_lock_sets_the_key_and_release_presents_it` | Locking sends a numeric key and returns it; releasing sends `none` with that key. |
| T-003 | `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R004` | `tests/test_ontology_core_rollup.py` | Every class of every module has a path to a core class. |
| T-004 | `CONN-HDHOMERUN-MCP-CONNECTOR-CONTENT-R005` | `tests/test_ontology_extends_core.py::test_pack_declares_no_core_term` | The served Turtle declares none of the listed core terms. |
