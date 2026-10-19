"""Project sources: the folders a project's agents may read (local disk, ACC via Desktop Connector, …).

project.yaml:
  sources:
    - name: ACC
      type: acc-dc            # local | acc-dc (Autodesk Desktop Connector sync folder) | acc-web (browse via Chrome)
      path: "C:/Users/me/DC/ACCDocs/WYA/AOH Hospital/Project Files"
      include: ["*.rvt", "*.ifc", "*.nw?", "*.docx", "*.xlsx", "*.pdf", "*.txt", "*.dwg"]   # optional
      exclude: ["*/Backup/*", "*.0001.rvt"]                                                  # optional
    - name: ACC-web
      type: acc-web
      url: "https://acc.autodesk.com/docs/files/projects/<id>"
The project folder itself is always an implicit source named 'project'.
Reads are allowed ONLY inside declared sources.
"""
from __future__ import annotations

import fnmatch
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..core.errors import BimHubError
from ..core.project import Project
from ..knowledge.naming import validate_name
from .readers import kind_of

DEFAULT_EXCLUDE = ["*/.git/*", "*/.claude/*", "*/__pycache__/*", "*/Backup/*", "*/backup/*", "*/~$*", "*.tmp",
                   "*.dwl", "*.dwl2", "*.slog", "*/Revit_temp/*", "*/*_backup/*",
                   "*.0001.rvt", "*.0002.rvt", "*.0003.rvt", "*.000?.rfa", ".gitkeep", "*.lock", "*.tmp.*"]
INDEX_NAME = "file-index.json"


@dataclass
class Source:
    name: str
    type: str
    path: Path | None
    url: str | None = None
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    @property
    def readable(self) -> bool:
        return self.path is not None and self.path.is_dir()


def sources(project: Project) -> list[Source]:
    out = [Source("project", "local", project.dir, exclude=["*/05-state/*", "*/07-lessons-inbox/*"])]
    for s in project.data.get("sources") or []:
        typ = s.get("type", "local")
        if typ not in ("local", "acc-dc", "acc-web"):
            raise BimHubError(f"source '{s.get('name')}': type must be local | acc-dc | acc-web")
        path = Path(os.path.expandvars(os.path.expanduser(s["path"]))) if s.get("path") else None
        out.append(Source(s.get("name") or (path.name if path else "web"), typ, path, s.get("url"),
                          list(s.get("include") or []), list(s.get("exclude") or [])))
    return out


def get_source(project: Project, name: str) -> Source:
    for s in sources(project):
        if s.name.lower() == name.lower():
            return s
    raise BimHubError(f"No source '{name}'. Sources: {[s.name for s in sources(project)]}")


def resolve(project: Project, source: str, rel: str) -> Path:
    s = get_source(project, source)
    if not s.readable:
        raise BimHubError(f"Source '{s.name}' ({s.type}) has no readable local path"
                          + (" — use the Chrome skill acc-browse to download into 00-inputs/received" if s.type == "acc-web" else ""))
    p = (s.path / rel).resolve()
    root = s.path.resolve()
    if root != p and root not in p.parents:
        raise BimHubError("Path escapes the source folder")
    if not p.is_file():
        raise BimHubError(f"Not found: {source}:{rel}" + (" (ACC: is the file synced? Desktop Connector shows cloud-only "
                                                          "files that are not downloaded yet)" if s.type == "acc-dc" else ""))
    return p


def _wanted(rel: str, s: Source) -> bool:
    r = "/" + rel.replace("\\", "/")
    if any(fnmatch.fnmatch(r, pat if pat.startswith("*") else "*/" + pat) or fnmatch.fnmatch(r.rsplit("/", 1)[-1], pat)
           for pat in DEFAULT_EXCLUDE + s.exclude):
        return False
    if s.include:
        name = r.rsplit("/", 1)[-1]
        return any(fnmatch.fnmatch(name.lower(), pat.lower()) for pat in s.include)
    return True


def scan(project: Project, only: str | None = None, max_files: int = 50000) -> dict:
    """Walk every readable source and write 05-state/file-index.json (metadata only, no content)."""
    files, summary, problems = [], {}, []
    for s in sources(project):
        if only and s.name.lower() != only.lower():
            continue
        if not s.readable:
            problems.append({"source": s.name, "type": s.type,
                             "problem": "no local path (acc-web: browse with Chrome)" if s.type == "acc-web" else f"path not found: {s.path}"})
            continue
        count = 0
        for dirpath, dirnames, filenames in os.walk(s.path):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                full = Path(dirpath) / fn
                rel = str(full.relative_to(s.path)).replace("\\", "/")
                if not _wanted(rel, s):
                    continue
                try:
                    st = full.stat()
                except OSError:
                    continue
                k = kind_of(full)
                naming = validate_name(full.name, project.naming, project.code) if k != "other" else None
                role = (naming or {}).get("fields", {}).get("role") if naming and naming.get("valid") else None
                files.append({"source": s.name, "path": rel, "kind": k, "size_kb": st.st_size // 1024,
                              "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                              "iso_name_ok": bool(naming and naming["valid"]),
                              "discipline": project.discipline_for_role(role) if role else None})
                summary[k] = summary.get(k, 0) + 1
                count += 1
                if len(files) >= max_files:
                    break
        problems.append({"source": s.name, "type": s.type, "files": count}) if count == 0 else None
    index = {"project": project.code, "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"), "count": len(files),
             "by_kind": dict(sorted(summary.items(), key=lambda kv: -kv[1])), "files": files}
    (project.state_dir / INDEX_NAME).write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"count": len(files), "by_kind": index["by_kind"], "notes": [p for p in problems if p],
            "index": f"05-state/{INDEX_NAME}"}


def load_index(project: Project) -> dict:
    f = project.state_dir / INDEX_NAME
    if not f.is_file():
        raise BimHubError("No file index yet — run files_scan first")
    return json.loads(f.read_text(encoding="utf-8"))


def find(project: Project, query: str | None = None, kind: str | None = None, discipline: str | None = None,
         source: str | None = None, limit: int = 100) -> dict:
    idx = load_index(project)
    terms = [t.lower() for t in (query or "").split() if t]
    out = []
    for f in idx["files"]:
        if kind and f["kind"] != kind:
            continue
        if discipline and (f.get("discipline") or "") != discipline:
            continue
        if source and f["source"].lower() != source.lower():
            continue
        hay = (f["source"] + "/" + f["path"]).lower()
        if terms and not all(t in hay for t in terms):
            continue
        out.append(f)
    return {"matched": len(out), "returned": min(limit, len(out)), "files": out[:limit], "scanned_at": idx["scanned_at"]}
