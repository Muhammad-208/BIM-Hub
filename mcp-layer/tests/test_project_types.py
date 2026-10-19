import struct

import yaml

from bimhub.cli.main import main
from bimhub.core import project_types as ptypes
from bimhub.core.paths import HubPaths
from bimhub.core.project import Project


def _srv(code):
    import os
    os.environ["BIMHUB_PROJECT"] = code
    from bimhub.servers import hub as srv
    srv.ctx._project = None
    srv.ctx.paths = HubPaths.discover()
    return srv


def test_types_load_and_render(hub):
    types = ptypes.load_types(HubPaths.discover())
    assert {"cad-to-bim", "model-review", "lod-uplift", "scan-to-bim"} <= set(types)
    for t in types.values():
        assert t["stages"] and t["title"] and t["title_ar"]


def test_new_typed_project(hub):
    assert main(["new-project", "REV", "--name", "Review job", "--team", "arc,mech", "--type", "model-review"]) == 0
    d = hub / "projects" / "REV"
    data = yaml.safe_load((d / "project.yaml").read_text(encoding="utf-8"))
    assert data["type"] == "model-review" and data["roles"] == ["leader", "clash", "info"]
    assert data["params"]["reference_lod"] == 300
    p = Project.load(HubPaths.discover(), "REV")
    assert "arc-modeler" not in p.all_agents and "arc-info" in p.all_agents
    wf = (d / "WORKFLOW.md").read_text(encoding="utf-8")
    assert "R6" in wf and "model-review" in wf
    assert "@WORKFLOW.md" in (d / "CLAUDE.md").read_text(encoding="utf-8")
    assert (d / "06-reports" / "review").is_dir() and (d / ".claude" / "skills" / "model-review-report").is_dir()
    assert main(["new-project", "BAD", "--name", "x", "--team", "arc", "--type", "nope"]) == 1


def test_stage_gates(hub):
    assert main(["new-project", "SCN", "--name", "Scan", "--team", "arc,str", "--type", "scan-to-bim"]) == 0
    srv = _srv("SCN")
    assert srv.stage_update("arc-modeler", "P3", "in-progress")["P3:arc"]["status"] == "in-progress"
    assert srv.stage_update("arc-modeler", "P3", "done")["ok"] is False                 # L1 cannot close
    assert srv.stage_update("bim-coordinator", "P3", "done", discipline="arc")["ok"] is False   # no qa-pass yet
    assert srv.stage_update("qa-data", "P3", "qa-pass", discipline="arc")["ok"] is False     # wrong gate
    srv.stage_update("arc-modeler", "P3", "review", evidence="02-cde/WIP/ARC/SCN-arc.rvt")
    srv.stage_update("qa-model", "P3", "qa-fail", discipline="arc", note="walls off by 40 mm")
    assert any(m["to"] == "arc-modeler" for m in srv.message_inbox("arc-modeler"))
    srv.stage_update("arc-modeler", "P3", "review")
    srv.stage_update("qa-model", "P3", "qa-pass", discipline="arc")
    assert srv.stage_update("bim-coordinator", "P3", "done", discipline="arc")["P3:arc"]["status"] == "done"
    assert srv.stage_update("str-modeler", "P1", "in-progress")["ok"] is False          # not owner/support
    w = srv.workflow_get()
    p3 = next(s for s in w["stages"] if s["id"] == "P3")
    assert p3["done"] == 1 and p3["total"] == 2
    assert srv.project_info()["project_type"]["id"] == "scan-to-bim"


def test_untyped_project_still_works(hub):
    srv = _srv("TST")
    assert srv.workflow_get()["type"] is None
    assert (hub / "projects" / "TST" / "WORKFLOW.md").is_file()


def test_point_cloud_readers(tmp_path):
    from bimhub.files.readers import read_file
    las = tmp_path / "scan.las"
    head = bytearray(227)
    head[0:4] = b"LASF"; head[24], head[25] = 1, 2; head[104] = 3
    head[105:107] = struct.pack("<H", 34); head[107:111] = struct.pack("<I", 1234567)
    head[131:227] = struct.pack("<12d", .001, .001, .001, 0, 0, 0, 50, 10, 30, 5, 12, 0)
    las.write_bytes(bytes(head))
    r = read_file(las)
    assert r["kind"] == "point-cloud" and r["points"] == 1234567 and r["extent_m"] == [40, 25, 12]

    # minimal E57: 48-byte header + one 1024-byte page of XML (last 4 bytes = CRC)
    xml = b'<?xml version="1.0"?><e57Root><data3D><vectorChild type="Structure"><points type="CompressedVector" ' \
          b'fileOffset="0" recordCount="5000"/></vectorChild><vectorChild type="Structure"><points ' \
          b'type="CompressedVector" fileOffset="0" recordCount="7000"/></vectorChild></data3D></e57Root>'
    page = bytearray(1024)
    off = 48
    hdr = b"ASTM-E57" + struct.pack("<IIQQQQ", 1, 0, 1024, off, len(xml), 1024)
    page[0:48] = hdr
    page[off:off + len(xml)] = xml
    e57 = tmp_path / "site.e57"
    e57.write_bytes(bytes(page))
    r = read_file(e57)
    assert r["scans"] == 2 and r["points"] == 12000
