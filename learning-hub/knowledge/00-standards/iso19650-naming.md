---
title: Information container naming (unique ID) — ISO 19650-2 UK National Annex NA.2 / BS 1192 field codes
source: "Guidance Part 1 §7.2 pp27–29 (catalog 76129f61); BS 1192:2007+A2:2016 §5.4, §6–§13 and Table 2 (catalog 9ebc361a) — the NA 'is based on the same convention set out in superseded BS 1192:2007' (Pt1 p27); Guidance Part 2 §2.7 (catalog 8ade0515)"
version: "ISO 19650-2:2018 UK NA (field codes from BS 1192:2007+A2:2016)"
status: current
tags: [iso19650, naming, unique-id, national-annex, originator, volume, level, type, role, discipline, number, bs1192, file-naming]
---

> **الخلاصة:** الاسم = `Project-Originator-Volume/System-Level/Location-Type-Role-Number`. الـ status والـ revision والـ classification بيتحطوا **metadata** في الـ CDE، مش جوه الاسم.

## 1. Structure
`Project - Originator - Volume/System - Level/Location - Type - Role - Number`

Example from Guidance Pt1 p27: **`NEWP-ABC-XX-ZZ-SP-S-0001`**
- project NEWP
- originator ABC
- XX = no volume
- ZZ = all levels
- SP = specification
- S = structural engineer
- 0001 = first container of that combination

The fact that it is a *steel frame* specification is carried by **classification metadata**, not by the name. Shown in a CDE: `NEWP-ABC-XX-ZZ-SP-S-0001 | S2 | P01 | Ss_20_10_75_35` (Pt1 Table 3, p28).

## 2. Field rules
| Field | Rule | Standard / reserved codes |
|---|---|---|
| **Project** | 2–6 characters; one identifier for the project, **different from any organization's internal job number** (BS 1192 §6; NA.3.2 per Pt1 fn 9) | none mandated |
| **Originator** | 3–6 characters, unique per organization (BS 1192 §7.3) | none mandated |
| **Volume / System** | 1–2 characters. Each container covers one volume. Volumes are non-overlapping per role and ideally match one team's scope (BS 1192 §8.1.2, §8.2.2) | `ZZ` all volumes · `XX` none |
| **Level / Location** | 2 characters (BS 1192 §8.2.3) | `ZZ` multiple levels · `XX` no level · `GF` ground · `00` base level / linear assets · `01`, `02` … floors · `M1` mezzanine above 01 · `B1`, `B2` basements. Linear and infra assets usually need project-specific location codes |
| **Type** | exactly 2 characters (BS 1192 §9.2) | see §3 |
| **Role** | 1 character (BS 1192 §10.2). In the 2021 UK NA revision this field is called **Discipline** and the code list was revised (see §5) | see §4 |
| **Number** | exactly 4 digits with leading zeros (BS 1192 §13.2), sequential within the combination of the other fields. The project may define otherwise | — |

Optional fields that appear only when the environment cannot carry metadata: Classification, Suitability, Revision (BS 1192 Table 2). In an ISO 19650 CDE, keep them **as metadata**.

## 3. Type codes (BS 1192 §9.2)
**Models and drawings:**
- AF animation
- CM combined (multi-discipline) model
- CR clash rendition
- DR 2D drawing
- M2 2D model
- M3 3D model
- MR model rendition (e.g. thermal)
- VS visualization

**Documents:**
- BQ bill of quantities
- CA calculations
- CO correspondence
- CP cost plan
- DB database
- FN file note
- HS health & safety
- IE information exchange file
- MI minutes / action notes
- MS method statement
- PP presentation
- PR programme
- RD room data sheet
- RI request for information
- RP report
- SA schedule of accommodation
- SH schedule
- SN snagging list
- SP specification
- SU survey

## 4. Role codes (BS 1192 §10.2)
| Code | Role | Code | Role |
|---|---|---|---|
| A | Architect | K | Client |
| B | Building surveyor | L | Landscape architect |
| C | Civil engineer | M | Mechanical engineer |
| D | Drainage, highways engineer | P | Public health engineer |
| E | Electrical engineer | Q | Quantity surveyor |
| F | Facilities manager | S | Structural engineer |
| G | Geographical & land surveyor | T | Town & country planner |
| H | Heating & ventilation designer | W | Contractor |
| I | Interior designer | X | Subcontractor |
| | | Y | Specialist designer |
| | | Z | General (non-disciplinary) |

Project-specific roles use **J, N, R, U, V** or longer codes, which must be listed and published (BS 1192 §10.3).

**BIM Hub default mapping** (in `project.yaml`, agree it in the BEP):

| Agent | Role code |
|---|---|
| arc | A |
| str | S |
| mech | M |
| plumb | P |
| elec | E |
| infra | C |
| land | L |
| ff | `FP` (project-defined; alternative Y) |
| ict | `IT` (project-defined; alternative Y) |

## 5. Version caveat ⚠️
- The UK NA was revised in 2021: Role was renamed **Discipline**, and codes were revised to describe technical activities rather than job titles (noted in library item 18f55046).
- The 2021 NA text is **not in the library**. If a project adopts it, put its code list in `project.yaml → naming` and in the BEP. Project rules always override this file.
- Other countries' National Annexes differ. When working for a foreign client, use that client's annex (Pt1 §7.1).

## 6. Rules that are often broken
1. **Renditions get their own ID.** An IFC exported from `…-M3-S-0001` and a PDF of `…-DR-A-0101` need distinct container IDs from their native sources (Guidance Pt2 §2.7).
2. Don't put status or revision in the file name inside a CDE. They are metadata (Pt1 p27–28).
3. Don't apply the unique-ID structure to folders or layers (Pt1 fn 8).
4. Back-office files should use the same ID. Otherwise the link between `Steel frame 8001` on a local drive and the CDE container is lost (Pt1 p28).
5. Use a hyphen only as the field separator, and never use special characters.

## Agent use
- `naming_validate` (bimhub MCP) runs the mechanical check against `project.yaml → naming`.
- qa-doc reports each failure as field / found / expected / corrected name.
- Skill `iso19650-naming` has the procedure.
