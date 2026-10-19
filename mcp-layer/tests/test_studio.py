"""Studio backend against a fake `claude` CLI that speaks stream-json."""
import json
import os
import stat
import sys
import time

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

FAKE = r'''import json, sys, os
args = sys.argv[1:]
if args[:2] == ["auth", "status"]:
    print(json.dumps({{"loggedIn": True, "authMethod": "api_key" if os.environ.get("ANTHROPIC_API_KEY") else "claude.ai"}})); sys.exit(0)
if args[:1] == ["--version"]:
    print("2.1.300 (Claude Code)"); sys.exit(0)
prompt = sys.stdin.buffer.read().decode("utf-8")
open(os.environ["FAKE_LOG"], "a", encoding="utf-8").write(json.dumps({{"args": args, "cwd": os.getcwd(), "key": os.environ.get("ANTHROPIC_API_KEY"), "prompt": prompt}}, ensure_ascii=False) + "\n")
agent = args[args.index("--agent") + 1]
sid = args[args.index("--session-id") + 1] if "--session-id" in args else args[args.index("--resume") + 1]
out = [
  {{"type": "system", "subtype": "init", "session_id": sid, "model": "claude-x", "mcp_servers": [{{"name": "bimhub", "status": "connected"}}]}},
  {{"type": "assistant", "message": {{"content": [{{"type": "text", "text": "هشوف الـ issues"}}, {{"type": "tool_use", "id": "t1", "name": "mcp__bimhub__issue_list", "input": {{"owner": agent}}}}]}}}},
  {{"type": "user", "message": {{"content": [{{"type": "tool_result", "tool_use_id": "t1", "content": "[]"}}]}}}},
  {{"type": "result", "subtype": "success", "result": "مفيش issues مفتوحة.", "session_id": sid, "total_cost_usd": 0.01, "num_turns": 2, "is_error": False}},
]
for o in out: sys.stdout.buffer.write((json.dumps(o, ensure_ascii=False) + "\n").encode("utf-8")); sys.stdout.flush()
'''


@pytest.fixture()
def studio(hub, tmp_path, monkeypatch):
    script = tmp_path / "fake_claude.py"
    script.write_text(FAKE.format(), encoding="utf-8")
    if os.name == "nt":      # like an npm-installed claude.cmd
        fake = tmp_path / "claude.cmd"
        fake.write_text(f'@"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    else:
        fake = tmp_path / "claude"
        fake.write_text(f"#!/bin/sh\nexec '{sys.executable}' '{script}' \"$@\"\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("BIMHUB_STUDIO_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.jsonl"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from bimhub.studio.settings import StudioSettings
    s = StudioSettings.load(); s.claude_path = str(fake); s._api_key_inline = ""; s.save()
    from bimhub.core.paths import HubPaths
    from bimhub.studio.server import create_app
    with TestClient(create_app(HubPaths.discover())) as client:
        yield client, tmp_path


def _wait_chat(client, n, timeout=10):
    t = time.time()
    while time.time() - t < timeout:
        chat = client.get("/api/projects/TST/state").json()["chat"]
        if len(chat) >= n:
            return chat
        time.sleep(0.1)
    raise AssertionError("chat did not finish")


def test_projects_and_state(studio):
    c, _ = studio
    assert c.get("/api/health").json()["ok"]
    ps = c.get("/api/projects").json()
    assert ps[0]["code"] == "TST" and ps[0]["agents"] == 20
    d = c.get("/api/projects/TST").json()
    assert any(a["id"] == "mech-clash" and a["role"] == "clash" for a in d["agents"])
    a = c.get("/api/auth").json()
    assert a["installed"] and a["authMethod"] == "claude.ai" and a["mode"] == "subscription"


def test_chat_subscription_then_resume(studio):
    c, tmp = studio
    r = c.post("/api/projects/TST/chat", json={"agent": "mech", "text": "إيه الـ issues بتاعتي؟"}).json()
    assert r["agent"] == "mech-leader" and r["mode"] == "subscription"
    chat = _wait_chat(c, 2)
    assert chat[-1]["from"] == "mech-leader" and "مفيش" in chat[-1]["text"]
    c.post("/api/projects/TST/chat", json={"agent": "mech-leader", "text": "تاني"})
    _wait_chat(c, 4)
    calls = [json.loads(l) for l in (tmp / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    first, second = calls[0]["args"], calls[1]["args"]
    assert "--session-id" in first and "--resume" in second
    assert first[first.index("--session-id") + 1] == second[second.index("--resume") + 1]
    assert calls[0]["cwd"].endswith("TST") and calls[0]["key"] is None
    assert "--permission-mode" in first and "mcp__bimhub" in first
    assert "-p" in first and not any("إيه" in x for x in first)     # prompt is NOT on the command line
    prompt = calls[0]["prompt"]
    assert "`mech-leader`" in prompt and "Egyptian Arabic" in prompt and prompt.endswith("إيه الـ issues بتاعتي؟")


def test_api_key_mode(studio):
    c, tmp = studio
    assert c.put("/api/settings", json={"auth_mode": "api_key"}).json()["auth_mode"] == "api_key"
    c.put("/api/settings/api-key", json={"key": "sk-ant-test"})
    c.post("/api/projects/TST/chat", json={"agent": "bim-manager", "text": "hi"})
    _wait_chat(c, 2)
    calls = [json.loads(l) for l in (tmp / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert calls[-1]["key"] == "sk-ant-test"
    assert c.get("/api/settings").json()["api_key_set"] is True


def test_engine_parse():
    from bimhub.studio.engine import ClaudeCodeEngine
    ev = ClaudeCodeEngine.parse("bim-manager", {"type": "assistant", "parent_tool_use_id": "x",
        "message": {"content": [{"type": "tool_use", "id": "1", "name": "Task", "input": {"subagent_type": "mech-clash"}}]}})
    assert ev[0].kind == "tool" and ev[0].data["target"] == "mech-clash" and ev[0].agent.endswith("›sub")
