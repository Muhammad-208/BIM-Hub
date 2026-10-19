---
name: model-qa-checklist
description: Full model-health checklist used by qa-model at the WIP→SHARED gate (coordinates, levels/grids, worksets, warnings, families, LOD geometry, hygiene). Use for any model audit.
---
# Model QA checklist

| # | Check | Pass criterion | Severity if fail |
|---|---|---|---|
| 1 | Shared coordinates / base points | identical to federated reference | Critical |
| 2 | Levels & grids | names + elevations = master; monitored | Critical |
| 3 | Units & true north | per BEP | Major |
| 4 | Worksets | per BEP list; nothing on default except allowed | Major |
| 5 | Critical warnings | 0 duplicate instances, 0 overlapping walls, 0 room separation issues | Major |
| 6 | Total warnings | ≤ threshold in BEP (default 200 / or trend down) | Minor |
| 7 | In-place families | 0 unless approved | Major |
| 8 | CAD imports | 0 (links only) | Major |
| 9 | Family / type naming | per BEP convention | Minor |
| 10 | Geometry vs LOD of stage | no missing required elements; no over-modelling | Major |
| 11 | Links | relative paths, correct versions, overlay vs attach per BEP | Minor |
| 12 | Hygiene | purged, no unused views/sheets beyond templates, file size within limit | Minor |

Verdict: any Critical → FAIL · Majors > 0 → PASS WITH COMMENTS only if bim-manager agreed, else FAIL · Minors only → PASS WITH COMMENTS.
Data via `revit` MCP: `get_model_info`, `list_warnings`, `audit_model`, `list_elements`.
