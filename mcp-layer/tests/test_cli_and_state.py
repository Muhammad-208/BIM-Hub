import json

import pytest

from bimhub.core.errors import BimHubError, ScopeError
from bimhub.core.guard import require_discipline_write
from bimhub.core.paths import HubPaths
from bimhub.core.project import Project
from bimhub.knowledge.naming import validate_name
from bimhub.knowledge.search import search
from bimhub.state.store import StateStore


def test_new_project_generates_team(hub):
    p = hub / "projects" / "TST"
    agents = sorted(f.stem for f in (p / ".claude" / "agents").glob("*.md"))
    roles = ["leader", "modeler", "drafter", "clash", "info"]
    assert agents == sorted(["bim-manager", "bim-coordinator", "qa-model", "qa-data", "qa-doc"] +
                            [f"{d}-{r}" for d in ("arc", "str", "mech") for r in roles])
    txt = (p / ".claude" / "agents" / "str-clash.md").read_text(encoding="utf-8")
    assert "{{" not in txt and "name: str-clash" in txt and "ECP 203" in txt and "`str-leader`" in txt
    assert (p / ".claude" / "skills" / "clash-workflow" / "SKILL.md").exists()
    cfg = json.loads((p / ".mcp.json").read_text())
    assert cfg["mcpServers"]["bimhub"]["env"]["BIMHUB_PROJECT"] == "TST"
    assert (p / "02-cde" / "WIP" / "STR").is_dir()


def test_naming(hub):
    proj = Project.load(HubPaths.discover())
    ok = validate_name("TST-WYA-ZZ-03-DR-A-0101.pdf", proj.naming, proj.code)
    bad = validate_name("TST-WYA-ZZ-03-XX-A-01", proj.naming, proj.code)
    assert ok["valid"], ok
    assert not bad["valid"] and len(bad["errors"]) == 2


def test_issue_lifecycle_and_messages(hub):
    s = StateStore(hub / "projects" / "TST" / "05-state")
    i = s.issue_create("bim-coordinator", "Duct hits beam B12", owner="mech-clash", priority="high", elements=["abc"])
    assert i["id"] == "ISS-0001" and i["status"] == "open"
    s.issue_update("mech-clash", "ISS-0001", status="resolved", comment="lowered duct 150mm")
    assert s.issue_get("ISS-0001")["status"] == "resolved"
    assert len(s.issue_list(owner="mech-clash")) == 1
    m = s.message_send("bim-manager", "str-leader", "Review beams L3", None, "medium", None)
    assert [x["id"] for x in s.message_inbox("str-leader")] == [m["id"]]
    s.message_ack("str-leader", m["id"], "done")
    assert s.message_inbox("str-leader") == []


def test_guard(hub):
    proj = Project.load(HubPaths.discover())
    for ok in ("str-modeler", "str-clash", "str-info"):
        require_discipline_write(proj, ok, "str")
    for bad, disc in (("mech-modeler", "str"), ("bim-coordinator", "str"), ("str-leader", "str"),
                      ("str-drafter", "str"), ("land-modeler", "land")):
        with pytest.raises(ScopeError):
            require_discipline_write(proj, bad, disc)
    assert proj.normalize("mech") == "mech-leader"


def test_hub_search(hub):
    hits = search(hub / "learning-hub", "clash grouping navisworks")
    assert hits and hits[0].path.startswith("skills/clash-workflow")


def test_hub_server_rules(hub):
    from bimhub.servers import hub as srv
    srv.ctx._project = None
    srv.ctx.paths = HubPaths.discover()
    r = srv.model_status_set("str-leader", "TST-WYA-ZZ-ZZ-M3-S-0001", state="SHARED")
    assert r["ok"] is False                      # L1 cannot promote
    srv.model_status_set("qa-model", "TST-WYA-ZZ-ZZ-M3-S-0001", qa_model="PASS")
    srv.model_status_set("qa-data", "TST-WYA-ZZ-ZZ-M3-S-0001", qa_data="PASS")
    r = srv.model_status_set("qa-doc", "TST-WYA-ZZ-ZZ-M3-S-0001", qa_doc="PASS", state="SHARED")
    assert r["TST-WYA-ZZ-ZZ-M3-S-0001"]["state"] == "SHARED"
    assert srv.model_status_set("bim-coordinator", "TST-WYA-ZZ-ZZ-M3-S-0001", state="PUBLISHED")["ok"] is False
    lid = srv.lesson_propose("mech-clash", "Route ducts below beams after drainage", "hospital floors", "x", "y", "ISS-1")["id"]
    assert srv.lesson_approve("mech-leader", lid)["ok"] is False
    assert srv.lesson_approve("bim-manager", lid)["hub_path"].startswith("lessons/")
    assert (hub / "learning-hub" / "lessons" / f"{lid}.md").exists()
