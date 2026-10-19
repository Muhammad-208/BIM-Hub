"""Entry point frozen by PyInstaller into bimhub-studio.exe (the Tauri sidecar).

Finds the BIM Hub folder (env BIMHUB_ROOT → Settings 'hub_root' → E:/Ai/BIM Hub) and serves the API on 127.0.0.1.
The MCP servers themselves are NOT inside this exe: Claude Code starts them from the hub's own Python venv
(projects/<CODE>/.mcp.json), exactly as when you use Claude Code in a terminal.
"""
import argparse
import os
import sys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8800)
    a = ap.parse_args()

    from bimhub.studio.settings import StudioSettings
    s = StudioSettings.load()
    root = os.environ.get("BIMHUB_ROOT") or s.hub_root or "E:/Ai/BIM Hub"
    os.environ["BIMHUB_ROOT"] = root
    if not os.path.isdir(os.path.join(root, "learning-hub")):
        print(f"BIM Hub folder not found at {root}. Set it in Studio Settings or BIMHUB_ROOT.", file=sys.stderr)

    from bimhub.studio.server import run
    run(a.port, open_browser=False)


if __name__ == "__main__":
    main()
