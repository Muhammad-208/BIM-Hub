import shutil
from pathlib import Path

import pytest

HUB = Path(__file__).resolve().parents[2]


@pytest.fixture()
def hub(tmp_path, monkeypatch):
    """A throw-away copy of the hub with one project 'TST' (team arc, str, mech)."""
    root = tmp_path / "hub"
    root.mkdir()
    for d in ("agents", "learning-hub"):
        shutil.copytree(HUB / d, root / d)
    (root / "projects").mkdir()
    shutil.copytree(HUB / "projects" / "_template", root / "projects" / "_template")
    shutil.copytree(HUB / "mcp-layer" / "config", root / "mcp-layer" / "config")
    monkeypatch.setenv("BIMHUB_ROOT", str(root))
    monkeypatch.setenv("BIMHUB_PROJECT", "TST")
    from bimhub.cli.main import main
    assert main(["new-project", "TST", "--name", "Test Project", "--team", "arc,str,mech"]) == 0
    return root
