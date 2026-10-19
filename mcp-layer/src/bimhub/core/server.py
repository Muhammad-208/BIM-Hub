"""Common factory: every BIM Hub MCP server gets the same identity + health tools and error style."""
from __future__ import annotations

import functools
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # SDK 1.x
    from mcp.server.fastmcp import FastMCP

from .. import __version__
from .errors import BimHubError
from .log import get_logger
from .paths import HubPaths
from .project import Project


class HubContext:
    """Lazily resolved hub + current project, shared by a server's tools."""

    def __init__(self) -> None:
        self.paths = HubPaths.discover()
        self._project: Project | None = None

    @property
    def project(self) -> Project:
        if self._project is None:
            self._project = Project.load(self.paths)
        return self._project


def make_server(name: str, instructions: str) -> tuple[FastMCP, HubContext]:
    os.environ.setdefault("BIMHUB_SERVER", name)
    mcp = FastMCP(f"bimhub-{name}", instructions=instructions)
    ctx = HubContext()

    @mcp.tool()
    def server_info() -> dict[str, Any]:
        """Which BIM Hub server this is, the hub root and the active project."""
        info: dict[str, Any] = {"server": name, "version": __version__, "hub_root": str(ctx.paths.root),
                                "project": os.environ.get("BIMHUB_PROJECT")}
        try:
            p = ctx.project
            info.update(project_name=p.name, team=p.all_agents)
        except BimHubError as e:
            info["project_error"] = str(e)
        return info

    return mcp, ctx


_ACTIVITY: Path | None | bool = None


def _activity_path() -> Path | None:
    """05-state/activity.jsonl of the active project, or None (cached)."""
    global _ACTIVITY
    if _ACTIVITY is None:
        try:
            _ACTIVITY = HubPaths.discover().project_dir() / "05-state" / "activity.jsonl"
        except Exception:  # noqa: BLE001
            _ACTIVITY = False
    return _ACTIVITY or None


def _log_activity(tool: str, kwargs: dict, ok: bool, result: Any) -> None:
    """Every MCP tool call → one line in activity.jsonl. The Studio app tails it (works for Claude Code
    sessions started anywhere, not only from the Studio)."""
    p = _activity_path()
    if not p:
        return
    try:
        brief = {k: v for k, v in kwargs.items() if k != "agent" and isinstance(v, (str, int, float, bool))}
        rec = {"at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
               "server": os.environ.get("BIMHUB_SERVER", "?"), "tool": tool, "agent": kwargs.get("agent"),
               "ok": ok, "args": {k: (str(v)[:80]) for k, v in list(brief.items())[:4]}}
        if not ok and isinstance(result, dict):
            rec["error"] = str(result.get("error", ""))[:200]
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — logging must never break a tool
        pass


def tool_errors(fn: Callable) -> Callable:
    """Turn BimHubError into a clean message for the agent instead of a stack trace, and log the call."""
    @functools.wraps(fn)
    def wrapper(*a, **kw):
        try:
            result = fn(*a, **kw)
            _log_activity(fn.__name__, kw, True, result)
            return result
        except BimHubError as e:
            get_logger("bimhub").info("tool %s refused: %s", fn.__name__, e)
            result = {"ok": False, "error": str(e)}
            _log_activity(fn.__name__, kw, False, result)
            return result
    return wrapper
