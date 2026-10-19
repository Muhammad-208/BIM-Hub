---
title: CDE workflow, status (suitability) codes and revision codes — ISO 19650-1 §12 + UK National Annex to ISO 19650-2
source: "UK BIM Framework Guidance Part 2, 4th ed. 2020 §2 pp28–44 incl. Table 11 (= ISO 19650-2 Table NA.1) and Table 12 (catalog 8ade0515); Guidance Part 1 §6.1 (catalog 76129f61); BS 1192:2007+A2:2016 Table 5 for superseded codes (catalog 9ebc361a)"
version: "ISO 19650-1:2018 / ISO 19650-2:2018 UK NA"
status: current
tags: [iso19650, cde, wip, shared, published, archive, status-code, suitability, revision, metadata, national-annex, S0, S1, S2, S3, S4, S6, S7, A, B, CR]
---

> **الخلاصة:** الـ CDE عبارة عن **workflow + solution**، مش برنامج. فيه 4 states. الـ status code بيقول الملف ينفع يُستخدم في إيه، والـ revision بيقول هو أنهي نسخة. P يعني preliminary و C يعني contractual.

## 1. CDE = solution + workflow
- The CDE is defined in ISO 19650-1 §3.3.15, and its workflow principle is in §12.
- It is the combination of **solution** (technology) and **workflow** (process), and it is often more than one tool (ISO 19650-1 §11.1; Guidance Pt1 §6.1).
- Develop the workflows first, then choose the solutions (Guidance Pt2 §2.2).
- The **project CDE** is provided by the appointing party. Delivery teams may run their own distributed CDEs in addition to it, never instead of it (Pt2 §2.1).

## 2. States (ISO 19650-1 Fig. 10, reproduced in Guidance Pt2 Fig. 3)
| State | Meaning | Gate to the next state |
|---|---|---|
| **WORK IN PROGRESS** | Being developed by its originator / task team; not visible to anyone else | **check / review / approve** (task team), per ISO 19650-2 §5.6.3–5.6.4 |
| **SHARED** | Approved for sharing with other task teams, delivery teams or the appointing party | **review / authorize** (lead appointed party, §5.7.2) and then **accept** (appointing party, §5.7.4) |
| **PUBLISHED** | Authorized for use in more detailed design, construction or asset management | — |
| **ARCHIVE** | Journal of transactions; audit trail of the container's development | continuous |

## 3. Required metadata on every container
- ISO 19650-1 §12.1 recommends a **revision code** and a **status code**.
- ISO 19650-2 §5.1.7 requires the CDE to support both, plus a **classification code** (Guidance Pt2 §2.2.2).
- These are **metadata**. They are not part of the unique ID (container name).

## 4. Status codes: ISO 19650-2 UK National Annex Table NA.1 (Guidance Pt2 Table 11, p39)
| Code | Description | Revision type | State |
|---|---|---|---|
| **S0** | Initial status | Preliminary revision **and version** (P01.01) | WIP |
| **S1** | Suitable for coordination | Preliminary (P01) | Shared |
| **S2** | Suitable for information | Preliminary | Shared |
| **S3** | Suitable for review and comment | Preliminary | Shared |
| **S4** | Suitable for stage approval | Preliminary | Shared |
| S5 | *Withdrawn, no longer used* | — | — |
| **S6** | Suitable for PIM authorization | Preliminary | Shared |
| **S7** | Suitable for AIM authorization | Preliminary | Shared |
| **A1…An** | Authorized and accepted (n = stage) | **Contractual** (C01) | Published |
| **B1…Bn** | Partial sign-off (with comments) | Preliminary | Published |
| **CR** | As-constructed record document | Contractual | Published (for AIM acceptance) |

