"""Shared test setup: a temporary Trellis project with configured settings."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trellis_mcp import settings as settings_module
from trellis_mcp.paths import Paths
from trellis_mcp.settings import Settings


class ProjectTestCase(unittest.TestCase):
    """Configures process settings for a throwaway project directory."""

    design_authority = False
    context_window_tokens: int | None = None

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.paths = Paths.for_project(self.project)
        self.projects_root = self.root / "claude-projects"
        self.settings = Settings(
            paths=self.paths,
            project_name="Example",
            repo_root=self.project,
            design_authority=self.design_authority,
            claude_projects_root=self.projects_root,
            context_window_tokens=self.context_window_tokens,
        )
        settings_module.configure(self.settings)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(settings_module.configure, None)

    def ben(self, relative: str) -> str:
        """Absolute path of a Ben state file written as `workitems/...`."""
        return str(self.paths.ben_root / relative)

    def iris(self, relative: str) -> str:
        """Absolute path of an Iris state file written as `specflows/...`."""
        return str(self.paths.iris_root / relative)

    def sunny(self, relative: str) -> str:
        """Absolute path of a Sunny state file written as `intents/...`."""
        return str(self.paths.sunny_root / relative)
