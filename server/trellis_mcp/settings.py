"""Runtime settings for one MCP server process.

The settings are built once in ``main()`` (``configure``) and read by the
transports through ``get()``. Nothing is read from the environment or the
filesystem at import time.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .config import TrellisConfig, default_claude_projects_root, load_config
from .paths import Paths

MAX_AUTHOR_LENGTH = 100
MAX_MESSAGE_SIZE = 50 * 1024  # 50KB


@dataclass(frozen=True)
class Settings:
    paths: Paths
    project_name: str = "this project"
    repo_root: Path | None = None
    design_authority: bool = False
    claude_projects_root: Path | None = None
    # None means "infer from the transcript's model" (200k unless a 1M model).
    context_window_tokens: int | None = None
    reuse_threshold_percent: int = 75
    slot_reuse_percent: int = 30
    max_author_length: int = MAX_AUTHOR_LENGTH
    max_message_size: int = MAX_MESSAGE_SIZE

    @property
    def project_dir(self) -> Path:
        return self.paths.project_dir

    @property
    def projects_root(self) -> Path:
        return self.claude_projects_root or default_claude_projects_root()

    @classmethod
    def from_config(cls, config: TrellisConfig) -> Settings:
        return cls(
            paths=config.paths,
            project_name=config.project_name,
            repo_root=config.repo_root,
            design_authority=config.doc_exists(config.design_authority),
            claude_projects_root=config.claude_projects_root,
            context_window_tokens=config.context_window_tokens,
        )

    @classmethod
    def for_project(cls, project_dir: str | Path) -> Settings:
        return cls.from_config(load_config(project_dir))

    @classmethod
    def for_directory(cls, project_dir: str | Path, **overrides) -> Settings:
        """Settings without a config file (hook, tests): fixed layout, defaults."""
        return replace(cls(paths=Paths.for_project(project_dir)), **overrides)


_current: Settings | None = None


def configure(settings: Settings | None) -> None:
    """Install the process-wide settings (``None`` clears them)."""
    global _current
    _current = settings


def get() -> Settings:
    if _current is None:
        raise RuntimeError("Trellis settings are not configured; start the server through `trellis serve`")
    return _current
