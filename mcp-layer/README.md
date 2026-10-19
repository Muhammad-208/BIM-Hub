# MCP Layer (`bimhub` Python package)

One shared layer that gives every agent the tools it needs. Python 3.10+, MCP Python SDK 1.x or 2.x.

```
mcp-layer/
├── config/
│   ├── servers.yaml          ← REGISTRY of every MCP the agents may use (native or external)
│   ├── hub.yaml              ← library folders + catalog tag rules
│   └── bridges/<app>.yaml    ← optional per-tool HTTP route mapping to an existing add-in
├── src/bimhub/
│   ├── core/                 ← paths, config, project, guard (scopes), bridge (HTTP to add-ins), server factory
│   ├── state/store.py        ← issues · decisions · messages (append-only JSONL) · model status (YAML)
│   ├── knowledge/            ← hub search, ISO 19650 naming validator
│   ├── servers/              ← hub.py · revit.py · navisworks.py · civil3d.py · _bridged.py (base)
│   └── cli/main.py           ← `bimhub` command
├── tests/                    ← unit + end-to-end (real stdio MCP against a fake add-in)
└── BRIDGE_PROTOCOL.md        ← what a desktop add-in must implement
```

## Layers inside the layer
```
Agent (Claude Code subagent)
   │  MCP stdio  (agent passes its name in `agent`)
   ▼
servers/<app>.py      typed tools, docstrings = what the agent sees
   │  guard.py         hierarchy & discipline write-scope (from project.yaml)
   ▼
core/bridge.py        HTTP + retries + clear "app not running" errors
   │
   ▼
Desktop add-in (C#)   Revit / Navisworks / Civil 3D / …   ← BRIDGE_PROTOCOL.md
```

## Install (Windows, once)
```powershell
cd "E:\Ai\BIM Hub\mcp-layer"
uv venv ; .venv\Scripts\activate ; uv pip install -e ".[ingest,dev]"
pytest                      # 8 tests, incl. real MCP over stdio
bimhub doctor
```
`bimhub sync` writes each project's `.mcp.json` with the **current** Python (`sys.executable`), so run it from the activated venv.

## Add a new MCP
**A. Wrap a desktop app (native)** — e.g. Tekla, ArchiCAD, Dynamo, ACC:
1. `src/bimhub/servers/tekla.py`:
   ```python
   from ..core.guard import require_discipline_write
   from ..core.server import tool_errors
   from ._bridged import BridgedApp
   app = BridgedApp("tekla", "Tekla Structures", instructions="…")
   mcp = app.mcp

   @mcp.tool()
   @tool_errors
   def list_assemblies(phase: int | None = None):
       """Docstring = the description the agent reads. Be specific."""
       return app.call("list_assemblies", phase=phase)

   def main(): mcp.run()
   if __name__ == "__main__": main()
   ```
2. Register in `config/servers.yaml` (kind native, module, bridge url).
3. Add it to a project's `mcp: [...]`, run `bimhub sync`.

**B. Pure Python service** (no desktop app — e.g. IFC checks with ifcopenshell, COBie validator, GIS): same as A but use `make_server()` from `core/server.py` instead of `BridgedApp`.

**C. Existing / third-party MCP** (your current navisworks-2026, sd-agent, a node server…): add it to `servers.yaml` as `kind: external` with `command` + `args`. No code.

## What is wired today
| Server | Talks to | Status |
|---|---|---|
| `bimhub` | Learning Hub + `projects/<CODE>/05-state` | ✅ works now |
| `navisworks` | your MCPBridge add-in `E:\MCP\Navisworks_MCP\addin` (localhost:8765, 35 routes, mapped in `config/bridges/navisworks.yaml`) | ✅ adapter + team permissions (clash/sets/viewpoints = L3+) |
| `sd-agent` | `E:\MCP\Revit\MCP\server.py` (external, file bridge `C:\ProgramData\SDAgent`) | ✅ registered as-is |
| `navisworks-legacy` | `E:\MCP\Navisworks_MCP\addin\server_http.py` (external, no permissions) | fallback |
| `revit` | BIM Hub Revit add-in `addins/revit` (Revit 2020–2027, localhost:8766) | ✅ install with `addins\\revit\\install.ps1` |
| `civil3d` | a Civil 3D add-in implementing BRIDGE_PROTOCOL.md | ⏳ add-in not built yet |

Navisworks note: after opening Navisworks click **Add-Ins → MCP Bridge** once (the add-in needs it to capture the UI thread).
Don't enable `navisworks` and `navisworks-legacy` in the same project — same add-in, duplicate tools.

## Rules for writing tools
- Read tools: no `agent` arg. Write tools: first arg `agent`, then call a guard (`require_discipline_write`, `require_layer`).
- Return JSON-serialisable data; raise `BimHubError` subclasses for expected failures (the agent sees a clean message).
- Never print to stdout (it is the MCP channel) — use `core.log.get_logger`.
- One tool = one clear job, named verb_noun, docstring says when to use it.
