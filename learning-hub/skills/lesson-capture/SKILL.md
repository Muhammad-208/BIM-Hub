---
name: lesson-capture
description: How to write a good lesson proposal for the shared Learning Hub. Use whenever an agent discovers a reusable rule, fix, pattern or mistake.
---
# Lesson capture

Call `lesson_propose` with:
- **title** — one line, imperative ("Slope gravity drainage before routing ducts on hospital floors")
- **context** — discipline(s), stage, element types (no client names / prices)
- **what happened** — the problem or discovery
- **rule** — the reusable instruction for next time
- **evidence** — issue id, clash group, standard clause, or test result
- **target** — where it should live: `lessons/`, `knowledge/02-disciplines/<d>/`, `knowledge/03-processes/`, or a skill name
- **tags**

Good lesson = would change what another agent does on a different project. Not a lesson = one-off typo, client preference (→ `team-notes/`), or something already in the hub (search first with `hub_search`).
