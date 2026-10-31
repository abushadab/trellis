from __future__ import annotations

import io
import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from fixture_templates import write_project
from support import ProjectTestCase
from test_sessions import DONE, SessionTestCase

from trellis_mcp import trust as trust_module
from trellis_mcp.cli import main
from trellis_mcp.doctor import FAIL, OK, WARN, run_doctor
from trellis_mcp.sessions import SessionError
from trellis_mcp.trust import TrustError, claude_json_path, ensure_trusted, git_root, trust_roots, trust_state


class TrustFileTests(ProjectTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.config_dir = self.root / "claude-config"
        self.config_dir.mkdir()
        patcher = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.config_dir)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.file = self.config_dir / ".claude.json"
        self.repo = self.root / "repo"
        self.repo.mkdir()

    def original(self) -> dict:
        return {
            "numStartups": 12,
            "theme": "dark",
            "projects": {"/other": {"hasTrustDialogAccepted": False, "allowedTools": ["Read"]}},
            "oauthAccount": {"emailAddress": "someone@example.test"},
        }

    def test_the_file_lives_in_the_config_dir_or_home(self) -> None:
        self.assertEqual(claude_json_path(), self.file)
        with mock.patch.dict(os.environ):
            os.environ.pop("CLAUDE_CONFIG_DIR")
            self.assertEqual(claude_json_path(), Path.home() / ".claude.json")

    def test_sets_only_the_trust_key_and_keeps_everything_else(self) -> None:
        self.file.write_text(json.dumps(self.original()))
        report = ensure_trusted([self.repo])
        after = json.loads(self.file.read_text())
        expected = self.original()
        expected["projects"][str(self.repo)] = {"hasTrustDialogAccepted": True}
        self.assertEqual(after, expected)
        self.assertEqual([(r.root, r.already) for r in report.results], [(self.repo, False)])

    def test_existing_project_entries_keep_their_other_keys(self) -> None:
        data = self.original()
        data["projects"][str(self.repo)] = {"hasTrustDialogAccepted": False, "allowedTools": ["Bash"], "x": 1}
        self.file.write_text(json.dumps(data))
        ensure_trusted([self.repo])
        entry = json.loads(self.file.read_text())["projects"][str(self.repo)]
        self.assertEqual(entry, {"hasTrustDialogAccepted": True, "allowedTools": ["Bash"], "x": 1})

    def test_one_time_backup_of_the_original(self) -> None:
        original_text = json.dumps(self.original())
        self.file.write_text(original_text)
        backup = self.config_dir / ".claude.json.trellis-bak"
        first = ensure_trusted([self.repo])
        self.assertEqual(first.backup, backup)
        self.assertEqual(backup.read_text(), original_text)
        other = self.root / "other-repo"
        other.mkdir()
        second = ensure_trusted([other])
        self.assertIsNone(second.backup)
        self.assertEqual(backup.read_text(), original_text)  # never overwritten

    def test_idempotent_second_run_writes_nothing(self) -> None:
        self.file.write_text(json.dumps(self.original()))
        ensure_trusted([self.repo])
        before = self.file.stat().st_mtime_ns
        text = self.file.read_text()
        report = ensure_trusted([self.repo])
        self.assertTrue(all(r.already for r in report.results))
        self.assertEqual(self.file.read_text(), text)
        self.assertEqual(self.file.stat().st_mtime_ns, before)

    def test_missing_file_is_created_without_a_backup(self) -> None:
        report = ensure_trusted([self.repo])
        self.assertIsNone(report.backup)
        self.assertEqual(
            json.loads(self.file.read_text()),
            {"projects": {str(self.repo): {"hasTrustDialogAccepted": True}}},
        )

    def test_permissions_are_kept_and_no_temp_files_remain(self) -> None:
        self.file.write_text("{}")
        self.file.chmod(0o600)
        ensure_trusted([self.repo])
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(
            sorted(p.name for p in self.config_dir.iterdir()), [".claude.json", ".claude.json.trellis-bak"]
        )

    def test_a_symlinked_file_stays_a_symlink(self) -> None:
        real = self.root / "dotfiles" / "claude.json"
        real.parent.mkdir()
        real.write_text("{}")
        self.file.symlink_to(real)
        ensure_trusted([self.repo])
        self.assertTrue(self.file.is_symlink())
        self.assertIn(str(self.repo), json.loads(real.read_text())["projects"])

    def test_invalid_json_is_never_overwritten(self) -> None:
        self.file.write_text("{ not json")
        with mock.patch.object(trust_module.time, "sleep"):
            with self.assertRaisesRegex(TrustError, "not valid JSON"):
                ensure_trusted([self.repo])
        self.assertEqual(self.file.read_text(), "{ not json")
        self.file.write_text("[1]")
        with self.assertRaisesRegex(TrustError, "JSON object"):
            ensure_trusted([self.repo])
        self.file.write_text(json.dumps({"projects": []}))
        with self.assertRaisesRegex(TrustError, "projects"):
            ensure_trusted([self.repo])

    def test_a_clobbered_write_is_retried_once(self) -> None:
        self.file.write_text(json.dumps(self.original()))
        real_write = trust_module._write_atomically
        calls = []

        def clobbering(path: Path, data: dict) -> None:
            calls.append(1)
            real_write(path, data)
            if len(calls) == 1:  # Claude Code rewrites its file from stale state
                path.write_text(json.dumps(self.original()))

        with (
            mock.patch.object(trust_module, "_write_atomically", clobbering),
            mock.patch.object(trust_module.time, "sleep"),
        ):
            ensure_trusted([self.repo])
        self.assertEqual(len(calls), 2)
        self.assertTrue(
            json.loads(self.file.read_text())["projects"][str(self.repo)]["hasTrustDialogAccepted"]
        )

    def test_gives_up_with_a_clear_error_after_one_retry(self) -> None:
        self.file.write_text(json.dumps(self.original()))
        real_write = trust_module._write_atomically

        def always_clobber(path: Path, data: dict) -> None:
            real_write(path, data)
            path.write_text(json.dumps(self.original()))

        with (
            mock.patch.object(trust_module, "_write_atomically", always_clobber),
            mock.patch.object(trust_module.time, "sleep"),
        ):
            with self.assertRaisesRegex(TrustError, "kept overwriting"):
                ensure_trusted([self.repo])

    def test_unwritable_location_is_a_trust_error(self) -> None:
        self.file.write_text("{}")
        with mock.patch.object(trust_module, "_write_atomically", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(TrustError, "Cannot write"):
                ensure_trusted([self.repo])

    def test_roots_are_git_roots_and_repo_root_is_added_when_different(self) -> None:
        project = self.root / "work" / "app"
        project.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(project.parent)], check=True)
        (project / "sub").mkdir()
        self.assertEqual(git_root(project / "sub"), project.parent.resolve())
        self.assertEqual(trust_roots(project, project / "sub"), [project.parent.resolve()])
        other = self.root / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        self.assertEqual(trust_roots(project, other), [project.parent.resolve(), other.resolve()])
        self.assertEqual(git_root(self.repo), self.repo.resolve())  # not a repository: itself

    def test_trust_state_is_read_only(self) -> None:
        self.assertEqual(trust_state([self.repo]), {self.repo: False})
        self.assertFalse(self.file.exists())
        ensure_trusted([self.repo])
        self.assertEqual(trust_state([self.repo]), {self.repo: True})