How the codes are used (Guidance Pt2 Table 13, p43):
- **S1**: use only to coordinate or advance your own work. Usually a geometrical model, but any container can be S1.
- **S2**: for information only, for example a dilapidations report or site photos.
- **S3**: for review and comment only. Never use it for procurement, cost agreement or construction.
- **S4**: the review should end in acceptance that the container meets the stage requirements.
- **S6**: waiting for the lead appointed party to authorize the PIM (§5.7.1–5.7.2). Not for contractual use until authorized and accepted.
  - If the PIM is rejected and this container needs no change, it **stays S6**.
  - If it needs changes, it goes back to **S0**.
- **S7**: for authorization of the handover (Stage 6) information model.
- **An**: authorized and accepted for stage n. For example, A2 is part of the accepted concept design and becomes reference information for stage 3 WIP.
- **CR**: authorized and accepted, previously S7.
- Codes may be extended or reduced per project if documented in the information standard (ISO 19650-2 NA.4.2 Note 2).
- ⚠️ BS 1192:2007+A2:2016 also had **D1–D4** codes (costing / tender / contractor design / manufacture). They are **not** in NA Table NA.1. Use them only if the project information standard adds them.

## 5. Revision codes (ISO 19650-2 NA.4.3; Guidance Pt2 Fig. 6–9)
- Format: `P01.01`, where P or C is the prefix, `01` is the primary revision (what gets shared) and `.01` is the WIP version.
  - **P** = preliminary (non-contractual).
  - **C** = contractual (Published).
- WIP iterations: P01.01, P01.02 … → shared as **P01** → further work P02.01 … → shared **P02** → after authorization and acceptance → **C01** (status An).
- Some containers never reach Published. For example, a structural coordination model may stay preliminary, while the drawings exported from it are published (Pt2 §2.5.3).

## 6. Worked sequence (Guidance Pt2 Table 12, pp41–42, condensed)
| Step | State | Rev | Status | ISO clause |
|---|---|---|---|---|
| Model WIP iterations, then task-team QA of the **container** | WIP | P01.05 | S0 | 5.6.3 |
| Final content review, model shared for coordination | Shared | P01 | S1 | 5.6.4 |
| Delivery-team coordination review | Shared | P01 | S1 | 5.6.5 |
| Drawing exported and QA'd | WIP | P01.01 | S0 | 5.6.3 |
| Drawing shared for comment | Shared | P01 | S3 | 5.6.4–5.6.5 |
| Updated, then submitted for PIM authorization | Shared | P02 | S6 | 5.6.4 / 5.7.1 |
| Lead appointed party authorizes | Shared | P02 | S6 | 5.7.2 |
| Submitted for acceptance | Client Shared | P02 | S4 | 5.7.3–5.7.4 |
| Contractual revision applied and published | Published | **C01** | **A3** | 5.7.4 |

## 7. Checklist for setting up the CDE (Guidance Pt2 §2.7, p44)
- [ ] Project-specific status and revision expansions are documented in the information standard (5.1.4) and agreed in the BEP (5.3.2, 5.4.1).
- [ ] The classification system is defined, including which tables apply to which container types.
- [ ] The container ID codification is defined, **including different names for renditions**: an IFC export must not share the ID of its native model, and a PDF must not share the ID of its native drawing.
- [ ] The CDE solutions support the required metadata and access permissions at individual and organization level (5.1.5, 5.5.2). Metadata transfers between solutions have been tested.
- [ ] Each container type has a documented workflow: develop → check → share → authorize → accept → publish → archive (5.5.2).

## BIM Hub mapping
| Hub CDE state | Gate in the hub | Matching ISO step |
|---|---|---|
| `02-cde/WIP/<DISC>` | discipline agent; status S0 | 5.6.2–5.6.3 |
| → `SHARED` | qa-model + qa-data + qa-doc all PASS (`model_status_set`) | 5.6.3–5.6.4 |
| SHARED review | bim-coordinator federation and clash | 5.6.5 |
| → `PUBLISHED` | bim-manager only, **after client acceptance** (log it with `decision_log`, source = acceptance record) | 5.7.2 + 5.7.4 |
| → `ARCHIVE` | bim-manager | continuous / 5.8.1 |
