# BIM Hub — Developer handoff (for Claude Code)

This file is for **developing** BIM Hub. Open Claude Code in the hub root (`E:\Ai\BIM Hub`) and say:

> Read DEVELOPMENT.md and continue the roadmap.

Note: the root `CLAUDE.md` holds the rules for the **BIM agents** inside projects. Don't put developer notes there, because every project agent inherits it.

---

## 1. What this is
BIM Hub is a hierarchical multi-agent BIM department built on Claude Code. It follows ISO 19650 roles and the CDE workflow.

**Layers:**
- **L4** `bim-manager`
- **L3** `bim-coordinator`
- **L2** `qa-model`, `qa-data`, `qa-doc`
- **L1** a 5-role sub-team for every discipline on the project: `<disc>-leader`, `-modeler`, `-drafter`, `-clash`, `-info`
- **L0** shared by all projects: the Learning Hub and the MCP layer

**Projects:**
- Each project lives in `projects/<CODE>/` and has its own generated team in `.claude/agents`.
- `bimhub sync` regenerates a project's agents from the templates in `agents/`.

**Owner:** Eng. Mohamed Osama, Head of BIM/GIS. He writes in Egyptian Arabic; reply in Arabic and keep technical terms in English.

## 2. Map of the code
| Path | What |
|---|---|
| `agents/` | Core agent templates (L2–L4); `L1-disciplines/disciplines.yaml` profiles; `L1-disciplines/roles/*.md` role templates (`{{DISC}} {{DISC_UPPER}} {{DISC_TITLE}} {{ROLE_CODE}} {{SUBTEAM}} {{PROFILE}} {{CODE}} {{NAME}}`) |
| `learning-hub/knowledge/00-standards/` | Distilled standards: ISO 19650-1/2, CDE status/revision, naming, LOIN, LOD 2021, LOD 400, COBie, USIBD LOA |
| `learning-hub/skills/` | Skills copied into every project on sync. 13 in total, including cad-to-bim, model-review-report, lod-uplift and scan-to-bim |
| `learning-hub/project-types/*.yaml` | Project types with stages (owner/support/gate/per_discipline/optional/outputs/done_when), roles, mcp, skills, folders, params, role_notes, deliverables, kpis |
| `mcp-layer/src/bimhub/core/` | `paths`, `config`, `project` (team model, `ROLES`, `split_agent`, `type_id`, `params`), `guard` (permission checks), `bridge` (HTTP to the desktop add-ins), `server` (`make_server`, `tool_errors` → logs every call to `05-state/activity.jsonl`), `project_types` (load types, `workflow_view`, `check_stage_update`, `render_workflow_md`) |
| `mcp-layer/src/bimhub/state/store.py` | `StateStore` (issues as an event JSONL, decisions, messages, model-status.yaml) and `ExtraState` (zones, health, dashboards, workflow.yaml) |
| `mcp-layer/src/bimhub/servers/` | `hub.py` (32 tools), `revit.py` (11), `navisworks.py` (26, adapter to the MCPBridge add-in via `config/bridges/navisworks.yaml`), `civil3d.py` (10), `_bridged.py` |
| `mcp-layer/src/bimhub/files/` | `readers.py`: IFC/DOCX/XLSX/PDF/PPTX/TXT are read fully; RVT, NWC/NWD/NWF, DWG and point clouds (E57/LAS/RCP/PTS) return metadata from their headers. `sources.py`: local, acc-dc and acc-web sources, scan → `05-state/file-index.json` |
| `mcp-layer/src/bimhub/cli/main.py` | Commands: `new-project [--type]`, `types`, `sync`, `list`, `catalog`, `ingest`, `doctor`, `source`, `scan`, `studio` |
| `mcp-layer/src/bimhub/studio/` | FastAPI backend: `server.py` (`/api/*` endpoints plus SSE), `engine.py`, `sessions.py` (per-agent session ids), `settings.py` (API key in keyring), `prompting.py`, `ui/` (built React app) |
| `mcp-layer/config/servers.yaml` | MCP registry: native servers bimhub/revit (8766)/navisworks (8765)/civil3d (8767); external sd-agent and navisworks-legacy from `E:/MCP` |
| `addins/revit/` | One C# project multi-targeted to Revit 2020–2027 (net47 / net48 / net8.0-windows / net10.0-windows) using Nice3point.Revit.Api packages. `HttpListener` on :8766, `ExternalEvent` dispatcher, `Compat.IdValue` for ElementId |
| `studio-ui/` | React 18 + three.js (Vite): `pages/Projects.jsx`, `Studio.jsx`, `Settings.jsx`; `components/Team3D.jsx`. Tauri 2 shell in `src-tauri` with a PyInstaller sidecar `bimhub-studio` on :8800. `build-desktop.ps1` makes the NSIS/MSI installer |
| `projects/_template/` | Skeleton for new projects (placeholders `{{CODE}} {{NAME}} {{TEAM}} {{TYPE}} {{TYPE_TITLE}} {{ROLES}} {{MCP}} {{PARAMS}}`) |

