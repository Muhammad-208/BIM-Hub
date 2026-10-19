"""bimhub MCP server — Learning Hub + project state + lessons + naming. Pure Python, no desktop app needed.

Run:  python -m bimhub.servers.hub      (env: BIMHUB_PROJECT=<CODE>, optional BIMHUB_ROOT)
"""
from __future__ import annotations

import re
import shutil
from typing import Any

from ..core.errors import BimHubError
from ..core.guard import require_layer, require_member, require_role
from ..core.project import split_agent
from ..core import project_types as ptypes
from ..core.server import make_server, tool_errors
from ..knowledge.naming import validate_name
from ..knowledge.search import parse_md, search
from ..state.store import ExtraState, StateStore, now
from ..reports.dashboard import render as render_dashboard
from ..files import sources as srcmod
from ..files.readers import read_file

mcp, ctx = make_server("hub", instructions=(
    "BIM Hub core tools. Search the shared Learning Hub before answering from general knowledge. "
    "Use issue_/decision_/message_/model_status_ tools for ALL project state. Always pass your agent name "
    "(e.g. 'str', 'qa-model', 'bim-manager') in the `agent` argument."))


def _store() -> StateStore:
    return StateStore(ctx.project.state_dir)


# ───────────────────────── Learning Hub ─────────────────────────
@mcp.tool()
@tool_errors
def hub_search(query: str, limit: int = 8, scope: str | None = None) -> list[dict[str, Any]]:
    """Search the shared Learning Hub (knowledge, skills, lessons). scope: optional sub-folder such as
    'knowledge/00-standards', 'knowledge/02-disciplines/str', 'skills', 'lessons'."""
    return [h.__dict__ for h in search(ctx.paths.hub, query, limit, scope)]


@mcp.tool()
@tool_errors
def hub_read(path: str) -> dict[str, Any]:
    """Read one Learning Hub file by its hub-relative path (as returned by hub_search)."""
    p = (ctx.paths.hub / path).resolve()
    if ctx.paths.hub.resolve() not in p.parents and p != ctx.paths.hub.resolve():
        raise BimHubError("Path is outside the Learning Hub")
    if not p.is_file():
        raise BimHubError(f"Not found: {path}")
    meta, body = parse_md(p)
    return {"path": path, "meta": meta, "content": body}


@mcp.tool()
@tool_errors
def project_info() -> dict[str, Any]:
    """Active project: code, name, stage, team, disciplines/scopes, naming, models, standards."""
    p = ctx.project
    t = ptypes.get_type(ctx.paths, p.type_id) if p.type_id else None
    return {"code": p.code, "dir": str(p.dir), **{k: v for k, v in p.data.items() if k != "code"},
            "team_full": p.all_agents,
            "project_type": {"id": t["id"], "title": t.get("title"), "skills": t.get("skills")} if t else None}


# ───────────────────────── Workflow (project type) ─────────────────────────
@mcp.tool()
@tool_errors
def workflow_get(discipline: str | None = None) -> dict:
    """This project's workflow from its project type: stages, owners, QA gates, outputs and current status.
    Read it before starting work; discipline filters per-discipline items."""
    p = ctx.project
    t = ptypes.get_type(ctx.paths, p.type_id) if p.type_id else None
    if not t:
        return {"type": None, "stages": [], "note": "No project type set — add `type:` to project.yaml (bimhub types)."}
    stages = ptypes.workflow_view(p, t, _extra().workflow())
    if discipline:
        d = discipline.lower()
        for s in stages:
            s["items"] = [i for i in s["items"] if i["discipline"] in (None, d)]
    return {"type": t["id"], "title": t.get("title"), "params": p.params or t.get("params") or {}, "stages": stages}


