# Learning Hub (L0) — shared by every project and every agent

One brain, many projects. Anything learned on project A is available on project B after approval.

```
learning-hub/
├── INDEX.md                 ← start here (agents read this first)
├── glossary.md              ← shared terminology
├── library/catalog.yaml     ← registry of source files (PDF/DOCX/XLSX/MP4) in your libraries, tagged & versioned
├── knowledge/
│   ├── 00-standards/        ← ISO 19650, PAS 1192, LOD/LOIN, COBie, classification, naming (distilled .md)
│   ├── 01-templates/        ← BEP, EIR, MIDP/TIDP, RACI, checklists
│   ├── 02-disciplines/<d>/  ← arc str mech plumb ff elec ict infra land
│   └── 03-processes/        ← CDE workflow, clash workflow, QA workflow
├── skills/<name>/SKILL.md   ← reusable procedures; copied into every project's .claude/skills by `bimhub sync`
└── lessons/                 ← approved lessons learned (one .md per lesson)
```

## How learning flows (governance)

```
agent finds something reusable
      │  lesson_propose            (writes projects/<CODE>/07-lessons-inbox/<id>.md)
      ▼
bim-manager reviews  ── lesson_reject (reason) ──► stays in project, marked rejected
      │  lesson_approve(target)
      ▼
learning-hub/lessons/<id>.md  (+ optional promotion into knowledge/ or a skill by you)
      │  bimhub sync
      ▼
every project's agents now see it
```

Rules for an approved lesson: reusable beyond one project · has a source (standard clause, test result, or the issue that proved it) · contains **no client-confidential data** (names, prices, drawings).

## Knowledge files format
Markdown with front-matter:
```yaml
---
title: ISO 19650-2 information delivery cycle
source: "BS EN ISO 19650-2:2018 §5.1–5.8"     # or library/catalog id
version: 2018
status: current        # current | superseded
tags: [iso19650, delivery, appointment]
---
```
`hub_search` ranks by title/tags/body, and prefers `status: current`.

## Filling it
1. `bimhub catalog` → rebuilds `library/catalog.yaml` from your source folders (paths in `mcp-layer/config/hub.yaml`).
2. `bimhub ingest <catalog-id>` → extracts text of a PDF/DOCX into `knowledge/_raw/` for an agent (or you) to distil into a clean knowledge file.
3. Distilled files go in `knowledge/…` — short, sourced, versioned. Raw extracts are never cited directly.
