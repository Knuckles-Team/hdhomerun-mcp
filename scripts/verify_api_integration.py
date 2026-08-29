#!/usr/bin/env python3
import os
import ast
import glob
import sys

BASELINES = {
    "adguard-home-agent": 89.2,
    "ansible-tower-mcp": 94.7,
    "archivebox-api": 85.7,
    "documentdb-mcp": 100.0,
    "github-agent": 100.0,
    "gitlab-api": 6.4,
    "home-assistant-agent": 63.6,
    "jellyfin-mcp": 81.0,
    "langfuse-agent": 100.0,
    "listmonk-api": 87.5,
    "mealie-mcp": 96.4,
    "microsoft-agent": 99.6,
    "nextcloud-agent": 52.6,
    "owncast-agent": 100.0,
    "plane-agent": 54.9,
    "portainer-agent": 35.5,
    "postiz-agent": 0.0,
    "qbittorrent-agent": 70.8,
    "scholarx": 90.0,
    "servicenow-api": 73.1,
    "stirlingpdf-agent": 0.0,
    "wger-agent": 41.7,
}


def _is_api_or_client_class(node: ast.ClassDef) -> bool:
    class_name = node.name.lower()
    return "api" in class_name or "client" in class_name or node.name == "Api"


def _is_public_client_method(item: ast.stmt) -> bool:
    return (
        isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not item.name.startswith("_")
        and item.name != "authenticate"
    )


def _collect_public_methods(node: ast.ClassDef) -> dict:
    return {
        item.name: {"line": item.lineno, "class": node.name}
        for item in node.body
        if _is_public_client_method(item)
    }


def parse_api_client(filepath):
    """
    Parses api_client.py to find the main API/Client class and its public methods.
    Returns a set of method names.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and _is_api_or_client_class(node):
            methods.update(_collect_public_methods(node))
    return methods


class MethodCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.called_methods = set()
        self.action_literals = set()

    def visit_Attribute(self, node):
        # E.g. client.get_repositories
        if isinstance(node.value, ast.Name):
            # Typically client, api, self
            if node.value.id in ("client", "api", "self"):
                self.called_methods.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node):
        # E.g. getattr(client, "foo")
        if isinstance(node.func, ast.Name) and node.func.id == "getattr":
            if len(node.args) >= 2 and isinstance(node.args[0], ast.Name):
                if node.args[0].id in ("client", "api"):
                    if isinstance(node.args[1], ast.Constant):
                        self.called_methods.add(node.args[1].value)
        self.generic_visit(node)

    def visit_Compare(self, node):
        # Capture action comparisons, e.g. action == "get"
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Eq, ast.In)):
                if isinstance(comparator, ast.Constant) and isinstance(
                    comparator.value, str
                ):
                    self.action_literals.add(comparator.value)
        self.generic_visit(node)


def _decorator_is_tool(dec: ast.expr) -> bool:
    if isinstance(dec, ast.Call):
        func = dec.func
        return isinstance(func, ast.Attribute) and func.attr == "tool"
    return isinstance(dec, ast.Attribute) and dec.attr == "tool"


_TOOL_NAME_PREFIXES = ("github_", "gitlab_", "adguard_", "atlassian_")


def _function_is_tool(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if any(_decorator_is_tool(dec) for dec in node.decorator_list):
        return True
    return node.name.startswith(_TOOL_NAME_PREFIXES)


def _map_tool_function(node, api_methods: dict) -> dict:
    visitor = MethodCallVisitor()
    visitor.visit(node)
    mapped = visitor.called_methods.intersection(api_methods.keys())
    return {
        "mapped": mapped,
        "entry": {"methods": list(mapped), "actions": list(visitor.action_literals)},
    }


def parse_mcp_server(filepath, api_methods):
    """
    Parses mcp_server.py to extract registered tools and identify which
    api_methods they leverage.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=filepath)

    tool_mappings = {}
    all_mapped_methods = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _function_is_tool(node):
            continue
        mapping = _map_tool_function(node, api_methods)
        tool_mappings[node.name] = mapping["entry"]
        all_mapped_methods.update(mapping["mapped"])

    return tool_mappings, all_mapped_methods


def verify_agent(agent_dir):
    # Find api_client.py and mcp_server.py
    api_clients = glob.glob(
        os.path.join(agent_dir, "**", "api_client.py"), recursive=True
    )
    mcp_servers = glob.glob(
        os.path.join(agent_dir, "**", "mcp_server.py"), recursive=True
    )

    if not api_clients or not mcp_servers:
        return None

    api_client_path = api_clients[0]
    mcp_server_path = mcp_servers[0]

    api_methods = parse_api_client(api_client_path)
    if not api_methods:
        return None

    tool_mappings, mapped_methods = parse_mcp_server(mcp_server_path, api_methods)

    total_methods = len(api_methods)
    covered_methods = len(mapped_methods)
    coverage = (covered_methods / total_methods) * 100 if total_methods > 0 else 0.0

    unmapped = set(api_methods.keys()) - mapped_methods

    return {
        "agent_name": os.path.basename(agent_dir),
        "api_client": api_client_path,
        "mcp_server": mcp_server_path,
        "total_methods": total_methods,
        "covered_methods": covered_methods,
        "coverage": coverage,
        "unmapped": sorted(list(unmapped)),
        "mapped": sorted(list(mapped_methods)),
        "tool_mappings": tool_mappings,
    }