class TrustCommandTests(ProjectTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.config_dir = self.root / "claude-config"
        self.config_dir.mkdir()
        patcher = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.config_dir)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.file = self.config_dir / ".claude.json"
        self.app = write_project(self.root, "project_name: Example\nrepo_root: ../code\n")
        # project lives in `project/`; give it its own repo and a separate code repo
        subprocess.run(["git", "init", "-q", str(self.app)], check=True)
        (self.root / "code").mkdir()
        subprocess.run(["git", "init", "-q", str(self.root / "code")], check=True)

    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_trusts_the_project_root_and_a_different_repo_root(self) -> None:
        code, out, _ = self.run_main("trust", "--project", str(self.app))
        self.assertEqual(code, 0)
        projects = json.loads(self.file.read_text())["projects"]
        self.assertEqual(set(projects), {str(self.app.resolve()), str((self.root / "code").resolve())})
        self.assertIn(f"trusted: {self.app.resolve()}", out)
        self.assertIn(f"trusted: {(self.root / 'code').resolve()}", out)

        code, out, _ = self.run_main("trust", "--project", str(self.app))
        self.assertEqual(code, 0)
        self.assertEqual(out.count("already trusted"), 2)

    def test_failure_is_reported_on_stderr_with_exit_1(self) -> None:
        self.file.write_text("{ broken")
        with mock.patch.object(trust_module.time, "sleep"):
            code, out, err = self.run_main("trust", "--project", str(self.app))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("not valid JSON", err)
        self.assertIn("trust dialog", err)

    def test_missing_config_exits_2(self) -> None:
        (self.app / ".trellis" / "config.yml").unlink()
        self.assertEqual(self.run_main("trust", "--project", str(self.app))[0], 2)

    def test_doctor_reports_the_trust_state(self) -> None:
        check = {c.name: c for c in run_doctor(self.app)}["workspace trust"]
        self.assertEqual(check.status, WARN)
        self.assertIn("trellis trust", check.detail)
        self.run_main("trust", "--project", str(self.app))
        check = {c.name: c for c in run_doctor(self.app)}["workspace trust"]
        self.assertEqual(check.status, OK)
        self.file.write_text("{ broken")
        check = {c.name: c for c in run_doctor(self.app)}["workspace trust"]
        self.assertEqual(check.status, FAIL)


