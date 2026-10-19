---
name: clash-workflow
description: End-to-end clash detection and resolution - clash matrix, tolerances, Navisworks tests via MCP, grouping, issue assignment, follow-up. Use for any coordination or clash request.
---
# Clash workflow

## 1. Clash matrix (03-coordination/clash-matrix.yaml)
```yaml
- id: STR-MECH-01
  a: {discipline: str, set: "STR - Framing"}
  b: {discipline: mech, set: "MECH - Ducts"}
  type: hard          # hard | clearance | duplicate
  tolerance_mm: 25
  priority: 1
```
Default priorities: 1 STR×MEP · 2 ARC×STR · 3 MEP×MEP (gravity drainage first) · 4 clearance (maintenance, ceiling void) · 5 soft/duplicates.

## 2. Run (navisworks MCP)
`list_clash_tests` → create missing with `create_clash_test` (selection sets from the matrix) → `run_clash_test` → `get_clash_results`.

## 3. Group — report problems, not clashes
Group by **level + grid zone + system + host element**. One beam hit by 40 duct segments = 1 group. Use `create_clash_group` + `add_clashes_to_group`. Mark approved/false positives with `set_clash_group_status`.

## 4. Assign
Each group → `issue_create` (owner discipline, GUIDs, viewpoint name, proposed fix, due date).
Who moves: smaller service before larger · pressure before gravity · MEP before STR · anything before façade — unless BEP says otherwise.

## 5. Follow-up
Re-run after each SHARED update. Closed in Navisworks + verified in model → `issue_update(status=closed)`. Report trend (new/resolved/open by discipline) to bim-manager.
