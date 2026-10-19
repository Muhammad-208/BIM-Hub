"""Shared plumbing for MCP servers that drive a desktop app through a Bridge."""
from __future__ import annotations

from pathlib import PurePath
from typing import Any

from ..core.bridge import Bridge, make_bridge
from ..core.config import load_servers
from ..core.server import HubContext, make_server
from ..knowledge.naming import validate_name


class BridgedApp:
    def __init__(self, server_name: str, app: str, instructions: str):
        self.server_name, self.app = server_name, app
        self.mcp, self.ctx = make_server(server_name, instructions)
        self._bridge: Bridge | None = None

        @self.mcp.tool(name=f"{server_name}_health")
        def health() -> dict[str, Any]:
            """Is the desktop app reachable? Returns app, version and active document."""
            try:
                return {"ok": True, **self.bridge.health()}
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "error": str(e)}

    @property
    def bridge(self) -> Bridge:
        if self._bridge is None:
            cfg = load_servers(self.ctx.paths).get(self.server_name)
            self._bridge = make_bridge(cfg.bridge if cfg else None, self.app)
        return self._bridge

    def call(self, command: str, **args: Any) -> Any:
        return self.bridge.call(command, args)

    def active_discipline(self, ctx: HubContext | None = None) -> str | None:
        """Discipline of the active document: project.yaml → models mapping first, then the ISO 19650 role field."""
        ctx = ctx or self.ctx
        doc = str(self.bridge.health().get("document") or "")
        if not doc:
            return None
        p = ctx.project
        stem = PurePath(doc).stem.lower()
        for disc, path in (p.data.get("models") or {}).items():
            if PurePath(str(path)).stem.lower() == stem:
                return disc
        parsed = validate_name(PurePath(doc).name, p.naming, p.code)
        role = (parsed.get("fields") or {}).get("role")
        return p.discipline_for_role(role) if role else None
