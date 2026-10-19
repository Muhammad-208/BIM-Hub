---
name: cobie-validation
description: Validate COBie deliverables (spreadsheet or IFC-derived) for completeness and consistency at handover stages. Use when preparing or checking FM handover data.
---
# COBie validation

Core sheets: Contact · Facility · Floor · Space · Zone · Type · Component · System · (Assembly, Connection, Spare, Resource, Job, Document, Attribute as required).

Background & stage-by-stage content: hub `knowledge/00-standards/cobie.md`.

Checks
1. Mandatory fields filled (required = per NBIMS-US V3 COBie / project EIR). No "n/a" where a value is required.
2. Keys resolve: every Component.TypeName exists in Type; every Component.Space exists in Space; every Space.FloorName exists in Floor.
3. Uniqueness: Name unique within each sheet; Space/Type/Component names only `[0-9A-Za-z_-]`, no spaces; Component in a Space; `SpatialPlacement` attribute present.
4. Classification column populated with the agreed table.
5. Contacts referenced (CreatedBy, Manufacturer, Warranty guarantors) exist in Contact.
6. Counts sanity: components vs model counts per category.
Report: sheet-by-sheet completeness %, broken references, duplicates.
