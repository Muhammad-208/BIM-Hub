# Learning Hub — Index

Read this first. Then use `hub_search` (MCP) or open the file you need.

## Standards (knowledge/00-standards)
| Topic | Primary source in library | Status |
|---|---|---|
| ISO 19650-1 concepts (parties, OIR/PIR/AIR/EIR, PIM/AIM, federation) | UK Guidance Part 1 | ✅ `knowledge/00-standards/iso19650-1-concepts.md` |
| ISO 19650-2 delivery process (5.1–5.8, TIDP/MIDP) | UK Guidance Part 2 (4th ed.) | ✅ `knowledge/00-standards/iso19650-2-delivery-process.md` |
| CDE states, status & revision codes | Guidance Part 2 §2, NA Table NA.1 | ✅ `knowledge/00-standards/iso19650-cde-status-revision.md` |
| ISO 19650-3 operational phase | UK Guidance Part 3, Information Protocol template | to distil |
| ISO 19650-5 security | PAS 1192-5 (superseded by 19650-5) | to distil |
| Naming (unique ID fields & codes) | Guidance Part 1 §7.2, BS 1192:2007+A2:2016 | ✅ `knowledge/00-standards/iso19650-naming.md` + skill `iso19650-naming` |
| Level of information need | Guidance Part 2 §4 | ✅ `knowledge/00-standards/level-of-information-need.md` |
| LOD (BIMForum 2021) | LOD Spec 2021 Part I + Guide (2016–2020 superseded) | ✅ `knowledge/00-standards/lod-spec-2021.md` + skill `loin-check` |
| LOD 400 (fabrication) | BIMForum LOD Spec 2021 | ✅ `knowledge/00-standards/lod-400-fabrication.md` |
| Scan accuracy (LOA) | USIBD LOA Specification | ✅ `knowledge/00-standards/usibd-loa.md` |
| COBie | NBIMS-US V3 COBie, COBie Guide 2013, UK Guidance Part B | ✅ `knowledge/00-standards/cobie.md` + skill `cobie-validation` |
| Classification | Uniclass 2023-07, OmniClass 23, ISO 12006-2/3, IEC 81346 | to distil |
| Data dictionaries & quality | ISO 23386, ISO 23387, ISO 8000 | to distil |
| Regional | UK, AU (NATSPEC/ABAB), NZ, Dubai, Singapore, HK, EU Handbook, NEOM | catalogued |

## Templates (knowledge/01-templates)
BEP (PSU v2.1/v3, NATSPEC, CPIx, UCSD), EIR (UoC, NATSPEC), PIR, Project BIM Brief, TIDP matrix, Responsibility matrix, Model audit & BIM checklists — see `library/catalog.yaml` tag `template`.

## Processes (knowledge/03-processes)
| Process | Skill |
|---|---|
| CDE states & promotion | `cde-workflow` |
| Clash detection & issue management | `clash-workflow` |
| Model QA gate | `model-qa-checklist` |
| BEP authoring | `bep-authoring` |
| Capturing lessons | `lesson-capture` |

## Project types (project-types/*.yaml → WORKFLOW.md in each project)
| Type | Skill | Background |
|---|---|---|
| `cad-to-bim` — CAD → coordinated Revit (LOD 300) | `cad-to-bim` | `lod-spec-2021.md` |
| `model-review` — RVT/IFC review vs LOD 300 + report | `model-review-report` | `lod-spec-2021.md`, `level-of-information-need.md` |
| `lod-uplift` — LOD 300 → LOD 400 fabrication | `lod-uplift` | `knowledge/00-standards/lod-400-fabrication.md` |
| `scan-to-bim` — as-built from point cloud | `scan-to-bim` | `knowledge/00-standards/usibd-loa.md` |

## Disciplines (knowledge/02-disciplines)
⚠️ Gap: the source library is strong on information management but thin on discipline-technical content.
Add per discipline: company modelling guidelines, Egyptian codes in force, typical details, family standards.

## Management & strategy (from your course material)
Succar BIM Framework, BIM Framework vs Ecosystem, DT, Lean/LPOM, KPIs, maturity — catalogued under tag `management`.
