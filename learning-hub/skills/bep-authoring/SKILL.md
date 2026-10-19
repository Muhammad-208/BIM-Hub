---
name: bep-authoring
description: Produce or update a BIM Execution Plan (pre- or post-appointment) that answers the EIR, per ISO 19650-2 §5.3 and §5.4. Use when the user asks for a BEP, BEP outline, or EIR response.
---
# BEP authoring

## Inputs
EIR (+ OIR/AIR/PIR if given) in `00-inputs/eir-oir-air/`, appointment type in `project.yaml`, hub templates (PSU BIM PxP v2.1/3.0, NATSPEC BMP, CPIx post-contract BEP, UCSD BEP sample).

## Sections (post-appointment)
1. Project info & information management team (names/roles — ask the user, never invent)
2. Information delivery strategy (goals, BIM uses — PSU Goal/Use worksheet)
3. Federation strategy & volume breakdown (feeds naming Volume field)
4. Responsibility matrix (RACI per deliverable)
5. Information standard: naming, status codes, classification, units, coordinates
6. LOIN table per stage
7. Production methods & procedures: modelling guidelines, QA gate, clash workflow
8. CDE: platform, states, permissions, transmittals
9. Schedule of software & versions
10. MIDP / TIDP references
11. Capability & capacity (ISO 19650-2 §5.3.3–5.3.4), mobilization plan (§5.3.5) and risk register (§5.3.6)

Clause map and TIDP/MIDP content: hub `knowledge/00-standards/iso19650-2-delivery-process.md`.

## Rule
Trace every BEP clause to the EIR requirement it answers (table: EIR ref → BEP section). Unanswered EIR items are listed at the end as open.
