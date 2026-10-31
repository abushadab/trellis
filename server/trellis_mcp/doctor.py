"""``trellis doctor``: check the machine, the config and the rendered files."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .config import ConfigError, TrellisConfig, load_config
from .paths import AGENT_NAMES, Paths
from .render import RenderError, render_project

OK, WARN, FAIL = "ok", "warn", "FAIL"


@dataclass(frozen=True)
class Check:
    status: str
    name: str
    detail: str = ""

    def line(self) -> str:
        return f"[{self.status:>4}] {self.name}" + (f": {self.detail}" if self.detail else "")


def _tool(name: str, *, required: bool, why: str) -> Check:
    found = shutil.which(name)
    if found:
        return Check(OK, name, found)
    return Check(FAIL if required else WARN, name, f"not on PATH ({why})")


def _claude_check() -> Check:
    found = shutil.which("claude")
    if not found:
        return Check(FAIL, "claude", "not on PATH (Sunny launches Iris and Ben through it)")
    try:
        result = subprocess.run([found, "--version"], capture_output=True, text=True, timeout=20)
        version = (
            (result.stdout or result.stderr).strip().splitlines()[0]
            if (result.stdout or result.stderr)
            else ""
        )
    except (OSError, subprocess.SubprocessError):
        version = "version check failed"
    return Check(OK, "claude", f"{found} {version}".strip())


def _trust_check(config: TrellisConfig) -> Check:
    from .trust import TrustError, claude_json_path, trust_roots, trust_state

    roots = trust_roots(config.project_dir, config.repo_root)
    try:
        state = trust_state(roots)
    except TrustError as exc:
        return Check(FAIL, "workspace trust", str(exc))
    missing = [str(root) for root, trusted in state.items() if not trusted]
    if not missing:
        return Check(OK, "workspace trust", "trusted: " + ", ".join(str(r) for r in roots))
    return Check(
        WARN,
        "workspace trust",
        f"not trusted in {claude_json_path()}: {', '.join(missing)}; "
        f"run `trellis trust --project {config.project_dir}` (sessions started by Sunny do it automatically)",
    )


def _usage_check() -> Check:
    from .usage import config_dir, token_available

    if token_available():
        return Check(
            OK, "usage token", f"`trellis usage` can read the OAuth token in {config_dir()}/.credentials.json"
        )
    return Check(
        WARN,
        "usage token",
        f"no OAuth token readable in {config_dir()}/.credentials.json (for example a keychain login); "
        "`trellis usage` prints `usage: unavailable` and the usage watcher stays off",
    )


def _git_repo(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _config_checks(config: TrellisConfig) -> list[Check]:
    checks = [Check(OK, "config", str(config.paths.config_path))]
    if config.unknown_keys:
        checks.append(Check(WARN, "config keys", "unknown keys ignored: " + ", ".join(config.unknown_keys)))
    if not config.repo_root.is_dir():
        checks.append(Check(FAIL, "repo_root", f"{config.repo_root} does not exist"))
    elif _git_repo(config.repo_root):
        checks.append(Check(OK, "repo_root", f"{config.repo_root} (git repository)"))
    else:
        checks.append(Check(WARN, "repo_root", f"{config.repo_root} is not inside a git repository"))
    if config.project_instructions and not config.project_instruction_files:
        checks.append(Check(WARN, "project_instructions", "none of the configured files exist"))
    for key in ("product_doc", "runtime_guide", "design_authority"):
        value = getattr(config, key)
        if value and not config.doc_exists(value):
            checks.append(Check(WARN, key, f"{config.resolve_doc(value)} does not exist"))
    if config.tools.serena and not config.tools.serena_url:
        checks.append(Check(FAIL, "tools.serena", "enabled but tools.serena_url is not set"))
    if config.tools.playwright == "true" and not shutil.which("npx"):
        checks.append(Check(FAIL, "tools.playwright", "enabled but npx is not on PATH"))
    return checks


def _rendered_checks(config: TrellisConfig, plugin_root: str | None, templates: str | None) -> list[Check]:
    paths = config.paths
    checks: list[Check] = []
    present = [a for a in AGENT_NAMES if paths.agent_root(a).is_dir()]
    if not present:
        return [Check(WARN, "rendered files", "none yet; run `trellis render` (/trellis:init does this)")]
    for agent in present:
        root = paths.agent_root(agent)
        missing = [
            rel for rel in ("CLAUDE.md", ".claude/settings.json", ".mcp.json") if not (root / rel).is_file()
        ]
        if missing:
            checks.append(Check(FAIL, f"rendered {agent}", "missing " + ", ".join(missing)))
        else:
            checks.append(Check(OK, f"rendered {agent}", str(root)))
    try:
        report = render_project(
            paths.project_dir, plugin_root=plugin_root, templates_root=templates, check=True, config=config
        )
    except RenderError as exc:
        checks.append(Check(FAIL, "render --check", str(exc)))
    else:
        if report.is_current:
            checks.append(Check(OK, "render --check", "rendered files match the templates"))
        else:
            checks.append(
                Check(WARN, "render --check", f"{len(report.stale)} file(s) stale; run `trellis render`")
            )
    if not (paths.trellis_dir / ".gitignore").is_file():
        checks.append(Check(WARN, ".trellis/.gitignore", "missing; run `trellis render`"))
    return checks


def run_doctor(
    project_dir: str | Path, *, plugin_root: str | None = None, templates: str | None = None
) -> list[Check]:
    checks = [Check(OK, "python", sys.version.split()[0])]
    checks.append(_claude_check())
    checks.append(_tool("uv", required=True, why="runs the Trellis server"))
    checks.append(_tool("uvx", required=True, why="runs the Trellis server and hooks"))
    checks.append(_tool("git", required=True, why="Ben and Iris commit through git"))
    checks.append(_tool("npx", required=False, why="Playwright browser testing is skipped without it"))

    try:
        config = load_config(project_dir)
    except ConfigError as exc:
        checks.append(Check(FAIL, "config", str(exc)))
        return checks
    checks.extend(_config_checks(config))
    checks.append(_trust_check(config))
    checks.append(_usage_check())
    checks.extend(_rendered_checks(config, plugin_root, templates))
    state = Paths(config.project_dir).state_dir
    checks.append(
        Check(OK, "state dir", str(state))
        if state.is_dir() or state.parent.is_dir()
        else Check(WARN, "state dir", f"{state} not created yet")
    )
    return checks
