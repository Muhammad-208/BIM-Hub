"""Project types (learning-hub/project-types/<id>.yaml): workflow stages, gates, roles, params per kind of job.

A stage `owner` / `support` entry is either a discipline role (leader, modeler, drafter, clash, info → applies to
every discipline on the team, stage tracked per discipline when `per_discipline: true`) or a core agent name.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import BimHubError
from .paths import HubPaths
from .project import CORE_AGENTS, ROLE_TITLES, ROLES, Project, split_agent

STAGE_STATES = ("todo", "in-progress", "review", "qa-pass", "qa-fail", "done", "blocked")


def types_dir(paths: HubPaths) -> Path:
    return paths.hub / "project-types"


def load_types(paths: HubPaths) -> dict[str, dict]:
    d = types_dir(paths)
    out: dict[str, dict] = {}
    for f in sorted(d.glob("*.yaml")) if d.is_dir() else []:
        t = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        tid = t.get("id") or f.stem
        t["id"] = tid
        for s in t.get("stages") or []:
            for who in [s.get("owner")] + list(s.get("support") or []) + list(s.get("gate") or []):
                if who and who not in ROLES and who not in CORE_AGENTS:
                    raise BimHubError(f"{f.name}: stage {s.get('id')}: unknown owner/support/gate '{who}'")
        out[tid] = t
    return out


def get_type(paths: HubPaths, type_id: str | None) -> dict | None:
    if not type_id:
        return None
    types = load_types(paths)
    if type_id not in types:
        raise BimHubError(f"Unknown project type '{type_id}'. Available: {', '.join(types)}")
    return types[type_id]


def stage_of(t: dict, stage_id: str) -> dict:
    for s in t.get("stages") or []:
        if s["id"].upper() == stage_id.upper():
            return s
    raise BimHubError(f"Stage '{stage_id}' not in type {t['id']}: {', '.join(s['id'] for s in t.get('stages') or [])}")


def _agents_for(p: Project, who: str, disc: str | None) -> list[str]:
    if who in CORE_AGENTS:
        return [who]
    if who not in p.roles:
        return []
    return [f"{d}-{who}" for d in ([disc] if disc else p.team)]


def stage_keys(p: Project, s: dict) -> list[tuple[str, str | None]]:
    """[(key, discipline)] — 'S3:mech' per discipline, or 'S2' once."""
    if s.get("per_discipline") and s.get("owner") in ROLES:
        return [(f"{s['id']}:{d}", d) for d in p.team]
    return [(s["id"], None)]


def responsible(p: Project, s: dict, disc: str | None) -> dict[str, list[str]]:
    return {"owner": _agents_for(p, s.get("owner", ""), disc),
            "support": [a for w in s.get("support") or [] for a in _agents_for(p, w, disc)],
            "gate": [g for g in s.get("gate") or [] if g in CORE_AGENTS]}


def workflow_view(p: Project, t: dict | None, state: dict[str, Any]) -> list[dict]:
    """Stages with resolved agents and current status (from 05-state/workflow.yaml)."""
    if not t:
        return []
    out = []
    for s in t.get("stages") or []:
        items = []
        for key, disc in stage_keys(p, s):
            st = state.get(key, {})
            items.append({"key": key, "discipline": disc, "status": st.get("status", "todo"), "by": st.get("by"),
                          "at": st.get("at"), "note": st.get("note"), "qa": st.get("qa", {}),
                          **responsible(p, s, disc)})
        done = sum(1 for i in items if i["status"] == "done")
        out.append({"id": s["id"], "title": s.get("title"), "owner": s.get("owner"), "support": s.get("support") or [],
                    "gate": s.get("gate") or [], "optional": bool(s.get("optional")), "outputs": s.get("outputs") or [],
                    "done_when": s.get("done_when"), "items": items, "done": done, "total": len(items),
                    "status": ("done" if done == len(items) else
                               "blocked" if any(i["status"] == "blocked" for i in items) else
                               "todo" if all(i["status"] == "todo" for i in items) else "in-progress")})
    return out


def check_stage_update(p: Project, t: dict, agent: str, stage_id: str, status: str,
                       discipline: str | None, state: dict) -> tuple[str, str | None]:
    """Who may set what. Returns (key, discipline). Raises ScopeError-like BimHubError."""
    from .guard import require_member
    if status not in STAGE_STATES:
        raise BimHubError(f"status must be one of {STAGE_STATES}")
    a = require_member(p, agent)
    s = stage_of(t, stage_id)
    disc_of_agent, role = split_agent(a)
    keys = stage_keys(p, s)
    if len(keys) > 1:
        disc = (discipline or disc_of_agent or "").lower()
        if disc not in p.team:
            raise BimHubError(f"Stage {s['id']} is tracked per discipline — pass discipline (one of {', '.join(p.team)})")
        key = f"{s['id']}:{disc}"
    else:
        disc, key = None, s["id"]
    r = responsible(p, s, disc)
    current = state.get(key, {})
    layer = p.layer(a)
    if status in ("qa-pass", "qa-fail"):
        if a not in r["gate"] and layer < 3:
            raise BimHubError(f"Only the gate ({', '.join(r['gate']) or 'L3+'}) may set {status} on {key}")
    elif status == "done":
        if layer < 3:
            raise BimHubError(f"{key}: 'done' is set by bim-coordinator / bim-manager"
                              + (f" after qa-pass from {', '.join(r['gate'])}" if r["gate"] else ""))
        if r["gate"] and current.get("status") != "qa-pass":
            raise BimHubError(f"{key} needs qa-pass from {', '.join(r['gate'])} before done (now: "
                              f"{current.get('status', 'todo')})")
    else:
        if a not in r["owner"] + r["support"] and layer < 3:
            raise BimHubError(f"{a} is not owner/support of {key} (owner: {', '.join(r['owner'])})")
    return key, disc


def render_workflow_md(p: Project, t: dict) -> str:
    params = p.data.get("params") or t.get("params") or {}
    L = [f"# Workflow — {p.code} · {t.get('title')} (`{t['id']}`)", "",
         f"> {str(t.get('summary', '')).strip()}", "",
         "Generated by `bimhub sync` from `learning-hub/project-types/" + t["id"] + ".yaml` — do not edit; "
         "project overrides go in `project.yaml → params` or `team-notes/`.", "",
         "## Rules", "- Track every stage with `stage_update(agent, stage, status, discipline?, note?, evidence?)`; "
         "read progress with `workflow_get()`.",
         "- Status flow: todo → in-progress → review → qa-pass / qa-fail (gate QA agent) → done (bim-coordinator / bim-manager).",
         "- Never start a stage whose previous non-optional stage is not done for your discipline — ask your leader.", ""]
    if params:
        L += ["## Parameters", *[f"- `{k}`: {v}" for k, v in params.items()], ""]
    if t.get("inputs"):
        L += ["## Inputs expected", *[f"- {x}" for x in t["inputs"]], ""]
    L += ["## Stages", "", "| # | Stage | Owner | Support | QA gate | Per discipline |", "|---|---|---|---|---|---|"]
    for s in t.get("stages") or []:
        own = ROLE_TITLES.get(s.get("owner"), s.get("owner"))
        L.append(f"| {s['id']} | {s.get('title')}{' *(optional)*' if s.get('optional') else ''} | {own} | "
                 f"{', '.join(ROLE_TITLES.get(x, x) for x in s.get('support') or []) or '—'} | "
                 f"{', '.join(s.get('gate') or []) or '—'} | {'yes' if s.get('per_discipline') else '—'} |")
    L.append("")
    for s in t.get("stages") or []:
        L += [f"### {s['id']} · {s.get('title')}", *[f"- Output: {o}" for o in s.get("outputs") or []],
              f"- Done when: {s.get('done_when', '')}", ""]
    if t.get("role_notes"):
        L += ["## Role notes for this project type"]
        for r, n in t["role_notes"].items():
            L.append(f"- **{ROLE_TITLES.get(r, r)}** ({r}): {' '.join(str(n).split())}")
        L.append("")
    if t.get("skills"):
        L += ["## Skills to use", ", ".join(f"`{x}`" for x in t["skills"]), ""]
    if t.get("deliverables"):
        L += ["## Deliverables", *[f"- {x}" for x in t["deliverables"]], ""]
    if t.get("kpis"):
        L += ["## KPIs (coordinator dashboards)", *[f"- {x}" for x in t["kpis"]], ""]
    return "\n".join(L)
