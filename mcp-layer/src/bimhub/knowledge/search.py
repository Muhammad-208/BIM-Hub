"""Lightweight search over the Learning Hub markdown (knowledge, skills, lessons, index).
Front-matter aware; ranks title > tags > body; prefers status: current. Swap for a vector index later
behind the same `search()` signature."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

WORD = re.compile(r"[\w؀-ۿ]+", re.UNICODE)
STOP = set("""a an and are as at be by can do does for from has have how i in is it its my of on or should
the this to was what when where which who why will with you your we our me
في من على عن الى إلى ما ماذا ازاي إزاي ايه إيه هو هي اللي الي ده دي مين امتى فين هل""".split())


def parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            return (meta if isinstance(meta, dict) else {}), parts[2]
    return {}, text


def tokens(s: str) -> list[str]:
    return [t.lower() for t in WORD.findall(s)]


@dataclass
class Hit:
    path: str
    title: str
    score: float
    snippet: str
    status: str


def search(hub_dir: Path, query: str, limit: int = 8, scope: str | None = None) -> list[Hit]:
    q = [t for t in tokens(query) if len(t) > 1 and t not in STOP]
    if not q:
        return []
    roots = [hub_dir / scope] if scope else [hub_dir]
    hits: list[Hit] = []
    for root in roots:
        for p in root.rglob("*.md"):
            if "_raw" in p.parts:
                continue
            meta, body = parse_md(p)
            title = str(meta.get("title") or meta.get("name") or p.stem)
            tags = " ".join(map(str, meta.get("tags") or []))
            desc = str(meta.get("description") or "")
            tt, tg, bd = tokens(title + " " + p.stem), tokens(tags + " " + desc), tokens(body)
            bd_set = {}
            for t in bd:
                bd_set[t] = bd_set.get(t, 0) + 1
            score = 0.0
            for t in q:
                score += 5 * tt.count(t) + 3 * tg.count(t) + (1 + math.log(bd_set[t]) if t in bd_set else 0)
            if score <= 0:
                continue
            status = str(meta.get("status", "current"))
            if status == "superseded":
                score *= 0.4
            hits.append(Hit(str(p.relative_to(hub_dir)).replace("\\", "/"), title, round(score, 2),
                            _snippet(body, q), status))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def _snippet(body: str, q: list[str], width: int = 240) -> str:
    low = body.lower()
    pos = min((low.find(t) for t in q if low.find(t) >= 0), default=0)
    start = max(0, pos - 60)
    return re.sub(r"\s+", " ", body[start:start + width]).strip()
