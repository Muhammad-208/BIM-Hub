---
title: Level of information need (LOIN) — framework, who/when/where, and how it differs from LOD
source: "UK BIM Framework Guidance Part 2, 4th ed. 2020 §4 pp75–80 (catalog 8ade0515); Guidance Part 1 §6.5 (catalog 76129f61); ISO 19650-1 §11.2 as cited"
version: "ISO 19650-1:2018 §11.2; EN 17412-1 (now ISO 7817-1) referenced"
status: current
tags: [loin, level-of-information-need, geometrical, alphanumerical, documentation, purpose, en17412, iso7817, lod, loi]
---

> **الخلاصة:** الـ LOIN بيبدأ دايمًا من **الغرض (purpose)**. بعدها نحدد الـ geometry والـ alphanumeric data والـ documentation اللي الغرض ده محتاجه، **لا أكتر ولا أقل**. الأرقام زي "LOD 300" أو "LOI 4" لوحدها مش LOIN.

## 1. What it is
- It is a framework to define the **quality, quantity and granularity** of the information required, for each **purpose**, "no more and no less". Extra information is waste (Guidance Pt2 §4.2). It was introduced in ISO 19650-1 §11.2.
- Defining it without a clear purpose is not in line with ISO 19650-1 (Pt2 §4.2).
- Never abbreviate "level of information need" (Pt1 §6.5.1; Pt2 §4.1).
- The receiver uses it to shape the "holes" (the requirements skeleton). The provider fills them, which makes automated checking possible (Pt2 §4.2, Fig. 28).

## 2. Why the old metrics fail (Pt2 §4.3)
- The UK "level of definition" (LOD + LOI on a 1–7 scale) was too generic and not tied to purpose. It could not be checked automatically.
- Example: an air terminal set to "LOI 4" with no purpose and no named properties (sound frequency, sound pressure, manufacturer). It is open to interpretation and raises risk.

## 3. How to define it (Pt2 §4.6)
1. **Purpose**: why the information is needed. This is always required.
2. **Geometrical information**, if applicable.
3. **Alphanumerical information**, if applicable.
4. **Documentation**, if applicable.

Each sub-division is detailed in EN 17412-1, now ISO 7817-1. Facets used in the guidance: purpose, content, form, format (Pt2 §3.2.4.2).

## 4. Who and when (Pt2 §4.4–4.5)
- The **appointing party** defines it for each deliverable. At minimum it defines the **purpose** and may get help from the lead appointed party or an independent third party, avoiding conflicts of interest.
- The lead appointed party may refine the granularity for its own work, using the appointing party's framework as the base.
- It is defined every time an information requirement is set:
  - in the AIR
  - at tender
  - by the designer (e.g. for accessibility analysis)
  - by the contractor (e.g. for H&S analysis)
  - by a manufacturer (e.g. to 3D-print a heritage component)
- Define it fully **at the start of each appointment**. Don't keep changing it during the appointment.
- Example: at feasibility the QS needs only the number of occupants. At detailed design it needs GIFA.

## 5. Where it lives (Pt2 §4.7)
| Document | ISO 19650-2 clause |
|---|---|
| Method of assignment, in the **information standard** | 5.1.4 c |
| Requirements, in the **EIR** | 5.2.1 b |
| What will be delivered, in each **TIDP** | 5.4.4 |
| Delivery, recorded in the **BEP** | Pt1 §6.5.2 |

Define it so both people **and software** can do:
- **verification**: does the container exist?
- **validation**: is its content correct and complete?

(Pt1 §6.5.2.)

## 6. LOIN vs LOD (BIMForum)
| | Level of information need | BIMForum LOD 100–400 |
|---|---|---|
| Driver | **Purpose** at each exchange | Reliability of element **geometry** |
| Covers | geometry + alphanumeric + documentation | geometry (Part I) + attribute tables (Part II) |
| Unit | per information container / object per purpose | per model element per milestone |
| Status | ISO framework | US industry specification |

Practical rule for the hub: define LOIN per purpose. Where geometry reliability must be stated, quote BIMForum LOD **inside** the geometrical part of the LOIN. See `lod-spec-2021.md`.

## 7. LOIN table template (01-bep/LOIN.xlsx or .md) — rows are illustrative
| Purpose | Milestone | Actor (receiver) | Object / class (Uniclass) | Geometry (detail · dimensionality · location · appearance · parametric) | Alphanumeric properties (name · unit · data type) | Documentation |
|---|---|---|---|---|---|---|
| Spatial coordination | Stage 3 end | lead appointed party | ductwork (Uniclass Ss code) | 3D, actual size incl. insulation, located ±25 mm | System, Size, InsulationThickness (mm) | — |
| FM handover | Stage 6 | appointing party FM | air handling unit (Uniclass Pr code) | symbolic box + access zone | COBie Type/Component + SerialNumber, InstallationDate, WarrantyDuration | O&M manual PDF |

## Agent use
- `qa-data` checks completeness against this table (skill `loin-check`). Missing table → ask bim-manager. Never invent requirements.
- Discipline agents: model to the LOIN. Over-modelling is a defect too.
