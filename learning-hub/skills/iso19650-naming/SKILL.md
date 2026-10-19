---
name: iso19650-naming
description: Validate or build information-container names per ISO 19650-2 (UK National Annex style) and assign status/revision codes. Use when naming files, checking a batch of drawings/models, or explaining a name.
---
# ISO 19650 naming

## Field structure (UK NA to BS EN ISO 19650-2)
`Project - Originator - Volume/System - Level/Location - Type - Role - Number`
e.g. `AOH-WYA-ZZ-03-DR-A-0101`

| Field | Rule | Notes |
|---|---|---|
| Project | 2–6 chars, agreed per project | from `project.yaml → code` |
| Originator | 3–6 chars, unique per organisation | |

Renditions (IFC of a model, PDF of a drawing) get their **own** ID — never the same as the native container.
| Volume/System | 1–2 chars | `ZZ` all volumes, `XX` none |
| Level/Location | 2 chars | `ZZ` multiple, `XX` none, `00` ground, `B1` basement |
| Type | 2 chars | M3 model · DR drawing · SP spec · RP report · SH schedule · CA calcs · MI minutes · VS visualisation |
| Role (2021 NA: Discipline) | 1 char standard (BS 1192 §10.2); J N R U V or longer = project-defined | A arch · B bldg surveyor · C civil · D drainage/highways · E elec · F FM · G surveyor · H heating & vent · I interior · K client · L landscape · M mech · P public health · Q QS · S struct · T planner · W contractor · X subcontractor · Y specialist · Z general |
| Number | 4 digits (BS 1192 §13.2), leading zeros; project may define otherwise | sequential within the preceding fields |

The project's own rules in `project.yaml → naming` **override** this table.

## Status (suitability) codes — metadata, not part of the file name (UK NA Table NA.1)
WIP: **S0** · SHARED: **S1** coordination, **S2** information, **S3** review & comment, **S4** stage approval, **S6** PIM authorization, **S7** AIM authorization (S5 withdrawn) · PUBLISHED: **A1…An** authorized & accepted (contractual rev), **B1…Bn** partial sign-off (preliminary rev) · **CR** as-constructed record.
D1–D4 are old BS 1192 codes — only if the project information standard adds them.
Full detail: hub `knowledge/00-standards/iso19650-cde-status-revision.md` and `iso19650-naming.md`.

## Revision codes
Preliminary (SHARED): `P01`, `P02` … with WIP sub-versions `P01.01`. Contractual (PUBLISHED): `C01`, `C02` …

## Procedure
1. Run `naming_validate` (bimhub MCP) on the names/folder.
2. For each failure, give the field, found value, expected rule, and a corrected name.
3. Status vs CDE state mismatch (e.g. S0 file in SHARED) is a defect too.