@mcp.tool()
@tool_errors
def stage_update(agent: str, stage: str, status: str, discipline: str | None = None, note: str | None = None,
                 evidence: str | None = None) -> dict:
    """Move a workflow stage: todo | in-progress | review | qa-pass | qa-fail | done | blocked.
    Owner/support set in-progress/review/blocked; the stage's QA gate sets qa-pass/qa-fail; only bim-coordinator /
    bim-manager set done (after qa-pass when the stage has a gate). Per-discipline stages need `discipline`
    (inferred for discipline agents). evidence = report path / issue ids."""
    p = ctx.project
    t = ptypes.get_type(ctx.paths, p.type_id) if p.type_id else None
    if not t:
        raise BimHubError("This project has no type — workflow stages are not defined")
    ex = _extra()
    s = ptypes.stage_of(t, stage)
    a = require_member(p, agent)
    key, disc = ptypes.check_stage_update(p, t, a, stage, status, discipline, ex.workflow())
    r = ex.stage_set(a, key, status, note, evidence, p.layer(a))
    if status == "done":
        _store().decision_log(a, f"Stage {key} done", s.get("title", ""), note or "workflow gate", "stage_update")
    if status == "qa-fail":
        for o in ptypes.responsible(p, s, disc)["owner"]:
            _store().message_send(a, o, f"QA fail on {key} — fix and resubmit", evidence, "high", note)
    return r


# ───────────────────────── Issues ─────────────────────────
@mcp.tool()
@tool_errors
def issue_create(agent: str, title: str, owner: str, priority: str = "medium", description: str | None = None,
                 location: str | None = None, elements: list[str] | None = None, viewpoint: str | None = None,
                 source: str | None = None, due: str | None = None) -> dict[str, Any]:
    """Create an issue. owner = responsible agent (e.g. 'mech-clash'; a bare discipline 'mech' = its leader). priority: critical|high|medium|low.
    elements = GUIDs/ids; source = clash group, QA report, standard clause…"""
    p = ctx.project
    by = require_member(p, agent)
    owner = require_member(p, owner)
    return _store().issue_create(by, title, owner, priority, description=description, location=location,
                                 elements=elements, viewpoint=viewpoint, source=source, due=due)


@mcp.tool()
@tool_errors
def issue_update(agent: str, issue_id: str, status: str | None = None, comment: str | None = None,
                 owner: str | None = None, priority: str | None = None,
                 elements: list[str] | None = None) -> dict[str, Any]:
    """Update an issue (status: open|in-progress|resolved|closed|rejected). Only L2+ may close or reject."""
    p = ctx.project
    by = require_member(p, agent)
    if status in ("closed", "rejected"):
        require_layer(p, agent, 2, f"set an issue to {status}")
    if owner:
        owner = require_member(p, owner)
    return _store().issue_update(by, issue_id, status=status, comment=comment, owner=owner,
                                 priority=priority, elements=elements)


@mcp.tool()
@tool_errors
def issue_list(status: str | None = None, owner: str | None = None, priority: str | None = None) -> list[dict]:
    """List issues, optionally filtered by status / owner / priority."""
    return _store().issue_list(status, ctx.project.normalize(owner) if owner else None, priority)


@mcp.tool()
@tool_errors
def issue_get(issue_id: str) -> dict[str, Any]:
    """One issue with its full history."""
    return _store().issue_get(issue_id)


# ───────────────────────── Decisions ─────────────────────────
@mcp.tool()
@tool_errors
def decision_log(agent: str, title: str, decision: str, reason: str, source: str | None = None) -> dict:
    """Record a project decision (L3+): what was decided, why, and the evidence/source."""
    by = require_layer(ctx.project, agent, 3, "log decisions")
    return _store().decision_log(by, title, decision, reason, source)


@mcp.tool()
@tool_errors
def decision_list(limit: int = 50) -> list[dict]:
    """Most recent project decisions."""
    return _store().decisions.read()[-limit:]


# ───────────────────────── Messages between agents ─────────────────────────
@mcp.tool()
@tool_errors
def message_send(agent: str, to: str, task: str, ref: str | None = None, priority: str = "medium",
                 body: str | None = None) -> dict:
    """Send a hand-off to another agent (envelope: from, to, task, ref, priority). to='all' broadcasts."""
    p = ctx.project
    by = require_member(p, agent)
    if to != "all":
        to = require_member(p, to)
    return _store().message_send(by, to, task, ref, priority, body)


@mcp.tool()
@tool_errors
def message_inbox(agent: str, include_done: bool = False) -> list[dict]:
    """Messages addressed to you (or 'all') that are not done yet."""
    return _store().message_inbox(require_member(ctx.project, agent), include_done)


@mcp.tool()
@tool_errors
def message_ack(agent: str, message_id: str, status: str = "done") -> dict:
    """Mark a message read | in-progress | done."""
    return _store().message_ack(require_member(ctx.project, agent), message_id, status)


