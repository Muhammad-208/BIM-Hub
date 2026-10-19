"""navisworks MCP server — adapter for the existing MCPBridge add-in (E:\\MCP\\Navisworks_MCP\\addin, port 8765).

Layers:
  read & visual tools ........ everyone on the team
  clash / sets / viewpoints .. bim-coordinator and bim-manager only (L3+), `agent` argument required
Visual tools work on the CURRENT SELECTION (that is how the add-in is built): select first, then color/isolate/hide.
"""
from __future__ import annotations

from typing import Any, Literal

from ..core.guard import require_layer
from ..core.server import tool_errors
from ._bridged import BridgedApp

app = BridgedApp("navisworks", "Navisworks", instructions=(
    "Navisworks federated model via the MCPBridge add-in (click 'MCP Bridge' once in the Add-Ins ribbon after "
    "opening Navisworks). Read and visual tools are open to everyone. Creating/running/grouping clashes, "
    "sets and viewpoints needs `agent` = bim-coordinator or bim-manager. Visual tools act on the current selection."))
mcp = app.mcp

Op = Literal["equals", "contains", "startsWith", "endsWith"]
ClashStatus = Literal["New", "Active", "Reviewed", "Approved", "Resolved"]


def _coord(agent: str) -> None:
    require_layer(app.ctx.project, agent, 3, "change clash tests, sets or viewpoints")


# ───────────── document ─────────────
@mcp.tool()
@tool_errors
def get_document_info() -> Any:
    """Open federated document: file, appended models, units."""
    return app.call("get_document_info")


@mcp.tool()
@tool_errors
def get_model_statistics() -> Any:
    """Element counts grouped by class."""
    return app.call("get_model_statistics")


# ───────────── find / select (read) ─────────────
@mcp.tool()
@tool_errors
def find_items(value: str, category: str = "Item", property: str = "Name", operator: Op = "contains",
               limit: int = 50, select_results: bool = False) -> Any:
    """Single-condition property search (e.g. category='Element', property='Category', value='Ducts').
    select_results=True also selects them in the viewport (needed before visual tools)."""
    return app.call("find_items", category=category, property=property, operator=operator, value=value,
                    limit=limit, select=select_results)


@mcp.tool()
@tool_errors
def find_items_by_name(pattern: str, limit: int = 50, select_results: bool = True) -> Any:
    """Quick search by element name (substring)."""
    return app.call("find_items_by_name", pattern=pattern, limit=limit, select=select_results)


@mcp.tool()
@tool_errors
def get_element_properties(name: str | None = None) -> Any:
    """All property tabs of the first selected element, or of the element with this name."""
    return app.call("get_element_properties", name=name)


@mcp.tool()
@tool_errors
def selection(action: Literal["get", "select_all", "deselect_all", "invert", "from_set"],
              set_name: str | None = None) -> Any:
    """Viewport selection: get | select_all | deselect_all | invert | from_set (needs set_name)."""
    cmd = {"get": "get_current_selection", "select_all": "select_all", "deselect_all": "deselect_all",
           "invert": "invert_selection", "from_set": "select_from_set"}[action]
    return app.call(cmd, name=set_name) if action == "from_set" else app.call(cmd)


@mcp.tool()
@tool_errors
def list_sets() -> Any:
    """All selection sets and search sets."""
    return app.call("list_sets")


@mcp.tool()
@tool_errors
def get_set_items(name: str) -> Any:
    """Elements stored in a named selection set."""
    return app.call("get_set_items", name=name)


@mcp.tool()
@tool_errors
def run_search_set(name: str) -> Any:
    """Run a saved search set and return the count of matching elements."""
    return app.call("run_search_set", name=name)


# ───────────── visual (current selection, not saved data) ─────────────
@mcp.tool()
@tool_errors
def visualize(action: Literal["color", "transparency", "hide", "isolate", "unhide_all", "reset"],
              r: int = 255, g: int = 0, b: int = 0, transparency: float = 0.5) -> Any:
    """Visual override on the CURRENT SELECTION: color (r,g,b) | transparency (0..1) | hide | isolate;
    or unhide_all / reset (all overrides). Use find_items(select_results=True) or selection() first."""
    if action == "color":
        return app.call("color_selection", r=r, g=g, b=b)
    if action == "transparency":
        return app.call("set_transparency", transparency=transparency)
    return app.call({"hide": "hide_selection", "isolate": "isolate_selection",
                     "unhide_all": "unhide_all", "reset": "reset_overrides"}[action])


# ───────────── clash (read) ─────────────
@mcp.tool()
@tool_errors
def list_clash_tests() -> Any:
    """Clash tests with status and result counts."""
    return app.call("list_clash_tests")


@mcp.tool()
@tool_errors
def get_clash_results(test_name: str, max_results: int = 100) -> Any:
    """Clash results of a test."""
    return app.call("get_clash_results", name=test_name, limit=max_results)


