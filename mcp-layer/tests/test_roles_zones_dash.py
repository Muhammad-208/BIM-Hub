from bimhub.core.paths import HubPaths


def _srv():
    from bimhub.servers import hub as srv
    srv.ctx._project = None
    srv.ctx.paths = HubPaths.discover()
    return srv


def test_issue_to_discipline_goes_to_leader(hub):
    srv = _srv()
    i = srv.issue_create("bim-coordinator", "Duct vs beam", owner="mech")
    assert i["owner"] == "mech-leader"
    assert srv.issue_list(owner="mech")[0]["id"] == i["id"]


def test_zone_gate(hub):
    srv = _srv()
    assert srv.drafting_clearance("str-drafter", "L03")["ok"] is False          # unknown zone
    assert srv.zone_set("str-drafter", "L03", "coordinated")["ok"] is False     # L1 can't release zones
    srv.zone_set("bim-coordinator", "L03", "in-coordination")
    assert srv.drafting_clearance("str-drafter", "L03")["ok"] is False
    srv.zone_set("bim-coordinator", "L03", "coordinated", note="9 groups → 0 open", disciplines=["str", "arc"])
    assert srv.drafting_clearance("str-drafter", "L03")["ok"] is True
    assert srv.drafting_clearance("mech-drafter", "L03")["ok"] is False         # mech not in this release
    assert srv.drafting_clearance("str-modeler", "L03")["ok"] is False          # not a drafter
    assert any("Zone L03" in d["title"] for d in srv.decision_list())


def test_health_and_dashboard(hub):
    srv = _srv()
    assert srv.health_submit("mech-modeler", "M", 80, [])["ok"] is False
    srv.health_submit("mech-info", "TST-WYA-ZZ-ZZ-M3-M-0001", 87.5,
                      [{"name": "Shared params filled", "status": "fail", "found": "82%", "expected": "100%"}],
                      report="ACC:Reports/ModelChecker.xlsx")
    h = srv.health_latest("mech")
    assert h[0]["score"] == 87.5 and h[0]["failed"] == 1
    assert srv.dashboard_publish("mech-leader", "clashes", {})["ok"] is False
    e = srv.dashboard_publish("bim-coordinator", "Model Health", {
        "title": "Model health", "kpis": [{"label": "Avg score", "value": 87.5, "tone": "warn"}],
        "bars": [{"title": "Score by discipline", "items": [{"label": "MECH", "value": 87.5}]}],
        "tables": [{"title": "Models", "columns": ["Model", "Score"], "rows": [["<script>x</script>", 87.5]]}]})
    page = (hub / "projects" / "TST" / e["path"]).read_text(encoding="utf-8")
    assert e["kind"] == "model-health" and "Avg score" in page and "<script>x" not in page
    assert srv.dashboard_list()["model-health"]["title"] == "Model health"


def test_activity_log(hub):
    import json
    import bimhub.core.server as core
    core._ACTIVITY = None
    srv = _srv()
    srv.issue_list()
    srv.zone_set(agent="mech-modeler", zone="L01", status="coordinated")   # refused → logged with ok=false
    lines = [json.loads(l) for l in (hub / "projects" / "TST" / "05-state" / "activity.jsonl").read_text().splitlines()]
    assert lines[0]["tool"] == "issue_list" and lines[0]["ok"] is True
    assert lines[1]["tool"] == "zone_set" and lines[1]["ok"] is False and lines[1]["agent"] == "mech-modeler"
    core._ACTIVITY = None
