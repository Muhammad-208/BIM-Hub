"""A project = projects/<CODE>/project.yaml + its folders.

Team model:
  core agents (L2–L4) ............ bim-manager, bim-coordinator, qa-model, qa-data, qa-doc
  per discipline on the team (L1)  <disc>-leader, <disc>-modeler, <disc>-drafter, <disc>-clash, <disc>-info
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import load_yaml
from .paths import HubPaths

CORE_AGENTS = ["bim-manager", "bim-coordinator", "qa-model", "qa-data", "qa-doc"]
LAYER_OF = {"bim-manager": 4, "bim-coordinator": 3, "qa-model": 2, "qa-data": 2, "qa-doc": 2}
ROLES = ["leader", "modeler", "drafter", "clash", "info"]
ROLE_TITLES = {"leader": "Leader", "modeler": "Modeler", "drafter": "Drafter", "clash": "Clash resolver",
               "info": "Information editor"}


def split_agent(agent: str) -> tuple[str | None, str | None]:
    """'mech-clash' → ('mech', 'clash'); core agents → (None, None)."""
    if agent in LAYER_OF:
        return None, None
    disc, _, role = agent.rpartition("-")
    return (disc, role) if disc and role in ROLES else (None, None)


@dataclass
class Project:
    code: str
    dir: Path
    data: dict[str, Any]

    @classmethod
    def load(cls, paths: HubPaths, code: str | None = None) -> "Project":
        d = paths.project_dir(code)
        data = load_yaml(d / "project.yaml")
        return cls(code=data.get("code") or d.name, dir=d, data=data)

    @property
    def name(self) -> str: return self.data.get("name", self.code)
    @property
    def disciplines(self) -> dict[str, dict]: return self.data.get("disciplines", {}) or {}
    @property
    def team(self) -> list[str]:
        """Disciplines on this project (e.g. ['arc', 'str', 'mech'])."""
        return [t.strip().lower() for t in (self.data.get("team") or [])]
    @property
    def roles(self) -> list[str]:
        r = [x.strip().lower() for x in (self.data.get("roles") or ROLES)]
        if "leader" not in r:
            r.insert(0, "leader")
        return [x for x in ROLES if x in r]
    @property
    def discipline_agents(self) -> list[str]:
        return [f"{d}-{r}" for d in self.team for r in self.roles]
    @property
    def all_agents(self) -> list[str]: return CORE_AGENTS + self.discipline_agents
    @property
    def naming(self) -> dict: return self.data.get("naming", {}) or {}
    @property
    def mcp(self) -> list[str]: return list(self.data.get("mcp") or ["bimhub"])
    @property
    def state_dir(self) -> Path: return self.dir / "05-state"
    @property
    def inbox_dir(self) -> Path: return self.dir / "07-lessons-inbox"
    @property
    def exports(self) -> dict: return self.data.get("exports", {}) or {}
    @property
    def shared_parameters(self) -> list[dict]: return list(self.data.get("shared_parameters") or [])
    @property
    def type_id(self) -> str | None: return (self.data.get("type") or None) and str(self.data["type"]).strip() or None
    @property
    def params(self) -> dict: return self.data.get("params", {}) or {}

    def layer(self, agent: str) -> int:
        return LAYER_OF.get(agent, 1)

    def normalize(self, name: str) -> str:
        """A bare discipline name ('mech') means its leader."""
        n = (name or "").strip().lower()
        return f"{n}-leader" if n in self.team else n

    def discipline_for_role(self, role_code: str) -> str | None:
        for disc, cfg in self.disciplines.items():
            if str(cfg.get("role", "")).upper() == role_code.upper():
                return disc
        return None
