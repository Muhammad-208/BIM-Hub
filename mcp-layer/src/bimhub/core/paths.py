"""Locations of the hub, its config and projects. One place, so nothing else hard-codes paths."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError, ProjectNotFound


def _default_root() -> Path:
    # mcp-layer/src/bimhub/core/paths.py → hub root is 4 levels up
    return Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class HubPaths:
    root: Path

    @classmethod
    def discover(cls) -> "HubPaths":
        root = Path(os.environ.get("BIMHUB_ROOT") or _default_root()).resolve()
        if not (root / "learning-hub").is_dir():
            raise ConfigError(f"BIM Hub root not found at {root} (set BIMHUB_ROOT)")
        return cls(root)

    @property
    def agents(self) -> Path: return self.root / "agents"
    @property
    def hub(self) -> Path: return self.root / "learning-hub"
    @property
    def skills(self) -> Path: return self.hub / "skills"
    @property
    def lessons(self) -> Path: return self.hub / "lessons"
    @property
    def projects(self) -> Path: return self.root / "projects"
    @property
    def template(self) -> Path: return self.projects / "_template"
    @property
    def config(self) -> Path: return self.root / "mcp-layer" / "config"

    def project_dir(self, code: str | None = None) -> Path:
        code = code or os.environ.get("BIMHUB_PROJECT")
        if not code:
            raise ProjectNotFound("No project selected (BIMHUB_PROJECT is not set)")
        p = self.projects / code
        if not (p / "project.yaml").is_file():
            raise ProjectNotFound(f"Project '{code}' not found under {self.projects}")
        return p

    def list_projects(self) -> list[str]:
        if not self.projects.is_dir():
            return []
        return sorted(p.name for p in self.projects.iterdir()
                      if p.is_dir() and not p.name.startswith("_") and (p / "project.yaml").is_file())
