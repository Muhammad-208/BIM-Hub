---
title: LOD 400 — fabrication-level development (BIMForum LOD Spec)
tags: [lod, lod400, fabrication, shop-drawings, spool, rebar, steel]
source: BIMForum LOD Specification (2021) definitions; trade practice notes
---
# LOD 400

**BIMForum definition (paraphrased):** the element is modelled as a specific system, object or assembly in terms of
size, shape, location, quantity and orientation **with detailing, fabrication, assembly and installation information**.
LOD 400 elements are modelled at sufficient detail and accuracy for fabrication of the represented component.

LOD 350 (between 300 and 400) adds the **interfaces** with other building systems (supports, connections) — many
fabrication projects pass through 350 on the way to 400.

## What changes from 300 → 400 (by trade)
| Trade | LOD 300 | LOD 400 adds |
|---|---|---|
| Structural steel | members with real profiles at correct location | connections (plates, bolts, welds), cleats, camber, piece marks, erection marks |
| Concrete / rebar | element geometry, openings | rebar (bar marks, shapes, cover, laps, couplers), embeds, pour breaks |
| Ductwork | sized ducts and main fittings | all fittings, joints/flanges, hangers with rod length, insulation, spool / section breaks |
| Pipework | sized pipes, main valves | all fittings & valves (actual product), joint types, supports, spool numbers, slopes |
| Cable containment | trays/trunking sized | fittings, supports, bonding, segment lengths |
| Sprinklers | mains & branch routing | heads (product), pipe sizes from hydraulic calc, hangers, seismic bracing if required |

## Information typically required at 400
Product / submittal reference · manufacturer & model · material grade · assembly mark / spool no. · weight ·
fabrication length · connection type · installation sequence / zone · status (for fabrication / approved).

## Coordination at 400
Tighter clash tolerance (≈ 0–10 mm vs 25–50 mm at 300), clearance tests for insulation, access and maintenance,
installation sequence and lifting/access checks.