# ───────────────────────── Model / container status (CDE) ─────────────────────────
@mcp.tool()
@tool_errors
def model_status_get(container: str | None = None) -> dict:
    """CDE state and QA verdicts per container (all, or one)."""
    return _store().model_status_get(container)


@mcp.tool()
@tool_errors
def model_status_set(agent: str, container: str, state: str | None = None, qa_model: str | None = None,
                     qa_data: str | None = None, qa_doc: str | None = None, revision: str | None = None,
                     suitability: str | None = None, note: str | None = None) -> dict:
    """Update a container's CDE status. Rules: each QA agent sets only its own verdict (PASS|PASS WITH
    COMMENTS|FAIL); SHARED needs all three QA = PASS*; PUBLISHED/ARCHIVE only by bim-manager."""
    p = ctx.project
    by = require_member(p, agent)
    store = _store()
    qa = {"qa_model": qa_model, "qa_data": qa_data, "qa_doc": qa_doc}
    for field, value in qa.items():
        if value is not None and by != field.replace("_", "-"):
            raise BimHubError(f"Only {field.replace('_', '-')} may set {field}")
    if state in ("PUBLISHED", "ARCHIVE") and by != "bim-manager":
        raise BimHubError("Only bim-manager may publish or archive")
    if state == "SHARED":
        require_layer(p, by, 2, "promote to SHARED")
        cur = store.model_status_get().get(container, {})
        merged = {k: (v or cur.get(k)) for k, v in qa.items()}
        missing = [k for k, v in merged.items() if not (v or "").startswith("PASS")]
        if missing:
            raise BimHubError(f"Cannot promote to SHARED: {', '.join(missing)} not PASS yet")
    if state == "PUBLISHED":
        cur = store.model_status_get().get(container, {})
        if cur.get("state") != "SHARED":
            raise BimHubError("Only SHARED containers can be published")
    return store.model_status_set(by, container, state=state, qa_model=qa_model, qa_data=qa_data,
                                  qa_doc=qa_doc, revision=revision, suitability=suitability, note=note)


# ───────────────────────── Lessons → Learning Hub ─────────────────────────
def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "lesson"


@mcp.tool()
@tool_errors
def lesson_propose(agent: str, title: str, context: str, what_happened: str, rule: str, evidence: str,
                   target: str = "lessons", tags: list[str] | None = None) -> dict:
    """Propose a reusable lesson for the shared Learning Hub (reviewed by bim-manager). No client names/prices."""
    p = ctx.project
    by = require_member(p, agent)
    p.inbox_dir.mkdir(exist_ok=True)
    lid = f"{now()[:10]}-{p.code}-{_slug(title)}"
    path = p.inbox_dir / f"{lid}.md"
    tag_list = ", ".join(tags or [])
    path.write_text(
        f"---\ntitle: \"{title}\"\nid: {lid}\nstatus: pending\nproposed_by: {by}\nproject: {p.code}\n"
        f"target: {target}\ntags: [{tag_list}]\nproposed_at: {now()}\n---\n\n"
        f"## Context\n{context}\n\n## What happened\n{what_happened}\n\n## Rule\n{rule}\n\n## Evidence\n{evidence}\n",
        encoding="utf-8")
    return {"id": lid, "status": "pending", "path": str(path)}


@mcp.tool()
@tool_errors
def lesson_list_pending() -> list[dict]:
    """Lesson proposals waiting for bim-manager review in this project."""
    out = []
    for f in sorted(ctx.project.inbox_dir.glob("*.md")):
        meta, body = parse_md(f)
        if meta.get("status") == "pending":
            out.append({**meta, "body": body.strip()})
    return out


def _set_inbox_status(lid: str, status: str, extra: str = "") -> Any:
    f = ctx.project.inbox_dir / f"{lid}.md"
    if not f.is_file():
        raise BimHubError(f"Lesson {lid} not found in the inbox")
    text = f.read_text(encoding="utf-8").replace("status: pending", f"status: {status}{extra}", 1)
    f.write_text(text, encoding="utf-8")
    return f


