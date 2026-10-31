from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml
from fixture_templates import write_project, write_templates

from trellis_mcp.config import parse_config
from trellis_mcp.render import (
    RenderContext,
    RenderError,
    process_conditionals,
    render_project,
    render_text,
)

REAL_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
FLAGS_ON = {
    "serena": True,
    "playwright": True,
    "product_doc": True,
    "runtime_guide": True,
    "design_authority": True,
    "reference_products": True,
    "pre_production": True,
    "commit_specs": True,
    "git_identity": True,
}


class ConditionalTests(unittest.TestCase):
    def render(self, text: str, **flags: bool) -> str:
        return process_conditionals(text, {**{k: False for k in FLAGS_ON}, **flags}, "test")

    def test_standalone_tag_lines_vanish_without_blank_lines(self) -> None:
        text = "a\n{{if:serena}}\nb\n{{else}}\nc\n{{/if}}\nd\n"
        self.assertEqual(self.render(text, serena=True), "a\nb\nd\n")
        self.assertEqual(self.render(text, serena=False), "a\nc\nd\n")

    def test_inline_and_nested_blocks(self) -> None:
        line = "tools: A{{if:serena}}, B{{if:playwright}}, C{{else}}, D{{/if}}{{/if}}\n"
        self.assertEqual(self.render(line, serena=True, playwright=True), "tools: A, B, C\n")
        self.assertEqual(self.render(line, serena=True, playwright=False), "tools: A, B, D\n")
        self.assertEqual(self.render(line), "tools: A\n")

    def test_nested_multiline_blocks(self) -> None:
        text = "{{if:serena}}\nx\n{{if:playwright}}\ny\n{{/if}}\nz\n{{/if}}\n"
        self.assertEqual(self.render(text, serena=True, playwright=True), "x\ny\nz\n")
        self.assertEqual(self.render(text, serena=True), "x\nz\n")
        self.assertEqual(self.render(text, playwright=True), "")

    def test_blank_line_runs_collapse_outside_code_fences(self) -> None:
        from trellis_mcp.render import tidy_blank_lines

        text = "a\n\n\n\nb\n```\nx\n\n\ny\n```\nc\n"
        self.assertEqual(tidy_blank_lines(text), "a\n\nb\n```\nx\n\n\ny\n```\nc\n")

    def test_negated_flags(self) -> None:
        self.assertEqual(self.render("{{if:!serena}}no{{/if}}"), "no")
        self.assertEqual(self.render("{{if:!serena}}no{{/if}}", serena=True), "")

    def test_errors(self) -> None:
        for text, message in (
            ("{{if:nope}}x{{/if}}", "unknown flag"),
            ("{{if:serena}}x", "never closed"),
            ("x{{/if}}", "without a matching"),
            ("{{else}}", "without a matching"),
            ("{{if:serena}}{{else}}{{else}}{{/if}}", "without a matching"),
        ):
            with self.subTest(text=text):
                with self.assertRaisesRegex(RenderError, message):
                    self.render(text)


class ValueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        project = write_project(self.root, docs=True)
        config = parse_config(
            {"project_name": "Example", "reference_products": ["A", "B"], "product_doc": "PRODUCT.md"},
            project,
        )
        self.project = project
        self.ctx = RenderContext(config, self.root / "plugin", self.root / "plugin" / "templates")

    def test_config_and_path_placeholders(self) -> None:
        text = (
            "{{config:project_name}}|{{config:reference_products}}|{{config:product_doc}}|"
            "{{path:project_dir}}|{{path:repo_root}}|{{path:plugin_root}}|{{path:handoff_chat}}|"
            "{{path:agent_root:ben}}|{{path:guidance:iris}}|{{path:specflows_root}}"
        )
        out = render_text(text, self.ctx, "t").split("|")
        self.assertEqual(out[0:2], ["Example", "A, B"])
        self.assertEqual(out[2], str(self.project / "PRODUCT.md"))
        self.assertEqual(out[3], str(self.project))
        self.assertEqual(out[5], str(self.root / "plugin"))
        self.assertTrue(out[6].endswith(".trellis/state/handoffs/chat.md"))
        self.assertTrue(out[7].endswith(".trellis/agents/ben"))
        self.assertTrue(out[8].endswith(".trellis/agents/iris/guidance"))
        self.assertTrue(out[9].endswith(".trellis/state/iris/specflows"))
        self.assertTrue(all(part.startswith("/") for part in out[3:]))

    def test_unknown_or_unset_values_are_errors(self) -> None:
        for text in (
            "{{config:nope}}",
            "{{path:nope}}",
            "{{path:agent_root:zed}}",
            "{{config:runtime_guide}}",
            "{{config:git.commit_email}}",
            "{{config:git}}",
        ):
            with self.subTest(text=text):
                with self.assertRaisesRegex(RenderError, "unknown or unset"):
                    render_text(text, self.ctx, "t")

    def test_malformed_placeholders_do_not_slip_through(self) -> None:
        with self.assertRaisesRegex(RenderError, "unresolved or malformed"):
            render_text("{{config:}}", self.ctx, "t")
        with self.assertRaisesRegex(RenderError, "unresolved or malformed"):
            render_text("{{shared:x}} inline", self.ctx, "t")


