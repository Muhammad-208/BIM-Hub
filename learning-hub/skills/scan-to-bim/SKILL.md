---
name: scan-to-bim
description: Produce as-built Revit models from laser-scan point clouds (E57, RCP/RCS, LAS) — registration check, LOA/scope matrix, modelling to the cloud with verification tags, deviation analysis against USIBD LOA tolerances, as-built data and handover. Use on projects of type scan-to-bim.
---
# Scan to BIM (as-built)

Background: `knowledge/00-standards/usibd-loa.md`. Stages P1–P7, tracked with `stage_update`.

## P1 Intake (coordinator + info)
- `files_find(kind="point-cloud")`; `file_read` each E57/LAS for point counts, scans, bounds, coordinate info.
- From the scan report: registration RMS / cloud-to-cloud error, control points, scanner, date.
- Registration error must fit `params.loa_measured`; if not → issue to the surveyor.
- Occlusions / missing areas → survey RFI issues with location.

## P2 Setup & scope (coordinator + leaders)
- E57/LAS → index in ReCap to RCP/RCS; link RCP in Revit (Auto – Origin to Origin or by shared coordinates).
- Levels from slab top surfaces (sections through the cloud), grids from structure.
- Scope matrix `01-bep/scan-scope.xlsx`: element class × zone × LOA represented × LOD × modelled yes/no.

## P3 Modelling (modeler)
- Model to the cloud: real thicknesses, out-of-plumb walls and slab falls within the LOA represented.
- Every element gets `Verification` = Scanned | Assumed | From drawings. Hidden services above ceilings = Assumed (or out of scope).
- Don't over-model: follow the scope matrix.

## P4 Deviation analysis (qa-model + info)
Compare model surfaces to the cloud (Revit + point-cloud tools, Navisworks, or CloudCompare cloud-to-mesh).
Report per element class: checked count, mean / max deviation, % within the LOA represented upper range.
Target: ≥ 95 % within tolerance (LOA is stated at 2σ). Outliers → fix or justify. Save in `04-qa/deviation/`.

## P5–P7
Info: asset data from photos/nameplates (never guessed). Drafter: as-built drawings with LOA note + verification legend.
Manager: handover with the accuracy & limitations statement.
