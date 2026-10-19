---
title: ISO 19650-2 delivery phase — the 8 activities and all sub-clauses, who does what, appointment documents, TIDP/MIDP
source: "UK BIM Framework Guidance Part 2: Processes for Project Delivery, 4th ed. April 2020 (catalog 8ade0515) — §1, §6, §9 process summary pp.143–152"
version: "BS EN ISO 19650-2:2018"
status: current
tags: [iso19650, delivery, process, appointment, tender, mobilization, bep, tidp, midp, responsibility-matrix, risk-register, close-out, lessons-learned]
---

> **الخلاصة:** 8 أنشطة. 5.1 و 5.8 مرة واحدة للمشروع كله. من 5.2 لـ 5.7 بيتكرروا مع كل appointment. الـ appointing party بيحدد الإطار، والـ lead appointed party بيرد بـ BEP ثم MIDP، والـ task teams بتعمل TIDPs، وبعدين إنتاج وQA ومراجعة وتسليم.

Activities **5.1** and **5.8** apply to the project as a whole. **5.2 to 5.7** repeat for every appointment the appointing party tenders (Guidance Pt2 Table 2, p9).

## 5.1 Assessment and need (appointing party), establishing the project's information framework
| Clause | Activity |
|---|---|
| 5.1.1 | Appoint individuals to undertake the information management function |
| 5.1.2 | Establish the project's information requirements |
| 5.1.3 | Establish the project's information delivery milestones |
| 5.1.4 | Establish the project's information standard (naming, status, classification, level of information need method…) |
| 5.1.5 | Establish the project's information production methods and procedures |
| 5.1.6 | Establish the project's reference information and shared resources |
| 5.1.7 | Establish the project's common data environment (must allow revision, status and classification metadata) |
| 5.1.8 | Establish the project's information protocol |

## 5.2 Invitation to tender (appointing party)
| 5.2.1 | Establish the appointing party's exchange information requirements (EIR) |
|---|---|
| 5.2.2 | Assemble reference information and shared resources |
| 5.2.3 | Establish tender response requirements and evaluation criteria |
| 5.2.4 | Compile invitation to tender information |

## 5.3 Tender response (prospective lead appointed party + its appointed parties)
| 5.3.1 | Nominate individuals to undertake the information management function |
|---|---|
| 5.3.2 | Establish the delivery team's (pre-appointment) BIM execution plan |
| 5.3.3 | Assess each task team capability and capacity |
| 5.3.4 | Establish the delivery team's capability and capacity |
| 5.3.5 | Establish the delivery team's mobilization plan |
| 5.3.6 | Establish the delivery team's risk register |
| 5.3.7 | Compile the delivery team's tender response |

## 5.4 Appointment, finalizing and confirming appointments
| 5.4.1 | Confirm the delivery team's BIM execution plan |
|---|---|
| 5.4.2 | Establish the delivery team's detailed responsibility matrix |
| 5.4.3 | Establish the lead appointed party's exchange information requirements (to its appointed parties) |
| 5.4.4 | Establish the task information delivery plans (TIDP), by each task team |
| 5.4.5 | Establish the master information delivery plan (MIDP), by the lead appointed party |
| 5.4.6 | Complete lead appointed party's appointment documents |
| 5.4.7 | Complete appointed party's appointment documents |

## 5.5 Mobilization
| 5.5.1 | Mobilize resources |
|---|---|
| 5.5.2 | Mobilize information technology |
| 5.5.3 | Test the project's information production methods and procedures |

## 5.6 Collaborative production of information (WIP → Shared), iterative
| 5.6.1 | Check availability of reference information and shared resources |
|---|---|
| 5.6.2 | Generate information |
| 5.6.3 | Undertake quality assurance check (the **container**, against the information standard) |
| 5.6.4 | Review information and approve for sharing (the **content**) |
| 5.6.5 | Information model review (by the lead appointed party, across containers, e.g. spatial coordination) |

If a check or review fails, the work returns to 5.6.2.

## 5.7 Information model delivery, at each information milestone (Shared → Published)
| 5.7.1 | Submit information model for lead appointed party authorization |
|---|---|
| 5.7.2 | Review and authorize the information model (lead appointed party) |
| 5.7.3 | Submit information model for appointing party acceptance |
| 5.7.4 | Review and accept the information model (appointing party) |

If the model is rejected, the work goes back to 5.6.1.

## 5.8 Project close-out (appointing party + lead appointed parties)
| 5.8.1 | Archive the project information model |
|---|---|
| 5.8.2 | Capture lessons learned for future projects |

## Appointment documents of a lead appointed party (Guidance Pt2 Table 3, p11)
| Component | Prepared by | Level |
|---|---|---|
| Information standard | appointing party | project |
| Information production methods and procedures | appointing party | project |
| Information protocol | appointing party | project |
| Exchange information requirements | appointing party | appointment |
| BIM execution plan | lead appointed party | appointment |
| Master information delivery plan | lead appointed party | appointment |

## TIDP — ISO 19650-2 §5.4.4 (Guidance Pt2 §6.4, pp89–93)
Every task team produces one. For each information container it lists:
- name and title
- predecessors / dependencies
- **level of information need**
- estimated production duration
- author
- delivery milestones

Notes:
- §5.4.4 does not require any particular template. The TIDP can be a spreadsheet or a programme tool.
- Two possible approaches:
  - **file-based**: predict container IDs. This is hard to keep up to date and creates heavy change control.
  - **task-based**: list the information needed, without fixing how many files it becomes.
- The TIDP forms part of the appointed party's appointment (§5.4.7).

## MIDP — ISO 19650-2 §5.4.5 (Guidance Pt2 §6.5, pp94–95)
- The lead appointed party aggregates the TIDPs. It considers:
  - the responsibilities in the detailed responsibility matrix
  - dependencies between task teams
  - review durations of the appointing party and the lead appointed party
- Then it must:
  1. **baseline** the deliverables and dates
  2. **notify** each task team of changes
  3. **inform the appointing party of risks**, and record them in the risk register (§5.3.6)
- The MIDP forms part of the lead appointed party's appointment (§5.4.6). Changes go through agreed change control.

## Agent use
| Clause | BIM Hub owner | Tool / output |
|---|---|---|
| 5.3.2 / 5.4.1 BEP | bim-manager | skill `bep-authoring`, `01-bep/` |
| 5.3.6 risk register | bim-manager | `01-bep/risk-register` + `decision_log` |
| 5.4.4 TIDP | each discipline agent | `01-bep/TIDP-<DISC>` |
| 5.4.5 MIDP | bim-manager (bim-coordinator compiles) | `01-bep/MIDP` |
| 5.6.3 QA check | qa-model / qa-data / qa-doc | `model_status_set(qa_*)` |
| 5.6.5 model review | bim-coordinator | clash workflow, `issue_create` |
| 5.7.1–5.7.2 authorize | bim-manager | `model_status_set(state=PUBLISHED)` after S6 review |
| 5.8.2 lessons | everyone → bim-manager | `lesson_propose` → `lesson_approve` |
