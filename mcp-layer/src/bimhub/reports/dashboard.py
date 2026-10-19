"""Static HTML dashboards (self-contained: inline CSS + SVG, no network) written to 06-reports/dashboards/.

Input spec (what the coordinator agent sends):
{
  "title": "Clash dashboard — L03",
  "subtitle": "Navisworks · AOH-WYA-ZZ-03-CM-Z-0003.nwd",
  "kpis":   [{"label": "Open groups", "value": 9, "tone": "bad"}, {"label": "Resolved", "value": 31, "tone": "good"}],
  "bars":   [{"title": "Open groups by discipline", "items": [{"label": "MECH", "value": 4}, ...]}],
  "tables": [{"title": "Clash tests", "columns": ["Test", "New", "Active", "Resolved"], "rows": [["STR×MECH", 2, 3, 20]]}],
  "notes":  ["Gravity drainage is prioritised on L03 (DEC-0007)."]
}
"""
from __future__ import annotations

import html
from typing import Any

TONE = {"good": "#1F9D6B", "bad": "#C2413A", "warn": "#B7791F", None: "#2B3A4A", "": "#2B3A4A"}


def _e(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def _bars(b: dict) -> str:
    items = b.get("items") or []
    mx = max([float(i.get("value") or 0) for i in items] + [1])
    rows = []
    for i in items[:30]:
        v = float(i.get("value") or 0)
        w = 0 if mx == 0 else 100 * v / mx
        rows.append(f'<div class="br"><span class="bl">{_e(i.get("label"))}</span>'
                    f'<span class="bt"><span class="bf" style="width:{w:.1f}%"></span></span>'
                    f'<span class="bv">{_e(i.get("value"))}</span></div>')
    return f'<section class="card"><h2>{_e(b.get("title"))}</h2>{"".join(rows) or "<p class=m>No data</p>"}</section>'


def _table(t: dict) -> str:
    cols = t.get("columns") or []
    head = "".join(f"<th>{_e(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f"<td>{_e(c)}</td>" for c in r) + "</tr>" for r in (t.get("rows") or [])[:500])
    return (f'<section class="card wide"><h2>{_e(t.get("title"))}</h2><div class="tw"><table><thead><tr>{head}</tr>'
            f'</thead><tbody>{body}</tbody></table></div></section>')


def render(spec: dict, project: str, generated_at: str, by: str) -> str:
    kpis = "".join(
        f'<div class="kpi"><div class="kv" style="color:{TONE.get(k.get("tone"), TONE[None])}">{_e(k.get("value"))}</div>'
        f'<div class="kl">{_e(k.get("label"))}</div></div>' for k in spec.get("kpis") or [])
    blocks = "".join(_bars(b) for b in spec.get("bars") or []) + "".join(_table(t) for t in spec.get("tables") or [])
    notes = "".join(f"<li>{_e(n)}</li>" for n in spec.get("notes") or [])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(spec.get("title"))} — {_e(project)}</title><style>
:root{{--bg:#F6F7F9;--card:#fff;--ink:#16202B;--mute:#5B6878;--line:#E1E5EA;--bar:#3B6EA8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0E1116;--card:#151A21;--ink:#E6EAF0;--mute:#93A0B0;--line:#232A33;--bar:#60A5FA}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 "Segoe UI",system-ui,sans-serif}}
header{{padding:20px 24px;border-bottom:1px solid var(--line)}}h1{{margin:0;font-size:22px}}.sub{{color:var(--mute)}}
main{{padding:20px 24px;display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
.kpis{{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:12px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:140px}}
.kv{{font-size:28px;font-weight:700}}.kl{{color:var(--mute);font-size:12px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}.wide{{grid-column:1/-1}}
h2{{margin:0 0 10px;font-size:14px}}.br{{display:grid;grid-template-columns:110px 1fr 48px;gap:8px;align-items:center;margin:6px 0}}
.bl{{color:var(--mute);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}.bt{{background:var(--line);border-radius:4px;height:10px}}
.bf{{display:block;height:10px;border-radius:4px;background:var(--bar)}}.bv{{text-align:right;font-variant-numeric:tabular-nums}}
.tw{{overflow-x:auto}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);font-size:13px}}
th{{color:var(--mute);font-weight:600}}.m{{color:var(--mute)}}footer{{padding:0 24px 24px;color:var(--mute);font-size:12px}}
</style></head><body><header><h1>{_e(spec.get("title"))}</h1><div class="sub">{_e(project)} · {_e(spec.get("subtitle"))}</div></header>
<main><div class="kpis">{kpis}</div>{blocks}{f'<section class="card wide"><h2>Notes</h2><ul>{notes}</ul></section>' if notes else ''}</main>
<footer>Generated {_e(generated_at)} by {_e(by)} · BIM Hub</footer></body></html>"""
