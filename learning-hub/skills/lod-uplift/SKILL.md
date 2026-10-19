---
name: lod-uplift
description: Develop coordinated LOD 300 models to LOD 400 for fabrication — baseline audit, LOD 400 element matrix, manufacturer families, connections/supports/rebar, fabrication splits, tight-tolerance coordination, assembly data, shop/spool drawings and approval. Use on projects of type lod-uplift.
---
# LOD 300 → LOD 400

Background: `knowledge/00-standards/lod-400-fabrication.md`, `lod-spec-2021.md`. Stages U1–U7, tracked with `stage_update`.

## U1 Baseline (leader)
Only coordinated LOD 300 is uplifted. Check: `health_latest`, zone status (`zone_list`), open clashes, `Current LOD`.
Anything below 300 → issue back to the original author; do not detail it.

## U2 LOD 400 matrix (manager + leaders)
`01-bep/lod400/matrix.xlsx`, per element class:
| Class | Product / submittal ref | Connections | Supports / hangers | Splits (max length) | Fabrication data | Tolerance |
Typical content: steel — profiles, plates, bolts, welds, cleats, camber; rebar — bar marks, shapes (BS 8666 / ACI 315),
cover, laps, couplers; duct/pipe — fittings, joints, flanges, hangers & rod lengths, insulation, spool breaks;
containment — fittings, supports, bonding; sprinklers — heads, pipe sizes from hydraulic calc.

## U3 Detailing (modeler)
- Replace generic families with the approved manufacturer families; record the submittal ref in a parameter.
- Model connections, supports/hangers, fittings and rebar; split runs at fabrication lengths.
- Fill `Current LOD = 400` only when the element meets its matrix row.

## U4 Coordination (clash)
Hard clash at `params.clash_tolerance_mm`; clearance tests at `params.clearance_mm` (insulation, access, maintenance);
installation sequence & access (can it be lifted in?). Zone → coordinated by the coordinator.

## U5 Fabrication information (info)
Assembly marks / spool numbers (unique, match drawing tags), material grade, weight, product data, quantities export.

## U6 Shop / spool drawings (drafter)
`drafting_clearance(zone)` first. STR shop drawings follow the sd-agent rules (`get_drawing_rules`).
Each sheet: assembly views, BOM, marks, dimensions for fabrication, revision & status code.

## U7 Approval
Submit with status codes; every consultant comment = an issue; resubmit until A/B, then publish.
