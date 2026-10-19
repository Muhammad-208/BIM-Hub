---
title: ISO 19650-1 concepts — parties, teams, information requirements, information models
source: "UK BIM Framework Guidance Part 1: Concepts, 1st ed. April 2019 (catalog 76129f61); quotes/clauses of ISO 19650-1:2018 as cited there"
version: "ISO 19650-1:2018"
status: current
tags: [iso19650, concepts, roles, appointing-party, lead-appointed-party, oir, air, pir, eir, aim, pim, federation, metadata, classification, responsibility-matrix]
---

> **الخلاصة:** ISO 19650 هدفها معلومات **على قد الحاجة** (لا أكتر ولا أقل)، يطلبها العميل بوضوح (OIR → AIR/PIR → EIR)، وتتنتج تعاونيًا داخل CDE، وتتسلّم في نهاية كل مرحلة مع تحقق إنها اتنفذت.

## 1. Purpose (what "BIM according to the ISO 19650 series" means)
A successful outcome has (Guidance Pt1 §2.1, p12):
- Clear definitions of the information the client/owner needs, and of the methods, processes, deadlines and protocols governing its production and checking.
- Quantity and quality of information **just sufficient** for the defined needs — too much is wasted supply-chain effort; too little means uninformed decisions.
- Efficient transfers of information across the life cycle, especially project delivery → asset operation.

It applies to **all** information (models, spreadsheets, drawings, certificates, programmes…) and to the whole life cycle (Pt1 §2.3, p13).

## 2. Parties and teams (ISO 19650-2 Figure 2 — Pt1 Table 2, p14)

| Party (actor) | Meaning | Team | Meaning |
|---|---|---|---|
| **Appointing party** | Leads the project/asset management — typically the client/owner | **Project team** | Everyone involved in the project |
| **Lead appointed party** | Coordinates information exchange between task teams, or between a delivery team and the appointing party | **Delivery team** | A lead appointed party + its task teams (e.g. contractor + subcontractors/suppliers) |
| **Appointed party** | Anyone generating information (contractor, subcontractor, supplier, consultant) | **Task team** | People performing a specific task (e.g. the architecture team) |

- An inexperienced appointing party may get help from a prospective lead appointed party or an independent third party (Pt1 p14).
- A project may have **several lead appointed parties**, each with its own delivery team.

**BIM Hub mapping:** user/client = appointing party · `bim-manager` = information management function of the lead appointed party · `bim-coordinator` = lead appointed party's coordination role · discipline agents = task teams · `qa-*` = task-team QA check + lead appointed party review (ISO 19650-2 §5.6.3–5.6.5).

## 3. Hierarchy of information requirements (ISO 19650-1 §5 — Pt1 §5.2, p20)
1. **OIR** — Organizational Information Requirements → organizational objectives.
2. **PIR** — Project Information Requirements → purpose, design and construction of an asset.
3. **AIR** — Asset Information Requirements → operation and maintenance of an asset.
4. **EIR** — Exchange Information Requirements → one **appointment**.

- "The appointing party should understand what information is required concerning their asset(s) or project(s) to support organizational or project objectives" (ISO 19650-1 §5.1, quoted Pt1 p20).
- Trap: over-detailed EIRs stifle delivery-team innovation (Pt1 p20).
- Lead appointed parties may add requirements when cascading to their supply chain (ISO 19650-2 §5.4.3), proportionately, placed with the party best able to deliver.

## 4. Information models: PIM and AIM (ISO 19650-1 Fig. 3 — Pt1 p15)
- **A** start of delivery phase: relevant information transferred AIM → PIM.
- **B** design intent model progressively develops into the virtual construction model.
- **C** end of delivery phase: relevant information transferred PIM → AIM.
- An information model is **a set of information containers**, not just a geometric model (Pt1 §6.2, p23). Information container: ISO 19650-1 §3.3.12. The ISO 19650-1 definition, as quoted in Guidance Pt2 §6.4.2.2: "a set of information retrievable from within a file, system or application storage hierarchy". A container can be a sub-directory, a file, or a distinct subset of a file (chapter, section, layer, symbol).

## 5. Information delivery cycle (Pt1 §5.1, p19)
1. Appointing party states need + information requirements (+ reasons why information is needed).
2. Each prospective lead appointed party answers in its **pre-appointment BEP** (capability and capacity).
3. Mobilization: agree roles, responsibilities, information delivery plan (ISO 19650-2 §5.4, §5.5); briefings/training.
4. Level of information need, verification/validation and quality-checking rules are set.
5. Assurance that requirements are met at the end of every stage (ISO 19650-1 §6.3.3).
6. Asset information is baselined and handed over for O&M.

## 6. Risk and responsibility
- Information-based risk assessment is part of overall risk management (ISO 19650-1 §6.3.1). Address it in the pre-appointment BEP (ISO 19650-2 §5.3.6 risk register) (Pt1 §5.3, p20).
- Two responsibility matrices (Pt1 §5.4, p21):
  1. **Information management activities**: Annex A of ISO 19650-2 has an indicative template.
  2. **Information deliverables** against exchange stages: no template is given. It grows from high level at tender to detailed at appointment.

## 7. Federation strategy & container breakdown structure (ISO 19650-1 §10.4 — Pt1 §6.3, p24)
- **Federation strategy** explains how and why the information model is divided. The appointing party sets it at project level, and the lead appointed party sets it for its delivery team. Reasons include security, spatial coordination and transmission.
- **Container breakdown structure** gives smaller units so several parties can work at once without overwriting each other.
  - It shows mostly in the **Volume/System** field of the container ID, but all ID fields segregate.
  - Classification metadata can be used too.
- It applies to **all** information types, not only geometry.

## 8. Metadata & classification (Pt1 §6.4, §6.6, p24–26)
- Agree where metadata lives: on the element, on the container, or in a linked database. Title-block placement follows BS EN ISO 7200.
- Classification should follow **ISO 12006-2**. The UK implementation is **Uniclass 2015**. Object information follows **ISO 12006-3**.
- ISO 19650-2 §5.1.7 requires each container to be classified through a metadata attribute.

## 9. Level of information need
Introduced in ISO 19650-1 §11.2. Do not abbreviate it. See `level-of-information-need.md`.

## 10. Transition from PAS 1192 / BS 1192 (Pt1 §4.4, p18)
- Projects contracted under BS 1192:2007+A2:2016 / PAS 1192-2:2013 should normally continue to completion.
- Transition is best at the start of a stage. Use PD 19650-0 Transition Guidance.

## Agent use
- `bim-manager`: use §3 to check that the EIR traces to PIR/AIR. Missing purposes go in an EIR clarification (`decision_log`).
- Anyone citing roles: use the exact terms in §2. "Employer" is not an ISO 19650 term (Pt1 §3.1).