### The Studio engine
- The engine runs Claude Code headless: `claude -p --agent <name> --output-format stream-json --verbose --forward-subagent-text --permission-mode <mode> --allowedTools …`.
- Sessions use `--session-id` for a new chat and `--resume` to continue one.
- The **prompt goes on stdin**, never in the argument list. `claude.cmd` runs through cmd.exe on Windows, and cmd.exe cuts arguments at newlines.
- The process is started with `subprocess.Popen` in a worker thread, so it works on any asyncio loop on Windows.
- **Auth modes:**
  - Subscription: uses the user's own `claude auth login`. For personal use only.
  - API key: sets the `ANTHROPIC_API_KEY` env var. Required for team, product or unattended use.

## 3. Rules that must stay true
- **Permissions are enforced in the MCP servers** (`core/guard.py`, `project_types.check_stage_update`), not in prompts. Every write tool takes an `agent` argument.
  - Model writes are allowed only for the modeler, clash and info roles of the model's own discipline.
  - NWC export is allowed only for the clash and modeler roles.
  - Setting zones, publishing dashboards and marking a stage done need L3 or above.
  - qa-pass and qa-fail can only be set by the stage's gate agent.
  - Drafting is allowed only in zones marked coordinated.
- **Sources are read-only.** Never sign in to, upload to, delete from or modify ACC. Downloads need the user's yes.
- **Never write secrets into project folders.** The API key lives in the keyring under service `BIMHub-Studio`.
- **The GitHub repo is public.** These stay out of git, already covered by `.gitignore`:
  - `projects/*` except `_template` (client data, e.g. AOH)
  - `learning-hub/library/catalog.yaml` (paths from the owner's drives)
  - `learning-hub/knowledge/_raw/`
  - binaries and build output
- **Windows first.** Use `encoding="utf-8"` on every read and write. No POSIX-only tricks (shebangs, chmod) in runtime code.
- Standards summaries are distilled in our own words. Never paste copyrighted standard text into the hub.

## 4. Build and test
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1          # venv + deps + tests + doctor + sync
.\mcp-layer\.venv\Scripts\python -m pytest mcp-layer\tests -q   # 24 tests
.\bimhub.cmd doctor ; .\bimhub.cmd types ; .\bimhub.cmd sync
.\bimhub.cmd studio                                             # http://localhost:8800
cd studio-ui ; npm install ; npm run build                      # then copy dist\* → mcp-layer\src\bimhub\studio\ui\
cd addins\revit ; dotnet build -c Release ; .\install.ps1
```

**Tests:**
- The `conftest.py` `hub` fixture copies agents, learning-hub, `_template` and config into a temp dir and creates project `TST` with team arc, str, mech.
- `test_studio.py` uses a fake `claude`: `claude.cmd` on Windows or a sh wrapper elsewhere, running `fake_claude.py`.
- `test_e2e_stdio.py` runs the MCP servers over stdio against fake Revit and Navisworks HTTP servers.

## 5. Current state (2026-10-19)
**Done:**
- The hierarchy, with 5 roles per discipline.
- Learning Hub knowledge and 13 skills.
- The MCP layer with 4 native servers and an external-server registry.
- File sources (local, ACC via Desktop Connector, ACC web) and file readers.
- Zones, the drafting gate, model health and dashboards.
- The Revit add-in, built for 2020–2027.
- The Studio app (subscription and API-key modes, 3D team, Workflow tab).
- Project types with enforced stage gates.
- The README.

**On the owner's PC:**
- Project `AOH` exists but has no `type:` yet. Add one to its `project.yaml`, e.g. `type: cad-to-bim`, then run `bimhub sync`.
- The Revit bridge was not running at the last `doctor`.

## 6. Roadmap (next tasks, in order)
1. **IFC 3D viewer in the Studio:** a "Model 3D" tab using web-ifc or That Open Components, loading IFC files from the project sources through a new `/api/projects/{code}/file?path=` endpoint. The endpoint must stay read-only and source-restricted.
2. **Revit commands for the drafter role:** `create_views`, `create_sheet`, `place_views`, `apply_view_template`, tags. Add them to `addins/revit/src/Commands.cs` and `servers/revit.py`. Guard: role drafter, and `drafting_clearance(zone)` must be ok.
3. **Navisworks shared-parameter coverage:** a route in the Navisworks bridge, plus a `dashboard_publish(kind="shared-parameters")` helper.
4. **Scan-to-BIM deviation helper:** a cloud-to-model deviation report in `04-qa/deviation`, using CloudCompare CLI if installed, or Revit/ReCap exports.
5. **Model-review report builder:** generate the DOCX/HTML review report from issues, health and criteria.xlsx, following the R6 structure in skill `model-review-report`.
6. **More discipline knowledge:** `knowledge/02-disciplines/*` is still empty. Add Egyptian codes, modelling standards and family standards.
7. A LICENSE for the repo (owner to choose).

## 7. Conventions
- Python 3.10+.
- MCP SDK 2.x: `from mcp.server.mcpserver import MCPServer`, with a fallback to `FastMCP`.
- Tools are wrapped with `@tool_errors`, which returns `{"ok": False, "error": …}` instead of raising.
- State is written with `file_lock` and an atomic `os.replace`.
- Agent names: a bare discipline name (`mech`) means `mech-leader` (`Project.normalize`).
- After changing templates, skills or project types, run `bimhub sync`.
- Commit messages end with a Co-Authored-By line.