class FixtureRenderTests(unittest.TestCase):
    CONFIG = (
        "project_name: Example\nproduct_doc: PRODUCT.md\nruntime_guide: RUNTIME.md\n"
        "design_authority: DESIGN.md\nmodels: {planner: sonnet}\n"
        "tools: {serena: true, serena_url: 'http://127.0.0.1:1/mcp', playwright: true}\n"
    )

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.plugin = self.root / "plugin"
        self.templates = write_templates(self.plugin)
        self.project = write_project(self.root, self.CONFIG, docs=True)
        self.out = self.project / ".trellis" / "agents" / "ben"

    def render(self, **kwargs):
        return render_project(self.project, plugin_root=self.plugin, **kwargs)

    def test_renders_prompts_subagents_guidance_settings_and_mcp(self) -> None:
        report = self.render()
        self.assertTrue(report.written)
        main = (self.out / "CLAUDE.md").read_text()
        self.assertIn("# Ben for Example", main)
        self.assertIn(f"`{self.project}/.trellis/state`", main)
        self.assertIn("Pre-production: no compatibility work.", main)
        self.assertNotIn("Production: keep", main)
        self.assertIn("Write plainly for Example.", main)
        self.assertIn("Branch prefix: ben/", main)
        self.assertIn("# Project Instructions", main)
        self.assertIn(str(self.project / "AGENTS.md"), main)
        self.assertIn("# Local Runtime Guide", main)
        self.assertNotIn("# Product Document", main)  # not listed for ben

        planner = (self.out / ".claude" / "agents" / "planner.md").read_text()
        self.assertTrue(planner.startswith("---\nname: planner\n"))
        self.assertIn("model: sonnet\n", planner)  # models override the literal model
        self.assertNotIn("model: opus", planner)
        self.assertIn("tools: Read, Bash, mcp__serena__find_symbol, mcp__playwright\n", planner)
        self.assertIn("mcpServers:\n  - playwright\n", planner)
        self.assertIn("Use Serena first.", planner)
        self.assertNotIn("Use grep for lookups.", planner)
        self.assertIn("# Product Document", planner)
        frontmatter = yaml.safe_load(planner.split("---\n")[1])
        self.assertEqual(frontmatter["name"], "planner")

        advisor = (self.out / ".claude" / "agents" / "general_advisor.md").read_text()
        self.assertIn("Write plainly for Example.", advisor)
        self.assertNotIn("# Project Instructions", advisor)  # not listed

        guidance = self.out / "guidance"
        self.assertIn("chat at", (guidance / "rules.md").read_text())
        self.assertIn(str(self.project / "DESIGN.md"), (guidance / "design.md").read_text())
        self.assertEqual((guidance / "data.bin").read_text(), "binary-ish {{not rendered}}")
        self.assertEqual((guidance / "testing" / "guide.md").read_text(), "Shared guide for Example.\n")
        self.assertTrue((guidance / "testing" / "browser.md").is_file())

        settings = json.loads((self.out / ".claude" / "settings.json").read_text())
        self.assertEqual(settings["permissions"]["additionalDirectories"], [str(self.project)])
        command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        self.assertEqual(
            command,
            f"uvx --from {self.plugin}/server trellis hook register-subagent --agent ben --project {self.project}",
        )
        mcp = json.loads((self.out / ".mcp.json").read_text())
        args = mcp["mcpServers"]["trellis"]["args"]
        self.assertEqual(args[2:], ["trellis", "serve", "--agent", "ben", "--project", str(self.project)])
        self.assertEqual(args[:2], ["--from", f"{self.plugin}/server"])
        self.assertEqual(mcp["mcpServers"]["serena"], {"type": "http", "url": "http://127.0.0.1:1/mcp"})
        roles = json.loads((self.out / "roles.json").read_text())
        self.assertEqual(roles, {"general_advisor": "general_advisor"})  # not a default for ben
        self.assertEqual((self.project / ".trellis" / ".gitignore").read_text()[:19], "# Managed by `trell")

    def test_additional_directories_include_a_separate_repo_root(self) -> None:
        (self.project / "code").mkdir()
        (self.project / ".trellis" / "config.yml").write_text("project_name: X\nrepo_root: code\n")
        self.render()
        settings = json.loads((self.out / ".claude" / "settings.json").read_text())
        self.assertEqual(
            settings["permissions"]["additionalDirectories"],
            [str(self.project), str(self.project / "code")],
        )

    def test_flags_off_drop_the_optional_pieces(self) -> None:
        (self.project / ".trellis" / "config.yml").write_text(
            "project_name: Example\nstage: production\ntools: {playwright: false}\n"
        )
        self.render()
        main = (self.out / "CLAUDE.md").read_text()
        self.assertIn("Production: keep compatibility.", main)
        self.assertNotIn("# Local Runtime Guide", main)
        planner = (self.out / ".claude" / "agents" / "planner.md").read_text()
        self.assertIn("tools: Read, Bash\n", planner)
        self.assertNotIn("mcpServers", planner)
        self.assertIn("model: opus", planner)
        self.assertIn("Use grep for lookups.", planner)
        self.assertFalse((self.out / "guidance" / "design.md").exists())
        self.assertFalse((self.out / "guidance" / "testing" / "browser.md").exists())
        mcp = json.loads((self.out / ".mcp.json").read_text())
        self.assertEqual(list(mcp["mcpServers"]), ["trellis"])

    def test_check_mode_reports_stale_files_and_does_not_write(self) -> None:
        stale = self.render(check=True)
        self.assertFalse(stale.is_current)
        self.assertFalse((self.out / "CLAUDE.md").exists())
        self.render()
        self.assertTrue(self.render(check=True).is_current)
        (self.out / "CLAUDE.md").write_text("edited")
        report = self.render(check=True)
        self.assertEqual(report.stale, [self.out / "CLAUDE.md"])
        self.assertEqual((self.out / "CLAUDE.md").read_text(), "edited")
        self.render()
        self.assertTrue(self.render(check=True).is_current)

    def test_second_render_is_a_no_op_and_stale_outputs_are_removed(self) -> None:
        self.render()
        again = self.render()
        self.assertTrue(again.is_current)
        leftover = self.out / ".claude" / "agents" / "old-role.md"
        leftover.write_text("gone soon")
        local = self.out / ".claude" / "settings.local.json"
        local.write_text("{}")
        self.assertFalse(self.render(check=True).is_current)
        report = self.render()
        self.assertEqual(report.removed, [leftover])
        self.assertTrue(local.exists())  # user-owned files are never touched

    def test_required_shared_parts_are_enforced(self) -> None:
        path = self.templates / "agents/ben/prompt-src/ben/02-shared.md"
        path.write_text("nothing shared here\n")
        with self.assertRaisesRegex(RenderError, "Missing required shared parts in ben: writing"):
            self.render()

    def test_a_shared_part_in_a_dead_branch_still_counts_as_included(self) -> None:
        # planner requires both `serena` and `lookups`; only one survives rendering.
        self.render()
        (self.project / ".trellis" / "config.yml").write_text("project_name: X\n")
        self.render()
        planner = (self.out / ".claude" / "agents" / "planner.md").read_text()
        self.assertIn("Use grep for lookups.", planner)
        self.assertNotIn("Use Serena first.", planner)

    def test_duplicate_unknown_and_misnumbered_parts_are_errors(self) -> None:
        planner = self.templates / "agents/ben/prompt-src/planner/01-role.md"
        original = planner.read_text()
        planner.write_text(original + "\n{{shared:writing}}\n")
        with self.assertRaisesRegex(RenderError, "more than once"):
            self.render()
        planner.write_text(original + "\n{{shared:nothing}}\n")
        with self.assertRaisesRegex(RenderError, "Unknown shared parts"):
            self.render()
        planner.write_text(original)
        (planner.parent / "03-extra.md").write_text("x\n")
        with self.assertRaisesRegex(RenderError, "numbered consecutively"):
            self.render()

    def test_manifest_problems_are_reported(self) -> None:
        manifest = self.templates / "agents/ben/manifest.yml"
        original = manifest.read_text()
        manifest.write_text(original + "surprise: 1\n")
        with self.assertRaisesRegex(RenderError, "unknown keys: surprise"):
            self.render()
        manifest.write_text(original.replace("flag: playwright", "flag: nonsense"))
        with self.assertRaisesRegex(RenderError, "unknown flag"):
            self.render()
        manifest.unlink()
        with self.assertRaisesRegex(RenderError, "Missing .*manifest.yml"):
            self.render()

    def test_frontmatter_name_must_match_the_manifest_role(self) -> None:
        fm = self.templates / "agents/ben/prompt-src/planner/frontmatter.yml"
        fm.write_text(fm.read_text().replace("name: planner", "name: other"))
        with self.assertRaisesRegex(RenderError, "declares `name: other`"):
            self.render()

    def test_roles_unknown_to_the_hook_are_written_for_it(self) -> None:
        manifest = self.templates / "agents/ben/manifest.yml"
        manifest.write_text(manifest.read_text().replace("name: planner", "name: Planner-X"))
        fm = self.templates / "agents/ben/prompt-src/planner/frontmatter.yml"
        fm.write_text(fm.read_text().replace("name: planner", "name: Planner-X"))
        self.render()
        roles = json.loads((self.out / "roles.json").read_text())
        self.assertEqual(roles, {"general_advisor": "general_advisor", "planner_x": "planner_x"})

    def test_serena_without_a_url_is_an_error(self) -> None:
        (self.project / ".trellis" / "config.yml").write_text("project_name: X\ntools: {serena: true}\n")
        with self.assertRaisesRegex(RenderError, "serena_url"):
            self.render()

    def test_missing_config_is_a_render_error(self) -> None:
        (self.project / ".trellis" / "config.yml").unlink()
        with self.assertRaisesRegex(RenderError, "/trellis:init"):
            self.render()

    def test_plugin_root_must_hold_templates_and_server(self) -> None:
        with self.assertRaisesRegex(RenderError, "not a Trellis plugin root"):
            render_project(self.project, plugin_root=self.root)

    def test_templates_override_and_agent_filter(self) -> None:
        elsewhere = self.root / "other-templates"
        shutil.copytree(self.templates, elsewhere)
        (elsewhere / "agents/ben/guidance/rules.md").write_text("overridden\n")
        render_project(self.project, plugin_root=self.plugin, templates_root=elsewhere, agents=["ben"])
        self.assertEqual((self.out / "guidance" / "rules.md").read_text(), "overridden\n")
        with self.assertRaisesRegex(RenderError, "No templates for: iris"):
            render_project(self.project, plugin_root=self.plugin, agents=["iris"])

    def test_gitignore_keeps_specs_and_plans_and_ignores_the_rest(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        self.render()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        state = self.project / ".trellis" / "state"
        files = {
            "iris/specflows/sf/specs/a-single-spec.md": False,
            "iris/specflows/sf/chat.md": True,
            "iris/specflows/sf/assignments/T/scout-assignment-r1.md": True,
            "ben/workitems/wi/plans/plan.md": False,
            "ben/workitems/wi/chat.md": True,
            "registry.sqlite3": True,
            "handoffs/chat.md": True,
        }
        for rel in files:
            path = state / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x")
        (self.out / ".claude" / "settings.local.json").write_text("{}")
        for rel, ignored in files.items():
            result = subprocess.run(["git", "-C", str(self.project), "check-ignore", "-q", str(state / rel)])
            self.assertEqual(result.returncode == 0, ignored, rel)
        for rel in ("CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json"):
            result = subprocess.run(
                ["git", "-C", str(self.project), "check-ignore", "-q", str(self.out / rel)]
            )
            self.assertEqual(result.returncode, 0, rel)
        self.assertNotEqual(
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.project),
                    "check-ignore",
                    "-q",
                    str(self.project / ".trellis/config.yml"),
                ]
            ).returncode,
            0,
        )

    def test_fixture_style_notes_are_not_rendered(self) -> None:
        self.render()
        # STYLE.md mentions `{{if:...}}` and must not reach any output.
        for path in (self.project / ".trellis").rglob("*"):
            if path.is_file():
                self.assertNotIn("{{if:...}}", path.read_text(errors="ignore"), path)


