"""civil3d MCP server — alignments, profiles, surfaces, corridors and pipe networks via the Civil 3D add-in.
Writes only by the 'infra' discipline agent."""
from __future__ import annotations

from typing import Any

from ..core.guard import require_discipline_write
from ..core.server import tool_errors
from ._bridged import BridgedApp

app = BridgedApp("civil3d", "Civil 3D", instructions=(
    "Civil 3D drawing data. Read freely; modifications need `agent`='infra'."))
mcp = app.mcp


@mcp.tool()
@tool_errors
def get_drawing_info() -> Any:
    """Active drawing, coordinate system, units, data shortcuts project."""
    return app.call("get_drawing_info")


@mcp.tool()
@tool_errors
def list_alignments() -> Any:
    """Alignments with length, start/end station, design speed."""
    return app.call("list_alignments")


@mcp.tool()
@tool_errors
def get_alignment(name: str, station_interval_m: float = 20) -> Any:
    """Alignment geometry (tangents/curves/spirals) and sampled stations."""
    return app.call("get_alignment", name=name, station_interval_m=station_interval_m)


@mcp.tool()
@tool_errors
def list_profiles(alignment: str) -> Any:
    """Profiles of an alignment (EG / design) with grades and VPIs."""
    return app.call("list_profiles", alignment=alignment)


@mcp.tool()
@tool_errors
def list_surfaces() -> Any:
    """TIN/grid surfaces with statistics (min/max elevation, area)."""
    return app.call("list_surfaces")


@mcp.tool()
@tool_errors
def list_corridors() -> Any:
    """Corridors with baselines, regions and assemblies."""
    return app.call("list_corridors")


@mcp.tool()
@tool_errors
def list_networks(kind: str = "all") -> Any:
    """Pipe (gravity) and pressure networks (kind: all | pipe | pressure)."""
    return app.call("list_networks", kind=kind)


@mcp.tool()
@tool_errors
def get_network_parts(network: str) -> Any:
    """Pipes and structures of a network: sizes, inverts, slopes, rims, connectivity."""
    return app.call("get_network_parts", network=network)


@mcp.tool()
@tool_errors
def check_network_rules(network: str, min_cover_m: float = 0.9, min_slope_pct: float = 0.5) -> Any:
    """Rule check: cover, slope, velocity flags per pipe."""
    return app.call("check_network_rules", network=network, min_cover_m=min_cover_m, min_slope_pct=min_slope_pct)


@mcp.tool()
@tool_errors
def set_object_properties(agent: str, handles: list[str], values: dict[str, Any], reason: str) -> Any:
    """WRITE: set properties on Civil 3D objects (by handle). infra only."""
    require_discipline_write(app.ctx.project, agent, "infra")
    return app.call("set_object_properties", handles=handles, values=values, reason=reason)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
