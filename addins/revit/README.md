# BIM Hub — Revit bridge add-in (Revit 2020 → 2027)

One C# project, built per Revit version, that lets the BIM Hub `revit` MCP server read and (with permission) write the active Revit model.

```
Agent ──MCP──► bimhub.servers.revit (Python, permissions) ──HTTP localhost:8766──► this add-in ──ExternalEvent──► Revit API
```

## Install
```powershell
powershell -ExecutionPolicy Bypass -File "E:\Ai\BIM Hub\addins\revit\install.ps1"
```
- Installs the prebuilt DLL from `dist\<year>\` into `%APPDATA%\Autodesk\Revit\Addins\<year>\` for every Revit installed on this PC (2020–2027). Close Revit first.
- On first launch Revit asks about the unsigned add-in → **Always Load**.
- Check: **Add-Ins → BIM Hub → Bridge Status**, or from the hub `.\bimhub.cmd doctor` (should show `✓ revit`).
- Rebuild from source: `install.ps1 -Build` (needs .NET SDK 10; uses your installed Revit DLLs, or the Nice3point reference packages if that Revit isn't installed).
- Remove: `install.ps1 -Uninstall`.

| Revit | .NET |
|---|---|
| 2020 | Framework 4.7 |
| 2021–2024 | Framework 4.8 |
| 2025–2026 | .NET 8 |
| 2027 | .NET 10 |

## Commands (POST /command)
| command | args | notes |
|---|---|---|
| `get_model_info` | — | title, file, version, levels (m), grids, phases, base/survey points (m, °), links |
| `list_elements` | `category` (display name or `OST_…`), `limit`, `parameter_filter` {name: value} | instances only |
| `get_element_parameters` | `element_ids` (ElementId or UniqueId), `parameter_names?` | instance + type params, display & raw values |
| `list_warnings` | `limit` | grouped by description, with element ids |
| `audit_model` | — | worksets, in-place families, imported CAD, link path types, views not on sheets, groups, design options, size |
| `list_views_and_sheets` | `kind` all/views/sheets | |
| `get_selection` | — | |
| `show_elements` | `element_ids`, `isolate?` | select + zoom (+ temporary isolate) — no model change |
| `export_ifc` | `output_folder`, `file_name?`, `ifc_version?` (IFC2x3CV2, IFC4RV, IFC4…), `view_id?` | runs in a rolled-back transaction |
| `export_nwc` | `output_folder`, `file_name?`, `view_name?` (3D view) | needs the Navisworks Exporter for Revit; shared coordinates, properties on, links off |
| `set_parameters` | `element_ids`, `values` {name: value}, `transaction` | **all-or-nothing**, instance params only; string → display units ("2400 mm"), number → internal units |

`GET /health` → `{ok, app, version, addin_version, document, port}` — `document` is the active file name; the MCP layer reads the ISO 19650 role field from it to decide which discipline agent may write.

## Settings (environment variables, optional)
- `BIMHUB_REVIT_PORT` (default 8766)
- `BIMHUB_REVIT_TIMEOUT_S` (default 120) — how long a request waits for Revit to become idle.

Log: `%APPDATA%\BIMHub\revit-bridge.log`.

## Adding a command
1. Add a `case` + method in `src/Commands.cs` (API thread, use `Compat` for version differences, return plain objects).
2. Add the matching tool in `mcp-layer/src/bimhub/servers/revit.py` (`app.call("<command>", …)`), with a guard if it writes.
3. `install.ps1 -Build`.
