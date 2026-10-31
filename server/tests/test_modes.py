import json
import subprocess
from pathlib import Path

import yaml

from trellis_mcp.render import render_project

PLUGIN = Path(__file__).resolve().parents[2]


def _project(tmp_path: Path, extra: str) -> Path:
    project = tmp_path / "proj"
    (project / ".trellis").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    (project / ".trellis" / "config.yml").write_text(f"project_name: P\ntools: {{playwright: false}}\n{extra}")
    return project


def _front(path: Path) -> dict:
    return yaml.safe_load(path.read_text().split("---\n")[1])


def _render(project: Path) -> Path:
    render_project(project, plugin_root=PLUGIN)
    return project / ".trellis" / "agents"


def test_standard_mode_matches_the_proven_setup(tmp_path):
    agents = _render(_project(tmp_path, ""))
    assert _front(agents / "ben/.claude/agents/plan_reviewer.md")["effort"] == "high"
    assert _front(agents / "ben/.claude/agents/implementation_engineer.md")["model"] == "sonnet"
    for name in ("sunny", "iris", "ben"):
        settings = json.loads((agents / name / ".claude/settings.json").read_text())
        assert (settings["model"], settings["effortLevel"]) == ("opus", "medium")


def test_saver_mode_has_no_opus_high_and_overrides_win(tmp_path):
    agents = _render(_project(tmp_path, "mode: saver\nmodels: {scout: haiku}\nefforts: {planner: low}\n"))
    for md in agents.glob("*/.claude/agents/*.md"):
        fm = _front(md)
        assert not (fm["model"] == "opus" and fm["effort"] == "high"), md.name
    assert _front(agents / "ben/.claude/agents/independent_final_validator.md")["model"] == "opus"
    assert _front(agents / "iris/.claude/agents/reconciliation_advisor.md")["model"] == "sonnet"
    assert _front(agents / "iris/.claude/agents/scout.md")["model"] == "haiku"
    assert _front(agents / "ben/.claude/agents/planner.md")["effort"] == "low"
    ben = json.loads((agents / "ben/.claude/settings.json").read_text())
    assert (ben["model"], ben["effortLevel"]) == ("sonnet", "high")