@mcp.tool()
@tool_errors
def lesson_approve(agent: str, lesson_id: str, target: str | None = None) -> dict:
    """bim-manager only: approve a lesson into the shared Learning Hub (learning-hub/lessons/).
    Run `bimhub sync` afterwards (or tell the user to) so every project sees it."""
    if require_member(ctx.project, agent) != "bim-manager":
        raise BimHubError("Only bim-manager may approve lessons")
    src = _set_inbox_status(lesson_id, "approved", f"\napproved_by: {agent}\napproved_at: {now()}")
    ctx.paths.lessons.mkdir(parents=True, exist_ok=True)
    dst = ctx.paths.lessons / src.name
    shutil.copyfile(src, dst)
    if target:
        dst.write_text(dst.read_text(encoding="utf-8").replace("target: ", f"target: {target}  # was: ", 1),
                       encoding="utf-8")
    return {"approved": lesson_id, "hub_path": f"lessons/{dst.name}"}


@mcp.tool()
@tool_errors
def lesson_reject(agent: str, lesson_id: str, reason: str) -> dict:
    """bim-manager only: reject a lesson proposal with a reason (it stays in the project inbox)."""
    if require_member(ctx.project, agent) != "bim-manager":
        raise BimHubError("Only bim-manager may reject lessons")
    reason_yaml = reason.replace("\n", " ").replace('"', "'")
    _set_inbox_status(lesson_id, "rejected", f"\nrejected_by: {agent}\nreject_reason: \"{reason_yaml}\"")
    return {"rejected": lesson_id}


# ───────────────────────── Coordination zones (drafting gate) ─────────────────────────
def _extra() -> ExtraState:
    return ExtraState(ctx.project.state_dir)


@mcp.tool()
@tool_errors
def zone_set(agent: str, zone: str, status: str, note: str | None = None,
             disciplines: list[str] | None = None) -> dict:
    """[coordinator/manager] Set a coordination zone's status: open | in-coordination | coordinated | on-hold.
    zone = level/area/system id agreed in the BEP (e.g. 'L03', 'L03-ZoneB', 'Basement-MEP-plant').
    Drafters may only draft in zones marked coordinated."""
    by = require_layer(ctx.project, agent, 3, "change coordination zones")
    r = _extra().zone_set(by, zone, status, note, disciplines)
    if status == "coordinated":
        _store().decision_log(by, f"Zone {zone} coordinated", "Drafting released for this zone", note or "coordination review",
                              "zone_set")
    return r


@mcp.tool()
@tool_errors
def zone_list() -> dict:
    """All coordination zones and their status (drafting is allowed only where status = coordinated)."""
    return {k: {kk: vv for kk, vv in v.items() if kk != "history"} for k, v in _extra().zones().items()}


@mcp.tool()
@tool_errors
def drafting_clearance(agent: str, zone: str) -> dict:
    """[drafter] Call BEFORE producing any sheet/view for a zone. ok=true only if the coordinator marked it coordinated
    (and, if the zone lists disciplines, yours is included)."""
    disc, _ = require_role(ctx.project, agent, ("drafter", "leader"), "ask for drafting clearance")
    z = _extra().zones().get(zone)
    if not z:
        return {"ok": False, "zone": zone, "reason": "zone not defined — ask bim-coordinator"}
    if z.get("status") != "coordinated":
        return {"ok": False, "zone": zone, "status": z.get("status"), "reason": "not coordinated yet"}
    if z.get("disciplines") and disc not in [d.lower() for d in z["disciplines"]]:
        return {"ok": False, "zone": zone, "reason": f"{disc} not included in this zone's clearance"}
    return {"ok": True, "zone": zone, "cleared_by": z.get("by"), "at": z.get("at")}


# ───────────────────────── Model health ─────────────────────────
@mcp.tool()
@tool_errors
def health_submit(agent: str, model: str, score: float, checks: list[dict], report: str | None = None) -> dict:
    """[information editor / qa-model] Submit a model-health result: score 0–100 and checks
    [{name, status: pass|fail|warn, found, expected}], report = path of the source report (e.g. Model Checker xlsx)."""
    p = ctx.project
    a = require_member(p, agent)
    disc, role = split_agent(a)
    if a != "qa-model" and role != "info":
        raise BimHubError("Only an information editor (<disc>-info) or qa-model may submit model health")
    return _extra().health_submit(a, disc or "all", model, score, checks, report)


@mcp.tool()
@tool_errors
def health_latest(discipline: str | None = None) -> list[dict]:
    """Latest model-health report per model (optionally one discipline)."""
    return _extra().health_latest(discipline)


