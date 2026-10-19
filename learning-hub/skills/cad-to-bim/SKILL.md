---
name: cad-to-bim
description: Convert 2D CAD/PDF drawing sets into coordinated Revit models — CAD audit and register, RFIs for conflicts, model setup on shared coordinates, zone-by-zone modelling to LOD 300, clash, health. Use on projects of type cad-to-bim.
---
# CAD → coordinated Revit model

Workflow and gates for this project: `WORKFLOW.md` (generated from project type `cad-to-bim`). Track every stage with `stage_update`.

## 1. CAD intake & audit (leader + info, per discipline)
1. `files_find(kind="dwg")`, `files_find(kind="pdf")` — list the set from the project sources.
2. For each drawing record: file, title, number, revision, scale, units (`file_read` gives DWG version; open in AutoCAD/Civil 3D only when needed), date.
3. Cross-check: every plan level has sections; grids/levels agree between ARC and STR; schedules exist for doors, windows, equipment.
4. Raise one issue per conflict or missing drawing: `issue_create(title="RFI: …", owner=<discipline leader>, source="<drawing refs>")`.
5. Save the register in `04-qa/cad-audit/<DISC>-cad-register.xlsx` → `stage_update(stage="S1", status="review")`.

## 2. Setup (coordinator)
- Levels and grids from the ARC/STR CAD; one shared-coordinate system; survey point from site data if given.
- One RVT per discipline (or volume); CAD **linked**, current view only, on workset `Z-Link-CAD`, units checked.
- Copy/Monitor levels & grids into every discipline model. Define zones with `zone_set(status="open")`.

## 3. Modelling (modeler, per zone)
- Use real categories and system families; in-place and generic models only with a reason in Comments.
- Heights come from sections/elevations — not guessed from plans. Missing → model likely option, `Comments = RFI-<id>`.
- Fill `Current LOD` (300) as you go; check against `knowledge/00-standards/lod-spec-2021.md`.
- After each zone: `audit_model`, `list_warnings` → fix → hand over to clash.

## 4–5. Clash, information, health
- Clash per zone with the `clash-workflow` skill; tolerance = `params.clash_tolerance_mm`.
- Information editor fills parameters from CAD schedules/legends; `health_submit` per model.

## 6–7. Sheets (optional) and issue
- Drafter only after `drafting_clearance(zone)` ok.
- Conversion report (manager): scope converted, assumptions, open RFIs, clash status, health. Publish.

## Common traps
Mixed units in CAD (cm vs mm) · xrefs missing · plans at different origins · exploded blocks lose data ·
door/window schedules disagree with plans → always RFI, never silently choose.