@mcp.tool()
@tool_errors
def list_clash_groups(test_name: str) -> Any:
    """Clash groups in a test, with their child clash names."""
    return app.call("list_clash_groups", test_name=test_name)


@mcp.tool()
@tool_errors
def viewpoints(action: Literal["list", "current", "goto"], name: str | None = None) -> Any:
    """Viewpoints: list | current camera | goto (needs name)."""
    if action == "goto":
        return app.call("goto_viewpoint", name=name)
    return app.call("list_viewpoints" if action == "list" else "get_current_viewpoint")


# ───────────── L3+ : sets ─────────────
@mcp.tool()
@tool_errors
def create_search_set(agent: str, name: str, value: str, category: str = "Item", property: str = "Name",
                      operator: Op = "contains") -> Any:
    """[L3+] Saved search with one property condition — used as clash-matrix sides."""
    _coord(agent)
    return app.call("create_search_set", name=name, category=category, property=property,
                    operator=operator, value=value)


@mcp.tool()
@tool_errors
def create_selection_set(agent: str, name: str) -> Any:
    """[L3+] Selection set from the current viewport selection."""
    _coord(agent)
    return app.call("create_selection_set", name=name)


@mcp.tool()
@tool_errors
def delete_set(agent: str, name: str) -> Any:
    """[L3+] Delete a selection or search set."""
    _coord(agent)
    return app.call("delete_set", name=name)


# ───────────── L3+ : clash tests ─────────────
@mcp.tool()
@tool_errors
def create_clash_test(agent: str, name: str, selection_a: str | None = None, selection_b: str | None = None,
                      clash_type: Literal["Hard", "Clearance", "Duplicate"] = "Hard",
                      tolerance: float = 0.001) -> Any:
    """[L3+] Create a clash test; selection_a/b = names of selection or search sets.
    tolerance is in the Navisworks document units (check get_document_info; 0.025 = 25 mm if metres)."""
    _coord(agent)
    return app.call("create_clash_test", name=name, type=clash_type, tolerance=tolerance,
                    selectionA=selection_a, selectionB=selection_b)


@mcp.tool()
@tool_errors
def set_clash_selections(agent: str, test_name: str, selection_a: str | None = None,
                         selection_b: str | None = None) -> Any:
    """[L3+] Attach sets to side A and/or B of an existing test."""
    _coord(agent)
    return app.call("set_clash_selections", name=test_name, selectionA=selection_a, selectionB=selection_b)


@mcp.tool()
@tool_errors
def run_clash_test(agent: str, test_name: str | None = None) -> Any:
    """[L3+] Run one clash test, or all if test_name is omitted."""
    _coord(agent)
    return app.call("run_clash_test", name=test_name)


@mcp.tool()
@tool_errors
def delete_clash_test(agent: str, test_name: str) -> Any:
    """[L3+] Delete a clash test."""
    _coord(agent)
    return app.call("delete_clash_test", name=test_name)


@mcp.tool()
@tool_errors
def group_clashes(agent: str, test_name: str, group_name: str, clash_names: list[str]) -> Any:
    """[L3+] One real problem = one group: creates the group (if needed) and moves the clashes
    (display names, e.g. 'Clash12') into it."""
    _coord(agent)
    existing = app.call("list_clash_groups", test_name=test_name)
    names = {g.get("name") for g in (existing.get("groups", []) if isinstance(existing, dict) else existing or [])
             if isinstance(g, dict)}
    created = None
    if group_name not in names:
        created = app.call("create_clash_group", test_name=test_name, group_name=group_name)
    moved = app.call("add_clashes_to_group", test_name=test_name, group_name=group_name, clash_names=clash_names)
    return {"group": group_name, "created": created, "moved": moved}


@mcp.tool()
@tool_errors
def set_clash_group_status(agent: str, test_name: str, group_name: str, status: ClashStatus) -> Any:
    """[L3+] Review status of a clash group."""
    _coord(agent)
    return app.call("set_clash_group_status", test_name=test_name, group_name=group_name, status=status)


@mcp.tool()
@tool_errors
def delete_clash_group(agent: str, test_name: str, group_name: str) -> Any:
    """[L3+] Delete a clash group and its child results."""
    _coord(agent)
    return app.call("delete_clash_group", test_name=test_name, group_name=group_name)


# ───────────── L3+ : viewpoints ─────────────
@mcp.tool()
@tool_errors
def save_viewpoint(agent: str, name: str) -> Any:
    """[L3+] Save the current camera as a named viewpoint (name it after the issue id, e.g. 'ISS-0012')."""
    _coord(agent)
    return app.call("save_viewpoint", name=name)


@mcp.tool()
@tool_errors
def delete_viewpoint(agent: str, name: str) -> Any:
    """[L3+] Delete a saved viewpoint."""
    _coord(agent)
    return app.call("delete_viewpoint", name=name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