def _run_local_check(cwd: str) -> int:
    """Verify the single agent rooted at `cwd`. Returns the process exit code."""
    res = verify_agent(cwd)
    if not res:
        # If no client or server found in this dir, pass silently (e.g. non-python files, doc edits)
        print(
            "Skipping integration parity verification: No mcp_server.py/api_client.py found in current directory."
        )
        return 0

    agent_name = res["agent_name"]
    coverage = res["coverage"]
    baseline = BASELINES.get(agent_name, 0.0)

    print(f"=== API-to-MCP Integration Parity Check for: {agent_name} ===")
    print(f"- API client methods: {res['total_methods']}")
    print(f"- Integrated methods: {res['covered_methods']}")
    print(f"- Current Coverage  : {coverage:.1f}%")
    print(f"- Target Baseline   : {baseline:.1f}%")

    # Allow small floating point tolerance (0.05%)
    if coverage < (baseline - 0.05):
        print(
            f"\n❌ FAILED: Integration coverage ({coverage:.1f}%) has DEGRADED below the required baseline of {baseline:.1f}%!"
        )
        print(
            "Please ensure any new or refactored API client methods are properly integrated into MCP server tools."
        )
        if res["unmapped"]:
            print("\nUnmapped API methods:")
            for m in res["unmapped"]:
                print(f"  - {m}")
        return 1

    print("\n✅ PASSED: Integration coverage meets or exceeds the required baseline!")
    return 0


def _discover_agent_dirs(agents_dir: str) -> list:
    agent_dirs = [
        d for d in glob.glob(os.path.join(agents_dir, "*")) if os.path.isdir(d)
    ]
    # Also support nested subdirectories if any
    nested_dirs = [
        d for d in glob.glob(os.path.join(agents_dir, "*", "*")) if os.path.isdir(d)
    ]
    all_dirs = sorted(set(agent_dirs + nested_dirs))
    return [
        d
        for d in all_dirs
        if not (
            os.path.basename(d).startswith(".")
            or "venv" in d
            or "egg-info" in d
        )
    ]


def _scan_workspace(agents_dir: str) -> list:
    results = []
    for agent_dir in _discover_agent_dirs(agents_dir):
        try:
            res = verify_agent(agent_dir)
            if res:
                results.append(res)
        except Exception as e:
            print(f"Error parsing {agent_dir}: {e}", file=sys.stderr)
    return results


def _print_summary_table(results: list) -> None:
    print("| Agent Name | API Methods | Covered Methods | Coverage % | Status |")
    print("|---|---|---|---|---|")
    for r in results:
        status = "✅ 100%" if r["coverage"] >= 100.0 else "⚠️ Parity Gap"
        print(
            f"| {r['agent_name']} | {r['total_methods']} | {r['covered_methods']} | {r['coverage']:.1f}% | {status} |"
        )


def _print_parity_gap(agents_dir: str, r: dict) -> None:
    print(f"### ⚠️ {r['agent_name']} ({r['coverage']:.1f}% Integration)")
    print(f"- **API Client**: `{os.path.relpath(r['api_client'], agents_dir)}`")
    print(f"- **MCP Server**: `{os.path.relpath(r['mcp_server'], agents_dir)}`")
    print("- **Unmapped API Methods**:")
    for m in r["unmapped"]:
        print(f"  - `{m}`")
    print()


def _print_full_parity(r: dict) -> None:
    print(f"### ✅ {r['agent_name']} (100% Integration)")
    print(f"- All {r['total_methods']} methods successfully mapped to MCP tools.")
    print()


def _print_detailed_gaps(results: list, agents_dir: str) -> None:
    print("\n## Detailed Parity Gaps\n")
    for r in results:
        if r["coverage"] < 100.0:
            _print_parity_gap(agents_dir, r)
        else:
            _print_full_parity(r)


def _run_workspace_report() -> None:
    agents_dir = "/home/apps/workspace/agent-packages/agents"
    results = _scan_workspace(agents_dir)

    print("# API to MCP Integration Parity Report")
    print(f"Scan Directory: `{agents_dir}`\n")
    _print_summary_table(results)
    _print_detailed_gaps(results, agents_dir)


def main():
    args = sys.argv[1:]

    # --- Local Mode (Single Agent Validation) ---
    if "--local" in args or "--pre-commit" in args:
        sys.exit(_run_local_check(os.getcwd()))

    # --- Default Mode (Workspace-wide Scan) ---
    _run_workspace_report()


if __name__ == "__main__":
    main()
