"""BIM Hub Studio API (FastAPI). Start with `bimhub studio` → http://localhost:8800

The UI never talks to Claude directly: it posts chat messages here; the engine runs Claude Code
(subscription or API key) inside projects/<CODE>; every event is pushed to the UI over Server-Sent Events,
together with live MCP activity (05-state/activity.jsonl) from ANY Claude Code session on this PC.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from ..core.errors import BimHubError
from ..core.paths import HubPaths
from ..core.project import CORE_AGENTS, ROLE_TITLES, LAYER_OF, Project, split_agent
from ..files import sources as srcmod
from ..knowledge.search import parse_md
from ..state.store import ExtraState, StateStore, now
from .engine import ClaudeCodeEngine, auth_status
from .prompting import build_prompt
from .sessions import Sessions
from .settings import StudioSettings


CORE_TITLES = {"bim-manager": "BIM Manager", "bim-coordinator": "BIM Coordinator", "qa-model": "QA · Model",
               "qa-data": "QA · Data", "qa-doc": "QA · Docs"}


class Bus:
    """Fan-out of events to every open UI connection, per project."""

    def __init__(self) -> None:
        self.subs: dict[str, set[asyncio.Queue]] = {}
        self.watchers: dict[str, asyncio.Task] = {}

    def subscribe(self, code: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=2000)
        self.subs.setdefault(code, set()).add(q)
        return q

    def unsubscribe(self, code: str, q: asyncio.Queue) -> None:
        self.subs.get(code, set()).discard(q)

    def publish(self, code: str, event: dict) -> None:
        event.setdefault("at", now())
        for q in list(self.subs.get(code, set())):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


def _jsonl_tail(path: Path, n: int) -> list[dict]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    return out


def create_app(paths: HubPaths | None = None) -> FastAPI:
    paths = paths or HubPaths.discover()
    app = FastAPI(title="BIM Hub Studio", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:1420", "http://localhost:5173",
                                                      "tauri://localhost", "http://tauri.localhost"],
                       allow_methods=["*"], allow_headers=["*"])
    bus = Bus()
    running: dict[str, dict] = {}

    def project(code: str) -> Project:
        try:
            return Project.load(paths, code.upper())
        except BimHubError as e:
            raise HTTPException(404, str(e)) from e

    def agent_info(p: Project, a: str) -> dict:
        disc, role = split_agent(a)
        return {"id": a, "layer": p.layer(a), "discipline": disc, "role": role,
                "title": (f"{disc.upper()} · {ROLE_TITLES[role]}" if disc else CORE_TITLES.get(a, a))}

    # ─────────────── meta & settings ───────────────
    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "hub": str(paths.root), "projects": paths.list_projects()}

    @app.get("/api/settings")
    def get_settings() -> dict:
        return StudioSettings.load().public()

    @app.put("/api/settings")
    def put_settings(body: dict = Body(...)) -> dict:
        s = StudioSettings.load()
        for k, v in body.items():
            if k in s.__dataclass_fields__ and not k.startswith("_"):
                setattr(s, k, v)
        if s.auth_mode not in ("subscription", "api_key"):
            raise HTTPException(400, "auth_mode must be subscription | api_key")
        s.save()
        return s.public()

    @app.put("/api/settings/api-key")
    def put_key(body: dict = Body(...)) -> dict:
        s = StudioSettings.load()
        s.set_api_key(str(body.get("key", "")).strip())
        return s.public()

    @app.get("/api/auth")
    def auth() -> dict:
        return auth_status(StudioSettings.load())

    # ─────────────── projects ───────────────
    @app.get("/api/project-types")
    def project_types() -> list[dict]:
        from ..core import project_types as ptypes
        return [{"id": t["id"], "title": t.get("title"), "title_ar": t.get("title_ar"),
                 "summary": " ".join(str(t.get("summary", "")).split()), "roles": t.get("roles"),
                 "inputs": t.get("inputs") or [], "deliverables": t.get("deliverables") or [],
                 "stages": [{"id": s["id"], "title": s.get("title")} for s in t.get("stages") or []],
                 "params": t.get("params") or {}} for t in ptypes.load_types(paths).values()]

    def _workflow(p: Project) -> list[dict]:
        from ..core import project_types as ptypes
        try:
            t = ptypes.get_type(paths, p.type_id) if p.type_id else None
        except BimHubError:
            return []
        return ptypes.workflow_view(p, t, ExtraState(p.state_dir).workflow())

    @app.get("/api/projects")
    def projects() -> list[dict]:
        out = []
        for c in paths.list_projects():
            p = Project.load(paths, c)
            st = StateStore(p.state_dir)
            idx = p.state_dir / srcmod.INDEX_NAME
            wf = _workflow(p)
            out.append({"code": p.code, "name": p.name, "stage": p.data.get("stage"), "client": p.data.get("client"),
                        "type": p.type_id,
                        "progress": [sum(s["done"] for s in wf), sum(s["total"] for s in wf)] if wf else None,
                        "team": p.team, "agents": len(p.all_agents),
                        "open_issues": len(st.issue_list(status="open")),
                        "files": json.loads(idx.read_text(encoding="utf-8")).get("count") if idx.is_file() else None,
                        "sources": len(srcmod.sources(p))})
        return out

    @app.post("/api/projects")
    def create_project(body: dict = Body(...)) -> dict:
        import argparse
        from ..cli.main import cmd_new_project
        try:
            cmd_new_project(paths, argparse.Namespace(code=body["code"], name=body.get("name") or body["code"],
                                                      team=",".join(body.get("team") or []),
                                                      type=body.get("type") or None))
        except (BimHubError, KeyError) as e:
            raise HTTPException(400, str(e)) from e
        return {"ok": True, "code": body["code"].upper()}

    @app.get("/api/projects/{code}")
    def project_detail(code: str) -> dict:
        p = project(code)
        return {"code": p.code, "name": p.name, "data": p.data, "team": p.team, "roles": p.roles,
                "type": p.type_id, "workflow": _workflow(p),
                "agents": [agent_info(p, a) for a in p.all_agents],
                "sources": [{"name": s.name, "type": s.type, "path": str(s.path) if s.path else None, "url": s.url,
                             "readable": s.readable} for s in srcmod.sources(p)]}

    @app.get("/api/projects/{code}/state")
    def project_state(code: str) -> dict:
        p = project(code)
        st, ex = StateStore(p.state_dir), ExtraState(p.state_dir)
        pending = []
        for f in sorted(p.inbox_dir.glob("*.md")) if p.inbox_dir.is_dir() else []:
            meta, _ = parse_md(f)
            pending.append(meta)
        return {"issues": st.issue_list(), "decisions": st.decisions.read()[-30:],
                "messages": _jsonl_tail(st.messages.path, 200), "models": st.model_status_get(),
                "zones": {k: {kk: vv for kk, vv in v.items() if kk != "history"} for k, v in ex.zones().items()},
                "health": ex.health_latest(), "dashboards": ex.dashboards(), "lessons": pending,
                "workflow": _workflow(p),
                "activity": _jsonl_tail(p.state_dir / "activity.jsonl", 200),
                "chat": _jsonl_tail(p.state_dir / "studio-chat.jsonl", 300),
                "running": [r for r in running.values() if r["project"] == p.code]}

    @app.get("/api/projects/{code}/files")
    def files(code: str, query: str | None = None, kind: str | None = None, discipline: str | None = None,
              source: str | None = None, limit: int = 500) -> dict:
        try:
            return srcmod.find(project(code), query, kind, discipline, source, limit)
        except BimHubError as e:
            return {"matched": 0, "files": [], "error": str(e)}

    @app.post("/api/projects/{code}/scan")
    async def scan(code: str) -> dict:
        p = project(code)
        r = await asyncio.to_thread(srcmod.scan, p)
        bus.publish(p.code, {"kind": "scan", "agent": "studio", **r})
        return r

    @app.post("/api/projects/{code}/sources")
    def add_source(code: str, body: dict = Body(...)) -> dict:
        import argparse
        from ..cli.main import cmd_source
        try:
            cmd_source(paths, argparse.Namespace(action="add", project=code, name=body.get("name"),
                                                 type=body.get("type", "local"), path=body.get("path"), url=body.get("url")))
        except BimHubError as e:
            raise HTTPException(400, str(e)) from e
        return project_detail(code)

    @app.post("/api/projects/{code}/lessons/{lesson_id}/approve")
    def approve(code: str, lesson_id: str) -> dict:
        p = project(code)
        src = p.inbox_dir / f"{lesson_id}.md"
        if not src.is_file():
            raise HTTPException(404, "lesson not found")
        text = src.read_text(encoding="utf-8").replace("status: pending", f"status: approved\napproved_by: user (Studio)\napproved_at: {now()}", 1)
        src.write_text(text, encoding="utf-8")
        paths.lessons.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, paths.lessons / src.name)
        bus.publish(p.code, {"kind": "lesson", "agent": "user", "id": lesson_id, "status": "approved"})
        return {"approved": lesson_id, "note": "run Sync to push it to every project"}

    @app.get("/api/projects/{code}/dashboards/{kind}", response_class=HTMLResponse)
    def dashboard(code: str, kind: str):
        p = project(code)
        f = p.dir / "06-reports" / "dashboards" / f"{kind}.html"
        if not f.is_file():
            raise HTTPException(404, "no such dashboard yet")
        return FileResponse(f)

    # ─────────────── chat with any agent ───────────────
    @app.post("/api/projects/{code}/chat")
    async def chat(code: str, body: dict = Body(...)) -> dict:
        p = project(code)
        agent = p.normalize(body.get("agent") or "bim-manager")
        if agent not in p.all_agents:
            raise HTTPException(400, f"unknown agent {agent}")
        text = (body.get("text") or "").strip()
        if not text:
            raise HTTPException(400, "empty message")
        run_id = uuid.uuid4().hex[:10]
        settings = StudioSettings.load()
        prompt = build_prompt(p, agent, text, body.get("context"), settings.language)
        chat_log = p.state_dir / "studio-chat.jsonl"

        def log(rec: dict) -> None:
            with open(chat_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": now(), "run": run_id, **rec}, ensure_ascii=False) + "\n")

        log({"from": "user", "to": agent, "text": text})
        bus.publish(p.code, {"kind": "user", "agent": agent, "run": run_id, "text": text})
        running[run_id] = {"run": run_id, "project": p.code, "agent": agent, "started": time.time()}

        async def go() -> None:
            sessions = Sessions(p.state_dir)
            sid, is_new = sessions.get(agent)
            engine = ClaudeCodeEngine(settings)
            ok = False
            try:
                async for ev in engine.run(p.dir, agent, prompt, sid, is_new):
                    d = ev.as_dict()
                    d["run"] = run_id
                    bus.publish(p.code, d)
                    if ev.kind == "done":
                        ok = not ev.data.get("is_error")
                        log({"from": agent, "to": "user", "text": ev.data.get("result") or "",
                             "cost_usd": ev.data.get("cost_usd"), "turns": ev.data.get("turns")})
                    elif ev.kind == "error":
                        log({"from": agent, "to": "user", "error": ev.data.get("error")})
            finally:
                if is_new and not ok:
                    sessions.reset(agent)
                running.pop(run_id, None)
                bus.publish(p.code, {"kind": "end", "agent": agent, "run": run_id, "ok": ok})

        asyncio.create_task(go())
        return {"run": run_id, "agent": agent, "mode": settings.auth_mode}

    @app.post("/api/projects/{code}/agents/{agent}/reset")
    def reset_session(code: str, agent: str) -> dict:
        Sessions(project(code).state_dir).reset(agent)
        return {"ok": True}

    # ─────────────── live events (SSE) ───────────────
    async def watch_activity(code: str, path: Path) -> None:
        pos = path.stat().st_size if path.exists() else 0
        while bus.subs.get(code):
            await asyncio.sleep(0.8)
            if not path.exists():
                continue
            size = path.stat().st_size
            if size < pos:
                pos = 0
            if size > pos:
                with open(path, encoding="utf-8", errors="replace") as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
                for ln in chunk.splitlines():
                    try:
                        rec = json.loads(ln)
                    except json.JSONDecodeError:
                        continue
                    bus.publish(code, {"kind": "activity", **rec})
        bus.watchers.pop(code, None)

    @app.get("/api/projects/{code}/events")
    async def events(code: str):
        p = project(code)
        q = bus.subscribe(p.code)
        if p.code not in bus.watchers:
            bus.watchers[p.code] = asyncio.create_task(watch_activity(p.code, p.state_dir / "activity.jsonl"))

        async def stream():
            try:
                yield "retry: 2000\n\n"
                while True:
                    try:
                        ev = await asyncio.wait_for(q.get(), timeout=15)
                        yield f"data: {json.dumps(ev, ensure_ascii=False, default=str)}\n\n"
                    except asyncio.TimeoutError:
                        yield ": keep-alive\n\n"
            finally:
                bus.unsubscribe(p.code, q)

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # ─────────────── UI ───────────────
    ui = Path(__file__).parent / "ui"
    if (ui / "index.html").is_file():
        app.mount("/", StaticFiles(directory=str(ui), html=True), name="ui")
    else:
        @app.get("/", response_class=HTMLResponse)
        def no_ui() -> str:
            return "<h1>BIM Hub Studio API</h1><p>UI not built yet. API docs: <a href='/docs'>/docs</a></p>"

    app.state.bus = bus
    return app


def run(port: int = 8800, open_browser: bool = True) -> None:
    import threading
    import webbrowser

    import uvicorn
    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")
