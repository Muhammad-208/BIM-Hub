# BIM Hub Studio — UI + desktop shell

```
studio-ui/
├── src/                 React + three.js UI (Projects · Studio 3D · Settings)
├── src-tauri/           Tauri 2 desktop shell (starts the backend sidecar, shows the UI)
├── desktop/             studio_entry.py (frozen by PyInstaller → bimhub-studio.exe), app-icon.png
├── build-desktop.ps1    one-shot build → NSIS .exe + .msi installers
└── vite.config.js
```

## How it fits
```
BIM Hub Studio.exe ──► bimhub-studio.exe (FastAPI, 127.0.0.1:8800)
                          ├─ chat → Claude Code headless:  claude -p … --agent mech-clash --resume <session>
                          │         cwd = projects/<CODE>  (its .claude/agents, skills, .mcp.json, CLAUDE.md)
                          │         auth = your Claude subscription  OR  ANTHROPIC_API_KEY (Settings)
                          └─ live events (SSE): run stream + 05-state/activity.jsonl from ANY Claude Code session
```
The MCP servers are not bundled: Claude Code starts them from the hub's venv (`projects/<CODE>/.mcp.json`).
So the hub must be installed (`install.ps1`) on the PC that runs the app.

## Run without building (fastest)
```powershell
cd "E:\Ai\BIM Hub" ; .\bimhub.cmd studio
```

## Develop the UI
```powershell
cd "E:\Ai\BIM Hub\studio-ui" ; npm install ; npm run dev     # :5173, API proxied to :8800 (run bimhub studio too)
```

## Build the installer
Prereqs once: Node.js 20+, Rust (rustup, MSVC), WebView2 (built into Windows 11).
```powershell
powershell -ExecutionPolicy Bypass -File "E:\Ai\BIM Hub\studio-ui\build-desktop.ps1"
```
Output: `src-tauri\target\release\bundle\nsis\BIM Hub Studio_0.1.0_x64-setup.exe` (+ `.msi`).
Unsigned → SmartScreen warns on first run; sign with a code-signing certificate for distribution.

## Modes and Anthropic terms
- **Claude subscription**: the app drives *your* installed Claude Code with *your* login. Use it for yourself.
- **API key**: required if the app is given to other people or sold (Anthropic does not allow third-party products
  to offer claude.ai login without approval — see Agent SDK overview docs).