class SessionTrustTests(SessionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.config_dir = self.root / "claude-config-sessions"
        self.config_dir.mkdir()
        patcher = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.config_dir)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_start_and_resume_trust_the_project_before_launching(self) -> None:
        self.fake.set_responses([{"final": DONE}, {"final": DONE}])
        file = self.config_dir / ".claude.json"
        self.assertFalse(file.exists())
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        self.assertTrue(json.loads(file.read_text())["projects"][str(self.project)]["hasTrustDialogAccepted"])
        self.wait_finished(session_id)
        file.write_text(json.dumps({"projects": {}}))  # trust revoked in the meantime
        self.store.resume(session_id, "Continue.")
        self.assertTrue(json.loads(file.read_text())["projects"][str(self.project)]["hasTrustDialogAccepted"])

    def test_a_trust_failure_stops_the_launch_with_a_clear_error(self) -> None:
        self.fake.set_responses([{"final": DONE}])
        (self.config_dir / ".claude.json").write_text("{ broken")
        with mock.patch.object(trust_module.time, "sleep"):
            with self.assertRaisesRegex(SessionError, "not valid JSON.*trust dialog"):
                self.store.start("iris", "Go.", "x")
        self.assertEqual(self.fake.invocations(), [])
        self.assertEqual(self.store.all(), [])

    def test_the_tool_returns_the_error(self) -> None:
        import asyncio

        from trellis_mcp import session_tools

        (self.config_dir / ".claude.json").write_text("{ broken")
        with mock.patch.object(trust_module.time, "sleep"):
            result = asyncio.run(session_tools.start_session("ben", "Go.", "x"))
        self.assertFalse(result["ok"])
        self.assertIn("trust", result["error"])

    def test_the_test_suite_never_touches_the_real_claude_json(self) -> None:
        real = Path.home() / ".claude.json"
        self.assertNotEqual(claude_json_path(), real)


if __name__ == "__main__":
    unittest.main()
