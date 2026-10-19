---
name: model-review-report
description: Review received Revit or IFC models against LOD 300 / LOIN / EIR — register, criteria matrix, geometry + integrity + information + clash review — and compile a scored review report with issue list and A/B/C recommendation. Read-only on received models. Use on projects of type model-review.
---
# Model review → report

Received models are **read-only**: never save, sync or purge them. Track stages R1–R7 with `stage_update`.

## R1 Register (coordinator + info)
For every model (`files_find(kind="revit-model")`, `files_find(kind="ifc")`, then `file_read`):
- RVT: Revit version, worksharing/central, file name vs naming (`naming_validate`).
- IFC: schema (IFC2X3 / IFC4 / IFC4X3), MVD / description, authoring app, units, site/georeference, entity counts.
Record in `04-qa/review/model-register.xlsx`.

## R2 Criteria matrix (manager + leaders)
`04-qa/review/criteria.xlsx`, one row per category / IFC entity:
| Discipline | Category / IFC entity | LOD 300 geometry criterion | Required properties | Integrity check | Source |
Geometry criterion from BIMForum LOD Spec 2021 element tables (`knowledge/00-standards/lod-spec-2021.md`);
properties from the EIR / LOIN; source = clause reference. No EIR → BIMForum + ask the manager to confirm.

## R3 Geometry & integrity (leader per discipline)
- Sample ≥ 10 % or ≥ 20 elements per category (all if fewer). LOD 300 = specific size, shape, location,
  orientation and quantity; generic placeholders = LOD 200 → **partial**.
- Integrity: warnings count and top types (`list_warnings`), duplicates/overlaps, in-place & generic families,
  imported CAD, unplaced/redundant rooms, levels/grids consistent with other disciplines, shared coordinates.
- IFC only: elements as `IfcBuildingElementProxy` (target < 5 %), missing storeys, wrong containment.
Result per row: pass / partial / fail + element ids.

## R4 Information (info per discipline)
Completeness % = filled required properties / required (`loin-check`). Placeholders count as missing.
Classification (Uniclass / OmniClass) coverage. COBie only if the EIR asks (`cobie-validation`).

## R5 Coordination (clash per discipline)
Run the clash matrix on the received models; report counts by severity & pair. Do not fix.

## R6 Report (coordinator)
Score per discipline = weighted: geometry 40 %, information 30 %, integrity 20 %, coordination 10 %
(adjust in criteria.xlsx if the BEP says otherwise). pass = 1, partial = 0.5, fail = 0.
1. One issue per finding (`issue_create`, with element ids and criterion source).
2. `dashboard_publish(kind="model-review", spec=…)` — KPIs: overall %, per discipline %, LOI %, proxies %, clashes.
3. Report in `06-reports/review/<CODE>-REVIEW-<date>.docx` (or .html):
   1 Summary & recommendation · 2 Scope & models reviewed · 3 Criteria & method · 4 Results per discipline
   (table + worst findings with screenshots/viewpoints) · 5 Information completeness · 6 Coordination ·
   7 Issue list · Appendix: register, criteria matrix.
Recommendation: ≥ `params.pass_mark` → A (accept); within 15 points below → B (accept with comments); else C (revise & resubmit).

## R7 Sign-off (manager)
`decision_log` the recommendation, then issue the report.
