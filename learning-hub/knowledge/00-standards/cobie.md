---
title: COBie — what it is, worksheets & keys, deliverables by stage, naming and quality rules
source: "NBIMS-US V3 §4.2 COBie (catalog 4afadadb) for worksheet definitions/keys; The COBie Guide, East & Carrasquillo-Mangual, 2013-03-12 v05 (catalog eb72e369) pp9–26 for deliverables and quality rules; UK Guidance Part B (catalog de557e70) for COBie as an MVD in ISO 19650"
version: "COBie 2.4 / NBIMS-US V3 (2015)"
status: current
tags: [cobie, handover, fm, asset-information, nbims, mvd, ifc, spreadsheet, space, type, component, system, zone, attribute, naming]
---

> **الخلاصة:** COBie مش متطلبات جديدة. هو **format مفتوح** لنفس معلومات الـ O&M اللي كانت بتتسلّم ورق. بيتسلم على مراحل: الـ Architect مسؤول عن مرحلة التصميم، والـ Contractor عن مرحلتي Beneficial Occupancy والـ As-Built. وأهم قاعدة: **أسماء فريدة**، ولازم تطابق الرسومات.

## 1. What COBie is
- Construction-Operations Building information exchange: the international format for exchanging information about **managed facility assets** (COBie Guide, exec summary).
- It **does not add requirements to contracts**. It changes the format of existing deliverables, such as equipment schedules and O&M manuals, from paper or proprietary formats to an open format. What is delivered, when and by whom must be set by the client (the Guide / Appendix A / EIR).
- In ISO 19650 terms it is a **model view definition (MVD)** of IFC: "An example of an MVD is COBie 2.4". It can be referenced in the project's information standard under ISO 19650-2 §5.1.4 (UK Guidance B §1.4).
- Delivered as **IFC (STEP Part 21)** or the **COBie 2.4 spreadsheet**. Referenced documents go as PDF, TIFF or JPEG (Guide §6).

## 2. Worksheets and keys (NBIMS-US V3 §4.2.3.2.2)
| Sheet | Content | Key |
|---|---|---|
| Contact | People and companies referenced anywhere | Email |
| Facility | **Only one row**; multiple facilities = separate files | Name |
| Floor | Vertical levels; also site areas | Name |
| Space | Horizontal decomposition of floors by function | Name |
| Zone | Aggregations of spaces with a common purpose | Name + Category + SpaceName |
| Type | Products and equipment types; name **must match the drawings** | Name |
| Component | Individual instances of Types; name must match the drawings | Name |
| System | Aggregations of components providing a function | Name + Category + ComponentNames |
| Assembly | Types or components made of other types or components | Name |
| Connection | Logical connections between Types or Components | Name |
| Spare | Spare parts, replacement parts, lubricants | Name + TypeName |
| Resource | Tools, materials, training needed for maintenance | Name |
| Job | Operate / PM / start-up / shutdown / troubleshoot tasks per Type | Name + TypeName + TaskNumber |
| Impact | Health, safety, economic, environmental impacts | Name |
| Document | External files linked to rows | Name + SheetName + RowName + Stage |
| Attribute | Properties of rows in other sheets | Name + SheetName + RowName + Category |
| Coordinate | Simple geometry | Name |
| Issue | Exceptions / business-process issues | Name + SheetName + RowName |

## 3. Deliverables by stage (Guide §5–6)
| Deliverable | Responsible | Main content |
|---|---|---|
| **Design Development (≈35%)** | Architect | Contact (BIM manager), Facility, Floors, Spaces (room data sheet level), Zones, scheduled architectural/plumbing/lighting Types and Components, **Systems by name and classification only**, Documents, required Attributes |
| **Construction Documents (100%)** | Architect coordinates all disciplines | Complete set of spaces and **all scheduled products and equipment** with basis-of-design attributes. Components grouped into Systems. **One merged file per facility**, with no duplicate assets or geometry |
| **Beneficial Occupancy** | General Contractor (commissioning agent may assist) | As-installed and commissioned. Adds **Spare, Resource, Job** (PM and operations schedules), submittal and commissioning Documents, nameplate photo and nameplate Attributes per Component |
| **As-Built** | General Contractor | Final update reflecting as-built drawings, with complete commissioning information |

- One COBie file per facility, plus a separate **site** file (Floor.FloorType = "Site").
- Content must match the drawings and schedules of the same stage (Guide §6–7).

## 4. Quality rules (Guide §7–8)
- **Unique names** for Space.Name, Type.Name and Component.Name.
  - Allowed characters: `[0-9][a-z][A-Z]`, `-` and `_`. **No spaces.**
  - Names must match the drawings.
  - During design, the Architect resolves duplicates. During construction, the Contractor does.
- **Space**: one row per functional area of every room. Large rooms with several areas use `-A`, `-B`… suffixes. Space.Tag is used for signage.
- **Type.Name** starts with a recognizable product signifier, e.g. `DOOR-A`, `LIGHT-A`.
- **Component.Name**, when schedules list types only: `Type.Name-Space.Name-NN`, e.g. `Sink-A-100-01`.
- Every Component sits in the Space where it is found or from which it is operated. It also gets the attribute **SpatialPlacement**: UnderFloor / AboveCeiling / InWall / InSpace / OnRoof / OnSite.
- **Facility geo-location attributes**: Longitude, Latitude, Elevation, Rotation.
- **Classification** is required on Contact, Facility, Space, Type and System. The default is OmniClass unless the contract says otherwise (in the UK, Uniclass 2015).
- **Zones and Systems**:
  - A Space appears only once per zone *type*, but can belong to zones of different types. The same rule applies to Components and Systems.
  - Nesting is done by name, or by ParentZone / ParentSystem attributes.
- **Units**: one project unit set, approved by the owner. Every numeric Attribute carries its unit.
- **Merging several models**: run a pre-flight duplicate check. The more detailed discipline schedule overrides the architectural one.
- **Only substantive attributes**: no software-internal parameters (Guide §8.1.3).
- Every deliverable comes with a **checker report** proving format compliance (Guide §7).

## Agent use
- `qa-data`: skill `cobie-validation` runs checks 1–6 against this file, reporting completeness % per sheet and broken keys.
- Discipline agents: schedule headings and Type naming must be agreed **before design** (Guide §8.1.1 pre-coordination submittal). Ask bim-manager for the client's property list.
- bim-manager: put COBie responsibility (who fills which sheet and columns) in the Responsibility Matrix (Guide §5).
