from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fixture_templates import write_project

from trellis_mcp.config import ConfigError, load_config, parse_config
from trellis_mcp.paths import GITIGNORE_TEXT, Paths
from trellis_mcp.settings import Settings


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.addCleanup(self.tmp.cleanup)

    def test_defaults_follow_the_design(self) -> None:
        project = write_project(self.root)
        config = load_config(project)
        self.assertEqual(config.project_name, "Example")
        self.assertEqual(config.repo_root, project)
        self.assertEqual(config.stage, "pre_production")
        self.assertEqual(config.git.branch_prefix, "ben/")
        self.assertEqual(config.git.work_branch_prefix, "work/")
        self.assertTrue(config.commit_specs)
        self.assertEqual(config.tools.playwright, "auto")
        self.assertEqual(config.sunny.usage_threshold, 75)
        self.assertEqual(config.sunny.autonomy, "technical")
        self.assertIsNone(config.context_window_tokens)
        self.assertEqual(config.unknown_keys, ())

    def test_project_name_is_required(self) -> None:
        with self.assertRaisesRegex(ConfigError, "project_name"):
            parse_config({}, self.root)
        with self.assertRaisesRegex(ConfigError, "mapping"):
            parse_config(["x"], self.root)

    def test_missing_file_points_at_init(self) -> None:
        with self.assertRaisesRegex(ConfigError, "/trellis:init"):
            load_config(self.root)

    def test_invalid_values_are_rejected(self) -> None:
        for data, message in (
            ({"stage": "beta"}, "stage"),
            ({"tools": {"playwright": "sometimes"}}, "playwright"),
            ({"sunny": {"autonomy": "full"}}, "autonomy"),
            ({"sunny": {"usage_threshold": 0}}, "usage_threshold"),
            ({"project_instructions": "AGENTS.md"}, "project_instructions"),
            ({"git": {"branch_prefix": ""}}, "branch_prefix"),
            ({"context_window_tokens": 5}, "context_window_tokens"),
            ({"models": {"planner": ""}}, "models"),
        ):
            with self.subTest(data=data):
                with self.assertRaisesRegex(ConfigError, message):
                    parse_config({"project_name": "X", **data}, self.root)

    def test_unknown_keys_are_reported_not_fatal(self) -> None:
        config = parse_config({"project_name": "X", "surprise": 1}, self.root)
        self.assertEqual(config.unknown_keys, ("surprise",))

    def test_paths_resolve_against_repo_root_and_flags_follow_existence(self) -> None:
        project = write_project(
            self.root,
            "project_name: X\nrepo_root: code\nproduct_doc: PRODUCT.md\nruntime_guide: MISSING.md\n"
            "design_authority: https://example.test/design\nreference_products: [A, B]\n"
            "git: {commit_name: N}\ntools: {playwright: false}\n",
        )
        (project / "code").mkdir()
        (project / "code" / "PRODUCT.md").write_text("p", encoding="utf-8")
        config = load_config(project)
        self.assertEqual(config.repo_root, project / "code")
        flags = config.flags()
        self.assertTrue(flags["product_doc"])
        self.assertFalse(flags["runtime_guide"])
        self.assertTrue(flags["design_authority"])  # a URL counts
        self.assertTrue(flags["reference_products"])
        self.assertFalse(flags["git_identity"])  # needs both name and email
        self.assertFalse(flags["playwright"])
        self.assertEqual(config.value("product_doc"), str(project / "code" / "PRODUCT.md"))
        self.assertEqual(config.value("design_authority"), "https://example.test/design")
        self.assertEqual(config.value("reference_products"), "A, B")
        with self.assertRaises(KeyError):
            config.value("runtime_guide.nope")
        with self.assertRaises(KeyError):
            config.value("git.commit_email")  # unset

    def test_git_identity_needs_both_values(self) -> None:
        both = parse_config(
            {"project_name": "X", "git": {"commit_name": "N", "commit_email": "e@x.test"}}, self.root
        )
        self.assertTrue(both.flags()["git_identity"])

    def test_settings_come_from_the_config(self) -> None:
        project = write_project(
            self.root,
            "project_name: X\ncontext_window_tokens: 500000\nclaude_projects_root: /somewhere/projects\n",
        )
        settings = Settings.for_project(project)
        self.assertEqual(settings.project_name, "X")
        self.assertEqual(settings.context_window_tokens, 500000)
        self.assertEqual(settings.projects_root, Path("/somewhere/projects"))
        self.assertEqual(settings.paths, Paths.for_project(project))
        self.assertFalse(settings.design_authority)

    def test_claude_executable_defaults_to_claude_and_is_configurable(self) -> None:
        self.assertEqual(parse_config({"project_name": "X"}, self.root).claude_executable, "claude")
        config = parse_config({"project_name": "X", "claude_executable": "/opt/claude"}, self.root)
        self.assertEqual(config.claude_executable, "/opt/claude")
        self.assertEqual(Settings.from_config(config).claude_executable, "/opt/claude")
        with self.assertRaisesRegex(ConfigError, "claude_executable"):
            parse_config({"project_name": "X", "claude_executable": ""}, self.root)

    def test_default_projects_root_is_the_claude_directory(self) -> None:
        settings = Settings.for_directory(self.root)
        self.assertEqual(settings.projects_root.name, "projects")
        self.assertIn("claude", str(settings.projects_root).lower())

    def test_gitignore_text_matches_the_design(self) -> None:
        for line in ("agents/", "**/settings.local.json", "state/**", "!state/iris/specflows/*/specs/**"):
            self.assertIn(line, GITIGNORE_TEXT)
        self.assertIn("!state/ben/workitems/*/plans/**", GITIGNORE_TEXT)


if __name__ == "__main__":
    unittest.main()
