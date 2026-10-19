"""Project state in 05-state/ — append-only event logs (auditable, merge-friendly, git-friendly).

issues.jsonl     {"op": "create"|"update", "id", "at", "by", ...}
decisions.jsonl  {"id", "at", "by", "title", "decision", "reason", "source"}
messages.jsonl   {"id", "at", "from", "to", "task", "ref", "status", "priority", "body"}
model-status.yaml  current CDE state + QA verdicts per container (small, overwritten atomically)
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import yaml

from ..core.errors import BimHubError

ISSUE_STATUSES = ("open", "in-progress", "resolved", "closed", "rejected")
PRIORITIES = ("critical", "high", "medium", "low")
CDE_STATES = ("WIP", "SHARED", "PUBLISHED", "ARCHIVE")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@contextmanager
def file_lock(path: Path, timeout: float = 10) -> Iterator[None]:
    lock = path.with_suffix(path.suffix + ".lock")
    start = time.time()
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                # stale lock (crashed writer) — take over
                try:
                    lock.unlink()
                except FileNotFoundError:
                    pass
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


class JsonlLog:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def read(self) -> list[dict[str, Any]]:
        out = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def append(self, rec: dict[str, Any]) -> dict[str, Any]:
        with file_lock(self.path):
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def next_id(self, prefix: str, ops: tuple[str, ...] | None = None) -> str:
        recs = self.read()
        n = sum(1 for r in recs if ops is None or r.get("op") in ops) + 1
        return f"{prefix}-{n:04d}"


class StateStore:
    def __init__(self, state_dir: Path):
        self.dir = state_dir
        self.issues = JsonlLog(state_dir / "issues.jsonl")
        self.decisions = JsonlLog(state_dir / "decisions.jsonl")
        self.messages = JsonlLog(state_dir / "messages.jsonl")
        self.status_path = state_dir / "model-status.yaml"

    # ---------- issues ----------
    def issue_create(self, by: str, title: str, owner: str, priority: str = "medium", **fields: Any) -> dict:
        if priority not in PRIORITIES:
            raise BimHubError(f"priority must be one of {PRIORITIES}")
        with file_lock(self.issues.path.with_name("issues.id")):
            iid = self.issues.next_id("ISS", ("create",))
            rec = {"op": "create", "id": iid, "at": now(), "by": by, "title": title, "owner": owner,
                   "priority": priority, "status": "open", **{k: v for k, v in fields.items() if v is not None}}
            self.issues.append(rec)
        return self._fold()[iid]

    def issue_update(self, by: str, issue_id: str, **changes: Any) -> dict:
        changes = {k: v for k, v in changes.items() if v is not None}
        if "status" in changes and changes["status"] not in ISSUE_STATUSES:
            raise BimHubError(f"status must be one of {ISSUE_STATUSES}")
        if issue_id not in self._fold():
            raise BimHubError(f"Issue {issue_id} does not exist")
        self.issues.append({"op": "update", "id": issue_id, "at": now(), "by": by, "changes": changes})
        return self._fold()[issue_id]

    def _fold(self) -> dict[str, dict]:
        issues: dict[str, dict] = {}
        for r in self.issues.read():
            if r.get("op") == "create":
                issues[r["id"]] = {k: v for k, v in r.items() if k != "op"} | {"history": []}
            elif r.get("op") == "update" and r["id"] in issues:
                i = issues[r["id"]]
                i.update(r["changes"])
                i["updated_at"] = r["at"]
                i["history"].append({"at": r["at"], "by": r["by"], "changes": r["changes"]})
        return issues

    def issue_list(self, status: str | None = None, owner: str | None = None,
                   priority: str | None = None) -> list[dict]:
        out = []
        for i in self._fold().values():
            if status and i.get("status") != status:
                continue
            if owner and i.get("owner") != owner:
                continue
            if priority and i.get("priority") != priority:
                continue
            out.append({k: v for k, v in i.items() if k != "history"})
        return out

    def issue_get(self, issue_id: str) -> dict:
        i = self._fold().get(issue_id)
        if not i:
            raise BimHubError(f"Issue {issue_id} does not exist")
        return i

    # ---------- decisions ----------
    def decision_log(self, by: str, title: str, decision: str, reason: str, source: str | None = None) -> dict:
        with file_lock(self.decisions.path.with_name("decisions.id")):
            did = self.decisions.next_id("DEC")
            return self.decisions.append({"id": did, "at": now(), "by": by, "title": title,
                                          "decision": decision, "reason": reason, "source": source})

    # ---------- messages ----------
    def message_send(self, sender: str, to: str, task: str, ref: str | None, priority: str,
                     body: str | None) -> dict:
        with file_lock(self.messages.path.with_name("messages.id")):
            mid = self.messages.next_id("MSG")
            return self.messages.append({"id": mid, "at": now(), "from": sender, "to": to, "task": task,
                                         "ref": ref, "status": "new", "priority": priority, "body": body})

    def message_inbox(self, agent: str, include_done: bool = False) -> list[dict]:
        msgs: dict[str, dict] = {}
        for r in self.messages.read():
            if r.get("op") == "ack":
                if r["id"] in msgs:
                    msgs[r["id"]]["status"] = r["status"]
            else:
                msgs[r["id"]] = r
        return [m for m in msgs.values()
                if m.get("to") in (agent, "all") and (include_done or m.get("status") != "done")]

    def message_ack(self, agent: str, message_id: str, status: str) -> dict:
        if status not in ("read", "in-progress", "done"):
            raise BimHubError("status must be read | in-progress | done")
        return self.messages.append({"op": "ack", "id": message_id, "at": now(), "by": agent, "status": status})

    # ---------- model status ----------
    def _status(self) -> dict:
        if not self.status_path.exists():
            return {"models": {}}
        with open(self.status_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"models": {}}

    def model_status_get(self, container: str | None = None) -> dict:
        models = self._status().get("models") or {}
        if container:
            if container not in models:
                raise BimHubError(f"No status recorded for '{container}'")
            return {container: models[container]}
        return models

    def model_status_set(self, by: str, container: str, **fields: Any) -> dict:
        fields = {k: v for k, v in fields.items() if v is not None}
        if "state" in fields and fields["state"] not in CDE_STATES:
            raise BimHubError(f"state must be one of {CDE_STATES}")
        with file_lock(self.status_path):
            data = self._status()
            models = data.setdefault("models", {}) or {}
            data["models"] = models
            entry = models.setdefault(container, {"state": "WIP"})
            entry.update(fields)
            entry["updated_at"], entry["updated_by"] = now(), by
            tmp = self.status_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("# Managed by bimhub MCP (model_status_*). Do not edit by hand.\n")
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=True)
            os.replace(tmp, self.status_path)
        return {container: entry}


# ───────────────────────── zones, health, dashboards ─────────────────────────
ZONE_STATES = ("open", "in-coordination", "coordinated", "on-hold")


class ExtraState:
    """Coordination zones (drafting gate), model-health reports and dashboard registry."""

    def __init__(self, state_dir: Path):
        self.dir = state_dir
        self.zones_path = state_dir / "zones.yaml"
        self.health = JsonlLog(state_dir / "health.jsonl")
        self.dash_path = state_dir / "dashboards.json"
        self.workflow_path = state_dir / "workflow.yaml"

    # workflow (project-type stages)
    def workflow(self) -> dict:
        if not self.workflow_path.exists():
            return {}
        with open(self.workflow_path, encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("stages", {}) or {}

    def stage_set(self, by: str, key: str, status: str, note: str | None = None, evidence: str | None = None,
                  layer: int = 1) -> dict:
        with file_lock(self.workflow_path):
            w = self.workflow()
            e = w.get(key, {})
            hist = e.get("history", [])
            hist.append({"at": now(), "by": by, "status": status, "note": note, "evidence": evidence})
            e.update(status=status, by=by, at=now(), note=note, history=hist[-30:])
            if evidence:
                e["evidence"] = evidence
            if status in ("qa-pass", "qa-fail"):
                e.setdefault("qa", {})[by] = status
            elif status in ("in-progress", "review"):
                e["qa"] = {}
            w[key] = e
            tmp = self.workflow_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("# Managed by bimhub MCP (stage_update). Workflow comes from the project type.\n")
                yaml.safe_dump({"stages": w}, f, allow_unicode=True, sort_keys=True)
            os.replace(tmp, self.workflow_path)
        return {key: {k: v for k, v in e.items() if k != "history"}}

    # zones
    def zones(self) -> dict:
        if not self.zones_path.exists():
            return {}
        with open(self.zones_path, encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("zones", {}) or {}

    def zone_set(self, by: str, zone: str, status: str, note: str | None = None,
                 disciplines: list[str] | None = None) -> dict:
        if status not in ZONE_STATES:
            raise BimHubError(f"status must be one of {ZONE_STATES}")
        with file_lock(self.zones_path):
            z = self.zones()
            entry = z.get(zone, {})
            hist = entry.get("history", [])
            hist.append({"at": now(), "by": by, "status": status, "note": note})
            entry.update(status=status, by=by, at=now(), note=note, history=hist[-20:])
            if disciplines is not None:
                entry["disciplines"] = disciplines
            z[zone] = entry
            tmp = self.zones_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("# Managed by bimhub MCP (zone_set). Coordinated zones may be drafted.\n")
                yaml.safe_dump({"zones": z}, f, allow_unicode=True, sort_keys=True)
            os.replace(tmp, self.zones_path)
        return {zone: {k: v for k, v in entry.items() if k != "history"}}

    # health
    def health_submit(self, by: str, discipline: str, model: str, score: float, checks: list[dict],
                      report: str | None) -> dict:
        if not 0 <= float(score) <= 100:
            raise BimHubError("score must be 0–100")
        rec = {"at": now(), "by": by, "discipline": discipline, "model": model, "score": round(float(score), 1),
               "checks": checks or [], "report": report,
               "failed": sum(1 for c in checks or [] if str(c.get("status", "")).lower() in ("fail", "failed"))}
        return self.health.append(rec)

    def health_latest(self, discipline: str | None = None) -> list[dict]:
        latest: dict[str, dict] = {}
        for r in self.health.read():
            if discipline and r["discipline"] != discipline:
                continue
            latest[r["model"]] = r
        return list(latest.values())

    # dashboards
    def dashboards(self) -> dict:
        if not self.dash_path.exists():
            return {}
        return json.loads(self.dash_path.read_text(encoding="utf-8"))

    def dashboard_register(self, kind: str, entry: dict) -> None:
        with file_lock(self.dash_path):
            d = self.dashboards()
            d[kind] = entry
            self.dash_path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
