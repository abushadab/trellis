"""Fixed on-disk layout of a Trellis project (DESIGN section 2).

Every location is derived from the project directory, so the MCP server, the
hook and the renderer always agree without environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

AGENT_NAMES = ("sunny", "iris", "ben")


@dataclass(frozen=True)
class Paths:
    project_dir: Path

    @classmethod
    def for_project(cls, project_dir: str | Path) -> Paths:
        return cls(Path(project_dir).expanduser().resolve())

    @property
    def trellis_dir(self) -> Path:
        return self.project_dir / ".trellis"

    @property
    def config_path(self) -> Path:
        return self.trellis_dir / "config.yml"

    @property
    def agents_dir(self) -> Path:
        return self.trellis_dir / "agents"

    def agent_root(self, agent: str) -> Path:
        return self.agents_dir / agent

    def guidance_dir(self, agent: str) -> Path:
        return self.agent_root(agent) / "guidance"

    @property
    def state_dir(self) -> Path:
        return self.trellis_dir / "state"

    @property
    def registry_path(self) -> Path:
        return self.state_dir / "registry.sqlite3"

    @property
    def handoffs_root(self) -> Path:
        return self.state_dir / "handoffs"

    @property
    def handoff_chat(self) -> Path:
        return self.handoffs_root / "chat.md"

    @property
    def sunny_root(self) -> Path:
        return self.state_dir / "sunny"

    @property
    def intents_root(self) -> Path:
        return self.sunny_root / "intents"

    @property
    def sessions_root(self) -> Path:
        return self.sunny_root / "sessions"

    @property
    def iris_root(self) -> Path:
        return self.state_dir / "iris"

    @property
    def specflows_root(self) -> Path:
        return self.iris_root / "specflows"

    @property
    def ben_root(self) -> Path:
        return self.state_dir / "ben"

    @property
    def workitems_root(self) -> Path:
        return self.ben_root / "workitems"

    def named(self, name: str) -> Path:
        """Resolve a ``{{path:name}}`` template name, without the agent argument."""
        table = {
            "project_dir": self.project_dir,
            "trellis_dir": self.trellis_dir,
            "state_dir": self.state_dir,
            "specflows_root": self.specflows_root,
            "workitems_root": self.workitems_root,
            "intents_root": self.intents_root,
            "handoff_chat": self.handoff_chat,
        }
        if name not in table:
            raise KeyError(name)
        return table[name]


GITIGNORE_TEXT = """\
# Managed by `trellis render`. Rendered prompts and runtime state are
# per-machine; specs and plans are the committed record of the workflow.
agents/
**/settings.local.json
state/**
!state/**/
!state/iris/specflows/*/specs/**
!state/ben/workitems/*/plans/**
"""
