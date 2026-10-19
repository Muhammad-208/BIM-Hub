"""Write-scope rules. MCP does not tell a server WHICH subagent is calling, so write tools take an
`agent` argument and we enforce the hierarchy here. It is a safety net against mistakes, not security."""
from __future__ import annotations

from .errors import ScopeError
from .project import Project, split_agent

# Which L1 roles may change the model, per kind of change.
MODEL_WRITERS = ("modeler", "clash", "info")       # set_parameters
NWC_EXPORTERS = ("clash", "modeler")


def require_member(project: Project, agent: str) -> str:
    a = project.normalize(agent)
    if a not in project.all_agents:
        raise ScopeError(f"'{agent}' is not on the team of {project.code}. Team: {', '.join(project.all_agents)}")
    return a


def require_layer(project: Project, agent: str, min_layer: int, action: str) -> str:
    a = require_member(project, agent)
    if project.layer(a) < min_layer:
        raise ScopeError(f"{a} (L{project.layer(a)}) may not {action}; needs L{min_layer}+")
    return a


def require_role(project: Project, agent: str, roles: tuple[str, ...], action: str) -> tuple[str, str]:
    """Agent must be an L1 discipline agent with one of `roles`. Returns (discipline, role)."""
    a = require_member(project, agent)
    disc, role = split_agent(a)
    if role not in roles:
        raise ScopeError(f"{a} may not {action} — only the {' / '.join(roles)} role(s) of a discipline can")
    return disc, role


def require_discipline_write(project: Project, agent: str, discipline: str | None,
                             roles: tuple[str, ...] = MODEL_WRITERS, action: str = "modify") -> str:
    """Only the owning discipline's modeler / clash resolver / information editor may modify its model."""
    a = require_member(project, agent)
    if project.layer(a) > 1:
        raise ScopeError(f"{a} is L{project.layer(a)} — upper layers review and assign, they don't edit models. "
                         "Create an issue for the discipline instead.")
    disc, role = split_agent(a)
    if role not in roles:
        raise ScopeError(f"{a} may not {action} the model — the {role} role doesn't; "
                         f"ask {disc}-{roles[0]}.")
    if discipline is None:
        raise ScopeError("Cannot determine the discipline of the active model; refusing to write. "
                         "Name it per ISO 19650 (role field) or map it in project.yaml → models.")
    if disc != discipline.lower():
        raise ScopeError(f"{a} may not {action} the {discipline.upper()} model — assign an issue to {discipline}.")
    return a