@unittest.skipUnless((REAL_PLUGIN_ROOT / "templates" / "agents").is_dir(), "real templates not present")
class RealTemplateTests(unittest.TestCase):
    """Render the shipped templates with every flag on, then every flag off."""

    ON = (
        "project_name: Demo\nrepo_root: repo\nproduct_doc: PRODUCT.md\nruntime_guide: RUNTIME.md\n"
        "design_authority: DESIGN.md\nreference_products: [Alpha, Beta]\n"
        "git: {commit_name: Dev, commit_email: dev@example.test}\n"
        "tools: {serena: true, serena_url: 'http://127.0.0.1:9000/mcp', playwright: true}\n"
        "models: {planner: sonnet}\n"
    )
    OFF = (
        "project_name: Demo\nstage: production\ncommit_specs: false\n"
        "project_instructions: []\ntools: {playwright: false}\n"
    )

    def render(self, config: str, *, docs: bool):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        project = write_project(root, config)
        (project / "repo").mkdir()
        if docs:
            for name in ("AGENTS.md", "PRODUCT.md", "RUNTIME.md", "DESIGN.md"):
                (project / "repo" / name).write_text(f"# {name}\n")
        report = render_project(project, plugin_root=REAL_PLUGIN_ROOT)
        self.assertTrue(report.written)
        return project

    def assert_clean(self, project: Path) -> list[Path]:
        files = [p for p in (project / ".trellis").rglob("*") if p.is_file()]
        self.assertGreater(len(files), 20)
        for path in files:
            # The plugin checkout path is machine-specific and legitimately appears in commands.
            text = path.read_text(encoding="utf-8").replace(str(REAL_PLUGIN_ROOT), "<plugin>")
            self.assertNotIn("{{", text, path)
            for forbidden in ("Attestara", "Probo", "ghki", "/home/abu"):
                self.assertNotIn(forbidden, text, path)
            if path.suffix == ".json":
                json.loads(text)
            if path.parent.name == "agents" and path.suffix == ".md":
                self.assertTrue(text.startswith("---\nname: "), path)
                yaml.safe_load(text.split("---\n")[1])
            self.assertNotRegex(text, r"\n\n\n\n", path)
        return files

    def test_all_flags_on(self) -> None:
        project = self.render(self.ON, docs=True)
        files = self.assert_clean(project)
        names = {p.name for p in files}
        self.assertIn("design-conformance-lens.md", names)
        self.assertIn("browser-guide.md", names)
        ben = project / ".trellis/agents/ben"
        planner = (ben / ".claude/agents/planner.md").read_text()
        self.assertIn("model: sonnet", planner)
        self.assertIn("mcp__serena__", planner)
        self.assertIn(str(project / "repo" / "RUNTIME.md"), (ben / "CLAUDE.md").read_text())
        mcp = json.loads((ben / ".mcp.json").read_text())
        self.assertIn("serena", mcp["mcpServers"])
        settings = json.loads((ben / ".claude/settings.json").read_text())
        command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        self.assertIn(f"{REAL_PLUGIN_ROOT}/server", command)
        self.assertIn(f"--project {project}", command)

    def test_all_flags_off(self) -> None:
        project = self.render(self.OFF, docs=False)
        files = self.assert_clean(project)
        self.assertNotIn("design-conformance-lens.md", {p.name for p in files})
        ben = project / ".trellis/agents/ben"
        self.assertNotIn("mcp__serena__", (ben / ".claude/agents/planner.md").read_text())
        self.assertNotIn("# Project Instructions", (ben / "CLAUDE.md").read_text())
        mcp = json.loads((ben / ".mcp.json").read_text())
        self.assertEqual(list(mcp["mcpServers"]), ["trellis"])

    def test_every_tool_the_templates_name_exists(self) -> None:
        from trellis_mcp.tools import TOOLSETS

        known = {f.__name__ for toolset in TOOLSETS.values() for f in toolset}
        used: set[str] = set()
        for path in (REAL_PLUGIN_ROOT / "templates").rglob("*"):
            if path.is_file():
                used |= set(re.findall(r"mcp__trellis__([a-z_]+)", path.read_text(errors="ignore")))
        self.assertEqual(used - known, set())

    def test_no_forbidden_words_ship_in_the_templates(self) -> None:
        for path in (REAL_PLUGIN_ROOT / "templates").rglob("*"):
            if path.is_file():
                text = path.read_text(errors="ignore")
                for forbidden in ("Attestara", "Probo", "KI-Quadrat", "ghki", "ai2.at", "/home/abu"):
                    self.assertNotIn(forbidden, text, path)


if __name__ == "__main__":
    unittest.main()
