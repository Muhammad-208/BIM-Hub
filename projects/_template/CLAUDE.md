# Project {{CODE}} — {{NAME}}

Read `project.yaml` first: team, naming, discipline scopes, models and standards for this project.

| Folder | Purpose | Who writes |
|---|---|---|
| `00-inputs/` | Everything received: EIR/OIR/AIR/PIR, contract, client standards, drawings | You (the user) |
| `01-bep/` | BEP, MIDP, TIDPs, Responsibility Matrix | bim-manager |
| `02-cde/WIP/<DISC>` | Work in progress per discipline | that discipline only |
| `02-cde/SHARED` | Passed QA gate | qa-* (promote) |
| `02-cde/PUBLISHED` | Authorised by manager | bim-manager |
| `03-coordination/` | Clash matrix, reports, viewpoints | bim-coordinator |
| `04-qa/reports/` | QA/QC reports | qa-* |
| `05-state/` | Issues, decisions, model status, messages (via MCP only) | all, through tools |
| `06-reports/` | Weekly / KPI / client reports | bim-manager |
| `07-lessons-inbox/` | Lesson proposals waiting for approval | all, through `lesson_propose` |
| `team-notes/<agent>.md` | Project-specific notes for one agent (overrides, client quirks) | you / the agent |

Before acting, each agent reads `team-notes/<its-name>.md` if it exists.

## Workflow for this project type
@WORKFLOW.md
