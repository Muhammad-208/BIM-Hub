"""revit MCP server — talks to the BIM Hub Revit add-in (addins/revit, Revit 2020–2027, localhost:8766).
Read tools are open to the whole team; write tools only for the discipline that owns the active model."""
from __future__ import annotations

from typing import Any

from pathlib import Path, PurePath

from ..core.guard import NWC_EXPORTERS, require_discipline_write, require_member
from ..core.server import tool_errors
from ._bridged import BridgedApp

app = BridgedApp("revit", "Revit", instructions=(
    "Revit tools for the active document. Read freely. Writes (set_parameters…) need your `agent` name and are "
    "allowed only if you own the discipline of the active model. Upper layers create issues instead of editing."))
mcp = app.mcp


@mcp.tool()
@tool_errors
def get_model_info() -> Any:
    """Active document: title, path, Revit version, worksharing, levels, phases, base points, units."""
    return app.call("get_model_info")


@mcp.tool()
@tool_errors
def list_elements(category: str, limit: int = 500, parameter_filter: dict[str, str] | None = None) -> Any:
    """Elements of a Revit category (e.g. 'OST_StructuralFraming' or 'Structural Framing'), with id, UniqueId,
    type, level. Optional parameter_filter {param: value}."""
    return app.call("list_elements", category=category, limit=limit, parameter_filter=parameter_filter)


@mcp.tool()
@tool_errors
def get_element_parameters(element_ids: list[str], parameter_names: list[str] | None = None) -> Any:
    """Instance + type parameters of elements (ElementId or UniqueId). Optionally only the named parameters."""
    return app.call("get_element_parameters", element_ids=element_ids, parameter_names=parameter_names)


@mcp.tool()
@tool_errors
def list_warnings(limit: int = 1000) -> Any:
    """Revit warnings grouped by description, with element ids and counts."""
    return app.call("list_warnings", limit=limit)


@mcp.tool()
@tool_errors
def audit_model() -> Any:
    """Model-health snapshot for qa-model: worksets, in-place families, CAD imports, links (path type),
    unused views/sheets, file size, warnings count."""
    return app.call("audit_model")


@mcp.tool()
@tool_errors
def list_views_and_sheets(kind: str = "all") -> Any:
    """Views and/or sheets (kind: all | views | sheets) with names, numbers, templates."""
    return app.call("list_views_and_sheets", kind=kind)


@mcp.tool()
@tool_errors
def get_selection() -> Any:
    """Elements currently selected by the user in Revit."""
    return app.call("get_selection")


@mcp.tool()
@tool_errors
def show_elements(element_ids: list[str], isolate: bool = False) -> Any:
    """Select and zoom to elements in the active view (optionally isolate temporarily). Does not change the model."""
    return app.call("show_elements", element_ids=element_ids, isolate=isolate)


@mcp.tool()
@tool_errors
def export_ifc(agent: str, output_folder: str, file_name: str | None = None, ifc_version: str | None = None,
               view_id: str | None = None) -> Any:
    """Export the active model to IFC (any team member). file_name must be the rendition's OWN ISO 19650 ID —
    never the native model's ID. ifc_version e.g. IFC2x3CV2 | IFC4RV | IFC4. view_id limits to a 3D view.
    The model is not changed (the add-in rolls its transaction back)."""
    require_member(app.ctx.project, agent)
    return app.call("export_ifc", output_folder=output_folder, file_name=file_name, ifc_version=ifc_version,
                    view_id=view_id)


@mcp.tool()
@tool_errors
def set_parameters(agent: str, element_ids: list[str], values: dict[str, Any], reason: str) -> Any:
    """WRITE: set INSTANCE parameter values in ONE all-or-nothing transaction (any failure → nothing changes,
    errors returned). Strings for length/area params use display units ("2400 mm"); numbers = Revit internal
    units. Only the discipline owning the active model may call this. `reason` goes into the transaction name."""
    require_discipline_write(app.ctx.project, agent, app.active_discipline())
    return app.call("set_parameters", element_ids=element_ids, values=values,
                    transaction=f"BIM Hub · {agent} · {reason}"[:120])


@mcp.tool()
@tool_errors
def export_nwc(agent: str, file_name: str | None = None, view_name: str | None = None) -> Any:
    """[clash resolver / modeler of the model's discipline] Export the active model to NWC in the AGREED
    folder (project.yaml → exports.nwc; may contain {DISC}; default 03-coordination/nwc/{DISC}).
    file_name defaults to the model's file name. view_name = a 3D view to export (default: whole model).
    Needs the Navisworks exporter for Revit installed on this PC."""
    p = app.ctx.project
    disc = app.active_discipline()
    require_discipline_write(p, agent, disc, roles=NWC_EXPORTERS, action="export NWC of")
    folder = str(p.exports.get("nwc") or "03-coordination/nwc/{DISC}").replace("{DISC}", (disc or "").upper())
    if not Path(folder).is_absolute() and not PurePath(folder).drive:
        folder = str(p.dir / folder)
    return app.call("export_nwc", output_folder=folder, file_name=file_name, view_name=view_name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