# ───────────────────────── Dashboards ─────────────────────────
@mcp.tool()
@tool_errors
def dashboard_publish(agent: str, kind: str, spec: dict) -> dict:
    """[coordinator/manager] Publish a dashboard as HTML in 06-reports/dashboards/. kind: clashes | project-info |
    shared-parameters | model-health | <any>. spec: {title, subtitle, kpis:[{label,value,tone good|bad|warn}],
    bars:[{title, items:[{label,value}]}], tables:[{title, columns, rows}], notes:[…]}.
    Gather the data first (navisworks clash/property tools, health_latest, files_find, model_status_get)."""
    by = require_layer(ctx.project, agent, 3, "publish dashboards")
    import re as _re
    k = _re.sub(r"[^a-z0-9-]+", "-", kind.lower()).strip("-") or "dashboard"
    out_dir = ctx.project.dir / "06-reports" / "dashboards"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now()
    page = render_dashboard(spec, f"{ctx.project.code} — {ctx.project.name}", stamp, by)
    latest = out_dir / f"{k}.html"
    dated = out_dir / f"{k}-{stamp[:10]}.html"
    latest.write_text(page, encoding="utf-8")
    dated.write_text(page, encoding="utf-8")
    entry = {"kind": k, "title": spec.get("title"), "by": by, "at": stamp,
             "path": f"06-reports/dashboards/{latest.name}", "kpis": spec.get("kpis") or []}
    _extra().dashboard_register(k, entry)
    return entry


@mcp.tool()
@tool_errors
def dashboard_list() -> dict:
    """Latest dashboard of each kind (title, KPIs, path)."""
    return _extra().dashboards()


# ───────────────────────── Project files (sources) ─────────────────────────
@mcp.tool()
@tool_errors
def source_list() -> list[dict]:
    """The folders this project's agents may read: the project folder plus every source in project.yaml
    (local paths, ACC via Desktop Connector, ACC web links for the Chrome skill)."""
    return [{"name": s.name, "type": s.type, "path": str(s.path) if s.path else None, "url": s.url,
             "readable": s.readable, "include": s.include, "exclude": s.exclude} for s in srcmod.sources(ctx.project)]


@mcp.tool()
@tool_errors
def files_scan(source: str | None = None) -> dict:
    """(Re)index all project files (metadata only): kind, size, date, ISO 19650 name check, discipline.
    Run it when files were added/changed. Big ACC folders can take a minute."""
    return srcmod.scan(ctx.project, only=source)


@mcp.tool()
@tool_errors
def files_find(query: str | None = None, kind: str | None = None, discipline: str | None = None,
               source: str | None = None, limit: int = 100) -> dict:
    """Search the file index. kind: revit-model | ifc | navisworks-cache | navisworks-document |
    navisworks-fileset | word | excel | pdf | text | csv | dwg | … ; discipline: arc, str, mech…
    query: words that must all appear in the path (e.g. 'EIR', 'L03 MECH')."""
    return srcmod.find(ctx.project, query, kind, discipline, source, limit)


@mcp.tool()
@tool_errors
def file_read(source: str, path: str, max_chars: int = 30000, sheet: str | None = None,
              pages: str | None = None) -> dict:
    """Read one project file by source + path (as returned by files_find).
    TXT/CSV/MD/JSON/XML, DOCX (text + tables), XLSX (sheet rows), PDF (pages '3-7'), PPTX, IFC (schema, storeys,
    element counts by type) → content. RVT/RFA (version, worksharing, central path), NWC/NWD/NWF, DWG → metadata
    only; the result's open_with names the MCP that reads full content through the app."""
    return read_file(srcmod.resolve(ctx.project, source, path), max_chars=max_chars, sheet=sheet, pages=pages)


# ───────────────────────── Naming ─────────────────────────
@mcp.tool()
@tool_errors
def naming_validate(names: list[str] | None = None, folder: str | None = None) -> dict:
    """Validate container names against project.yaml → naming. Give a list of names, or a project-relative
    folder (e.g. '02-cde/WIP/ARC') to check every file in it."""
    p = ctx.project
    items = list(names or [])
    if folder:
        d = (p.dir / folder).resolve()
        if p.dir.resolve() not in d.parents and d != p.dir.resolve():
            raise BimHubError("Folder must be inside the project")
        items += [f.name for f in d.rglob("*") if f.is_file() and not f.name.startswith(".")]
    results = [validate_name(n, p.naming, p.code) for n in items]
    bad = [r for r in results if not r["valid"]]
    return {"checked": len(results), "failed": len(bad), "results": bad + [r for r in results if r["valid"]]}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
