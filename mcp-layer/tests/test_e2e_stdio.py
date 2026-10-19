"""End-to-end: launch the real MCP servers over stdio (as Claude Code does) against a fake desktop add-in."""
import asyncio
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

mcp = pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

CALLS = []


class FakeRevit(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send({"ok": True, "app": "Revit", "version": "2027", "document": "TST-WYA-ZZ-ZZ-M3-S-0001.rvt"})

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append(req)
        self._send({"ok": True, "result": {"echo": req}})


@pytest.fixture()
def fake_revit(hub):
    srv = HTTPServer(("127.0.0.1", 0), FakeRevit)
    port = srv.server_address[1]
    cfg = hub / "mcp-layer" / "config" / "servers.yaml"
    cfg.write_text(cfg.read_text().replace("http://localhost:8766", f"http://127.0.0.1:{port}"))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield port
    srv.shutdown()


def _text(result):
    return json.loads(result.content[0].text)


async def _session(module, hub):
    env = {**os.environ, "BIMHUB_ROOT": str(hub), "BIMHUB_PROJECT": "TST"}
    return StdioServerParameters(command=sys.executable, args=["-m", module], env=env)


def test_hub_over_stdio(hub):
    async def run():
        async with stdio_client(await _session("bimhub.servers.hub", hub)) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                assert {"hub_search", "issue_create", "lesson_propose", "naming_validate"} <= names
                res = _text(await s.call_tool("issue_create", {"agent": "bim-coordinator", "title": "t", "owner": "mech"}))
                assert res["id"] == "ISS-0001"
    asyncio.run(run())


def test_revit_guard_over_stdio(hub, fake_revit):
    async def run():
        async with stdio_client(await _session("bimhub.servers.revit", hub)) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                ok = _text(await s.call_tool("set_parameters", {"agent": "str-modeler", "element_ids": ["1"],
                                                               "values": {"Mark": "B1"}, "reason": "renumber"}))
                assert ok["echo"]["command"] == "set_parameters"
                denied = _text(await s.call_tool("set_parameters", {"agent": "mech-modeler", "element_ids": ["1"],
                                                                   "values": {"Mark": "X"}, "reason": "oops"}))
                assert denied["ok"] is False and "may not modify the STR model" in denied["error"]
    asyncio.run(run())


# ---------------- Navisworks: real route map of the MCPBridge add-in ----------------
NAVIS_CALLS = []


class FakeNavis(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, {"ok": True, "version": "2.0.0", "port": 8765, "routes": 35})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        NAVIS_CALLS.append((self.path, body))
        if self.path == "/clash/results" and body.get("name") == "missing":
            return self._send(500, {"error": "InvalidOperationException", "detail": "clash test 'missing' not found"})
        if self.path == "/clash/group/list":
            return self._send(200, {"test_name": body["test_name"], "count": 0, "groups": []})
        self._send(200, {"path": self.path, "body": body})


@pytest.fixture()
def fake_navis(hub):
    srv = HTTPServer(("127.0.0.1", 0), FakeNavis)
    port = srv.server_address[1]
    cfg = hub / "mcp-layer" / "config" / "servers.yaml"
    cfg.write_text(cfg.read_text().replace("http://localhost:8765", f"http://127.0.0.1:{port}"))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield port
    srv.shutdown()


def test_navisworks_routes_and_permissions(hub, fake_navis):
    async def run():
        async with stdio_client(await _session("bimhub.servers.navisworks", hub)) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                res = _text(await s.call_tool("get_clash_results", {"test_name": "STR-MECH", "max_results": 5}))
                assert res == {"path": "/clash/results", "body": {"name": "STR-MECH", "limit": 5}}
                err = _text(await s.call_tool("get_clash_results", {"test_name": "missing"}))
                assert err["ok"] is False and "not found" in err["error"]
                denied = _text(await s.call_tool("run_clash_test", {"agent": "mech-clash"}))
                assert denied["ok"] is False
                grp = _text(await s.call_tool("group_clashes", {"agent": "bim-coordinator", "test_name": "T",
                                                                "group_name": "L03-Duct-B12",
                                                                "clash_names": ["Clash1", "Clash2"]}))
                assert grp["moved"]["path"] == "/clash/group/add-clashes"
                paths = [p for p, _ in NAVIS_CALLS]
                assert "/clash/group/create" in paths
    asyncio.run(run())
