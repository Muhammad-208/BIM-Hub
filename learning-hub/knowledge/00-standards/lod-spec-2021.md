---
title: BIMForum Level of Development (LOD) Specification 2021 — definitions, rules of use, Model Element Table
source: "BIMForum LOD Specification 2021 Part I, Guide & Commentary, Dec 2021 (catalog 9ce7873f) — pp5, 16–17, 265–275"
version: "2021"
status: current
supersedes: "LOD Spec 2016, 2017, 2018, 2019, 2020 (all in library, marked superseded)"
tags: [lod, level-of-development, bimforum, lod100, lod200, lod300, lod350, lod400, lod500, model-element-table, mea, uniformat, omniclass, uniclass, coordinates]
---

> **الخلاصة:** الـ LOD هنا يعني **Level of Development**، يعني قد إيه تقدر **تعتمد** على شكل العنصر، مش Level of Detail. ومفيش حاجة اسمها "LOD 300 model". كل عنصر ليه LOD في كل milestone.

## 1. Development ≠ Detail (p16)
- **Level of Detail** = how much detail is put into the element. It is the *input*.
- **Level of Development** = how far the element's geometry has been thought through, i.e. how much others may **rely** on it. It is reliable *output*.
- Some countries use "Level of Detail" and other numbering for the same concept. In this specification, LOD always means Level of Development.

## 2. Definitions (AIA G202-2013 wording + BIMForum interpretation, pp16–17)
| LOD | Definition (short) | BIMForum interpretation |
|---|---|---|
| **100** | Symbol or generic representation. Doesn't meet 200. Information may be derived from other elements (e.g. cost/m², HVAC tonnage) | Not a geometric representation; everything derived is **approximate** |
| **200** | Generic system/object/assembly with **approximate** quantity, size, shape, location, orientation | Generic placeholders or space-reservation volumes; approximate |
| **300** | **Specific** system/object/assembly in quantity, size, shape, location, orientation | Measurable directly from the model **without notes or dimension call-outs**; project origin defined and element located accurately relative to it |
| **350** | As 300 **plus interfaces** with other building systems | Parts needed for coordination with nearby or attached elements are modelled (supports, connections). BIMForum addition for clash detection and layout |
| **400** | As 300 with **detailing, fabrication, assembly and installation** information | Enough detail and accuracy to **fabricate** |
| 500 | Field-verified representation | **Not defined or illustrated**: it is field verification, not a progression step |

Example, light fixture (p17):
- **100**: cost/sf attached to the floor slab
- **200**: generic fixture, approximate size, shape and location
- **300**: design-specified 2x4 troffer, specific size, shape and location
- **350**: actual manufacturer model, specific size, shape and location
- **400**: as 350 plus special mounting details

## 3. Rules of use (Guide §1–2, pp265–269)
1. **LODs are not phases** (§1.1.2). At the end of SD a model has elements at 100, 200, some at 300, maybe 400.
2. **There is no "LOD ### model"** (§1.1.3). Say "100% SD model", with LODs defined per element.
3. **Not a set of requirements** (§1.2.1). It is a *language* for writing requirements. The project decides what is modelled, when and by whom, usually in the BEP (§1.2.2).
4. **Minimum and cumulative** (§2.2.2–2.2.3). An element reaches an LOD only when *all* its requirements are met, and each LOD includes all lower ones.
5. **Order of precedence** (§2.2.1). The specific expansion (e.g. C1010) beats the general one (C10), which beats the fundamental definitions.
6. **Model Element Author (MEA)** (§2.2.4, from AIA E203-2013). The party responsible for developing an element to the LOD required at a milestone.
7. **2D supplements are out of scope** (§2.2.5). The specification covers only modelled 3D and the non-graphic data attached to it.
8. **Size thresholds** (e.g. don't model conduit under 10 mm) are project-specific and go in the BEP Model Element Table notes (§2.3.1).
9. Benefits when referenced from the BEP: limited **reliance**, multiple uses, efficient sequencing, **no over-modelling** (§2.4).

## 4. Implementation methods (§2.5)
- **Model Element Table**: each row is a Uniformat element. For each milestone it gives LOD + MEA + Notes. Every element in the row is assumed to be at that LOD.
- **Per-element attributes**: `Current LOD` and `Target LOD` on every element. More flexible, and software can highlight elements where Current < Target. **Recommended for BIM Hub** so qa-data can check it automatically.

## 5. Structure (§3)
- **Part I**: element geometry, with narrative + illustrations per element, organized by **CSI Uniformat 2010**, with OmniClass and **Uniclass 2015** indices (p5).
- **Part II**: attribute tables (Excel).
  - Attributes are split into **Baseline** (default list) and **Additional** ("shopping list").
  - Data types: Text, Number, Logical, Date, Time, Datetime in ISO format.
  - MEPF tables have a Global part and an Item-specific part.
- Part II file in the library: `LOD Spec 2020 Part II 2020-12-31.xlsx` (latest Part II available).

## 6. Coordinates (Guide §4.1, pp274–275), the single most costly omission
- Define the local building origin (Revit internal 0,0) relative to the **south-west grid intersection**, offset south and west so the whole building is in positive X-Y.
- Z = 0, 100' or absolute. Plan north = +Y.
- Keep four systems linked by fixed offsets and rotation, documented in the BEP:
  - **Object**
  - **Building (local)**
  - **Campus/site**
  - **Civil (state plane / national grid)**
- The structural engineer sets the origin with the architect at the start of DD, coordinated with the civil engineer and surveyor.

## Agent use
- Discipline agents: model each element to the **Target LOD** of the current milestone. Don't go beyond it unless asked.
- qa-model: check geometry against the milestone LOD (skill `model-qa-checklist` #10). Check the shared coordinates first (#1).
- bim-manager: put the Model Element Table, or the LOIN table with LOD in its geometry column, in `01-bep/`.
