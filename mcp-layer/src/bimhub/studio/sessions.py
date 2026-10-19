"""One Claude Code session per (project, agent), so every agent remembers its own conversation."""
from __future__ import annotations

import json
from pathlib import Path

from .engine import new_session_id


class Sessions:
    def __init__(self, state_dir: Path):
        self.f = state_dir / "studio-sessions.json"

    def _all(self) -> dict:
        return json.loads(self.f.read_text(encoding="utf-8")) if self.f.is_file() else {}

    def get(self, agent: str) -> tuple[str, bool]:
        """(session_id, is_new)."""
        d = self._all()
        if agent in d:
            return d[agent], False
        sid = new_session_id()
        d[agent] = sid
        self.f.parent.mkdir(parents=True, exist_ok=True)
        self.f.write_text(json.dumps(d, indent=1), encoding="utf-8")
        return sid, True

    def reset(self, agent: str) -> None:
        d = self._all()
        d.pop(agent, None)
        self.f.write_text(json.dumps(d, indent=1), encoding="utf-8")
