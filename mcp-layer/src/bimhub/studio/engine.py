"""One engine for both modes: the official Claude Code CLI in headless mode.

  claude -p --agent <name> --output-format stream-json --verbose --forward-subagent-text   (prompt on stdin)
         [--resume <session>] [--model m] --permission-mode dontAsk --allowedTools …
  cwd = projects/<CODE>   → loads that project's .claude/agents, skills, .mcp.json and CLAUDE.md

subscription mode: Claude Code uses the login the user made with `claude auth login` (their plan).
api_key mode:      ANTHROPIC_API_KEY is set for the child process (pay-per-use, required for products).
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator

from ..core.errors import BimHubError
from .settings import StudioSettings


def find_claude(settings: StudioSettings) -> str:
    exe = settings.claude_path or shutil.which("claude") or shutil.which("claude.exe") or shutil.which("claude.cmd")
    if not exe:
        home = Path.home()
        for cand in (home / ".local" / "bin" / "claude.exe", home / ".local" / "bin" / "claude"):
            if cand.exists():
                return str(cand)
        raise BimHubError("Claude Code CLI not found. Install it, run `claude auth login`, or set its path in Settings.")
    return exe


def auth_status(settings: StudioSettings) -> dict:
    try:
        exe = find_claude(settings)
    except BimHubError as e:
        return {"installed": False, "error": str(e)}
    try:
        out = subprocess.run([exe, "auth", "status"], capture_output=True, text=True, timeout=20)
        data = json.loads(out.stdout or "{}") if out.stdout.strip().startswith("{") else {"raw": out.stdout.strip()}
    except Exception as e:  # noqa: BLE001
        data = {"error": str(e)}
    try:
        ver = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        ver = None
    return {"installed": True, "path": exe, "version": ver, **data,
            "mode": settings.auth_mode, "api_key_set": bool(settings.get_api_key())}


@dataclass
class RunEvent:
    kind: str                 # start | text | tool | tool_result | subagent | done | error
    agent: str
    data: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"kind": self.kind, "agent": self.agent, **self.data}


class ClaudeCodeEngine:
    def __init__(self, settings: StudioSettings):
        self.s = settings

    def command(self, agent: str, session: str | None, new_session: bool) -> list[str]:
        # The prompt goes to stdin, never on the command line: on Windows `claude.cmd` runs through cmd.exe,
        # which cuts arguments at newlines and mangles & | < > characters.
        cmd = [find_claude(self.s), "-p", "--agent", agent, "--output-format", "stream-json", "--verbose",
               "--forward-subagent-text", "--permission-mode", self.s.permission_mode]
        if self.s.allowed_tools:
            cmd += ["--allowedTools", *self.s.allowed_tools]
        if session:
            cmd += (["--session-id", session] if new_session else ["--resume", session])
        if self.s.model:
            cmd += ["--model", self.s.model]
        if self.s.auth_mode == "api_key" and self.s.max_budget_usd > 0:
            cmd += ["--max-budget-usd", str(self.s.max_budget_usd)]
        return cmd

    def env(self) -> dict:
        env = dict(os.environ)
        env.pop("ANTHROPIC_API_KEY", None)
        if self.s.auth_mode == "api_key":
            key = self.s.get_api_key()
            if not key:
                raise BimHubError("API-key mode selected but no key is set (Settings → API key).")
            env["ANTHROPIC_API_KEY"] = key
        return env

    async def run(self, project_dir: Path, agent: str, prompt: str, session: str | None,
                  new_session: bool) -> AsyncIterator[RunEvent]:
        """Runs claude in a worker thread (plain subprocess.Popen) so it works on every asyncio loop,
        including the Windows selector loop that cannot spawn async subprocesses."""
        yield RunEvent("start", agent, {"session": session, "mode": self.s.auth_mode})
        try:
            cmd, env = self.command(agent, session, new_session), self.env()
        except BimHubError as e:
            yield RunEvent("error", agent, {"error": str(e)})
            return
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        END = object()
        result: dict = {}

        def worker() -> None:
            try:
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
                proc = subprocess.Popen(cmd, cwd=str(project_dir), env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
                assert proc.stdin and proc.stdout and proc.stderr
                proc.stdin.write(prompt.encode("utf-8"))
                proc.stdin.close()
                err_chunks: list[bytes] = []
                t = threading.Thread(target=lambda: err_chunks.append(proc.stderr.read()), daemon=True)
                t.start()
                for raw in proc.stdout:
                    loop.call_soon_threadsafe(q.put_nowait, raw)
                result["code"] = proc.wait()
                t.join(timeout=5)
                result["err"] = b"".join(err_chunks).decode("utf-8", "replace")
            except OSError as e:
                result["code"], result["err"] = -1, f"could not start Claude Code: {e}"
            finally:
                loop.call_soon_threadsafe(q.put_nowait, END)

        threading.Thread(target=worker, daemon=True).start()
        while True:
            raw = await q.get()
            if raw is END:
                break
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("{"):
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            for ev in self.parse(agent, msg):
                yield ev
        if result.get("code", 0) != 0:
            yield RunEvent("error", agent, {"error": (result.get("err", "").strip()
                                                       or f"claude exited with {result.get('code')}")[-1500:]})

    @staticmethod
    def parse(agent: str, msg: dict) -> list[RunEvent]:
        t = msg.get("type")
        sub = msg.get("parent_tool_use_id")
        who = agent if not sub else f"{agent}›sub"
        out: list[RunEvent] = []
        if t == "system" and msg.get("subtype") == "init":
            out.append(RunEvent("session", agent, {"session": msg.get("session_id"), "model": msg.get("model"),
                                                   "mcp": [s.get("name") + ":" + s.get("status", "")
                                                           for s in msg.get("mcp_servers") or []]}))
        elif t == "assistant":
            for b in (msg.get("message") or {}).get("content") or []:
                if b.get("type") == "text" and b.get("text", "").strip():
                    out.append(RunEvent("text", who, {"text": b["text"], "subagent": bool(sub)}))
                elif b.get("type") == "tool_use":
                    name = b.get("name", "")
                    target = (b.get("input") or {}).get("subagent_type") or (b.get("input") or {}).get("to")
                    out.append(RunEvent("tool", who, {"tool": name, "id": b.get("id"), "target": target,
                                                      "input": _short(b.get("input"))}))
        elif t == "user":
            for b in (msg.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    out.append(RunEvent("tool_result", who, {"id": b.get("tool_use_id"), "is_error": bool(b.get("is_error")),
                                                             "content": _short(b.get("content"), 600)}))
        elif t == "result":
            out.append(RunEvent("done", agent, {"result": msg.get("result"), "cost_usd": msg.get("total_cost_usd"),
                                                "turns": msg.get("num_turns"), "duration_ms": msg.get("duration_ms"),
                                                "is_error": bool(msg.get("is_error")), "session": msg.get("session_id"),
                                                "usage": msg.get("usage")}))
        return out


def _short(v, n: int = 300):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + "…"


def new_session_id() -> str:
    return str(uuid.uuid4())
