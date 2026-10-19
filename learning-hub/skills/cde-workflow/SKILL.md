---
name: cde-workflow
description: CDE states (WIP, SHARED, PUBLISHED, ARCHIVE) and who may promote a container between them, per ISO 19650-1 §12 and this hub's agent hierarchy. Use when moving or approving models/documents.
---
# CDE workflow

| Transition | Gate | Done by | Tool |
|---|---|---|---|
| WIP → SHARED | **Check, review, approve** — qa-model + qa-data + qa-doc all PASS | QA agents record PASS; bim-coordinator accepts into federation | `model_status_set` |
| SHARED → PUBLISHED | **Review & authorise** (§5.7.2, lead appointed party) **+ client acceptance** (§5.7.4) — coordination signed off, no open critical issues | bim-manager only, citing the acceptance record | `model_status_set(state=PUBLISHED)` + `decision_log` |
| PUBLISHED → ARCHIVE | Superseded by a newer revision | bim-manager | `model_status_set(state=ARCHIVE)` |
| SHARED → WIP (rejection) | QA FAIL or coordinator rejection | QA / coordinator | `issue_create` + `message_send` |

Rules
- A discipline never promotes its own work.
- Status code must match the state (see `iso19650-naming`).
- Full status/revision tables and the worked P01.01 → C01 sequence: hub `knowledge/00-standards/iso19650-cde-status-revision.md`.
- Every PUBLISHED container has a decision record (who authorised, on what evidence).
