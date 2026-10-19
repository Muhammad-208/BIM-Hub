---
name: loin-check
description: Check Level of Information Need (geometry + alphanumeric + documentation) per element class and stage, using the project LOIN table or BIMForum LOD Spec 2021 as fallback. Use when validating model data or defining requirements.
---
# LOIN check

LOIN (ISO 7817-1, formerly EN 17412-1) = for **purpose + milestone + actor + object**: geometrical info (detail, dimensionality, location, appearance, parametric behaviour), alphanumerical info (identification + properties), documentation.

LOD (BIMForum) is the US-practice shorthand: 100 symbolic · 200 generic · 300 specific · 350 + interfaces · 400 fabrication · 500 field-verified (not a progression level in Spec 2021 terms).

Background: hub `knowledge/00-standards/level-of-information-need.md` and `lod-spec-2021.md`. Recommended: elements carry `Current LOD` / `Target LOD` parameters (LOD Spec 2021 Guide §2.5.2) so this check is automatic.

## Procedure
1. Get the LOIN table from `01-bep/` (columns: element class, stage, geometry level, required properties, docs). No table → use BIMForum LOD Spec 2021 Part I for geometry and ask bim-manager to confirm properties.
2. For each element class in scope: `list_elements(category)` then `get_element_parameters` (revit MCP) for a sample or all.
3. Score: completeness % = filled required properties / required properties. Flag placeholders (TBC, 0, -, n/a where a value is required).
4. Report per class: count, completeness %, top missing properties, worst elements (GUIDs).
