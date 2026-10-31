"""Workspace trust for headless sessions.

``claude -p`` never shows the trust dialog, and until the project is trusted it ignores the
project's ``permissions.additionalDirectories`` and allow rules. Claude Code records trust in
``~/.claude.json`` (or ``$CLAUDE_CONFIG_DIR/.claude.json``) as
``projects[<abs git root>].hasTrustDialogAccepted = true``. This module sets exactly that key.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

BACKUP_SUFFIX = ".trellis-bak"
KEY = "hasTrustDialogAccepted"


class TrustError(Exception):
    """Trust could not be read or set."""


def claude_json_path() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base).expanduser() if base else Path.home()) / ".claude.json"


def git_root(path: Path) -> Path:
    """The enclosing git repository root, or ``path`` itself outside a repository."""
    path = Path(path).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return path
    top = result.stdout.strip()
    return Path(top).resolve() if result.returncode == 0 and top else path


def main_checkout_root(path: Path) -> Path | None:
    """For a linked worktree, the main checkout's root (Claude Code keys trust on it); else None."""
    try:
        result = subprocess.run(
            ["git", "-C", str(Path(path).resolve()), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    common = result.stdout.strip()
    if result.returncode != 0 or not common:
        return None
    common_dir = Path(common).resolve()
    return common_dir.parent if common_dir.name == ".git" else None


def trust_roots(project_dir: Path, repo_root: Path | None = None) -> list[Path]:
    """The git roots to trust: the project's, ``repo_root``'s when different, and for a linked
    worktree also its main checkout, which is the path Claude Code actually checks."""
    roots: list[Path] = []
    for path in [project_dir] + ([repo_root] if repo_root is not None else []):
        for root in (git_root(path), main_checkout_root(path)):
            if root is not None and root not in roots:
                roots.append(root)
    return roots


def _read(path: Path, *, retry: bool = True) -> dict:
    """Parse the file. A half-written file is retried once; an unreadable one is never replaced."""
    for attempt in range(2 if retry else 1):
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        except OSError as exc:
            raise TrustError(f"Cannot read {path}: {exc}") from None
        if not text.strip():
            return {}
        try:
            data = json.loads(text)
        except ValueError:
            if attempt == 0 and retry:
                time.sleep(0.3)  # Claude Code may be mid-write
                continue
            raise TrustError(f"{path} is not valid JSON; refusing to touch it") from None
        if not isinstance(data, dict):
            raise TrustError(f"{path} does not hold a JSON object; refusing to touch it")
        return data
    raise TrustError(f"Cannot parse {path}")  # pragma: no cover


def _is_trusted(data: dict, root: Path) -> bool:
    projects = data.get("projects")
    entry = projects.get(str(root)) if isinstance(projects, dict) else None
    return isinstance(entry, dict) and entry.get(KEY) is True


def trust_state(roots: list[Path], path: Path | None = None) -> dict[Path, bool]:
    """Read-only: which roots are already trusted."""
    data = _read(path or claude_json_path(), retry=False)
    return {root: _is_trusted(data, root) for root in roots}


@dataclass
class TrustResult:
    root: Path
    already: bool


@dataclass
class TrustReport:
    path: Path
    results: list[TrustResult]
    backup: Path | None  # set when this call created the one-time backup

    def lines(self) -> list[str]:
        out = []
        for result in self.results:
            out.append(f"{'already trusted' if result.already else 'trusted'}: {result.root}")
        if self.backup:
            out.append(f"backup of {self.path.name}: {self.backup}")
        return out


def _write_atomically(path: Path, data: dict) -> None:
    real = Path(os.path.realpath(path))  # keep a symlinked config file a symlink
    real.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{real.name}.", suffix=".tmp", dir=real.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            shutil.copymode(real, temp)
        except FileNotFoundError:
            os.chmod(temp, 0o600)
        os.replace(temp, real)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def ensure_trusted(roots: list[Path], path: Path | None = None) -> TrustReport:
    """Mark every root trusted in the Claude config file. Idempotent.

    Changes only ``projects[<root>].hasTrustDialogAccepted``, keeps one backup of the original
    file, writes through a temp file and rename, then re-reads to verify. If a concurrent
    Claude Code write removed the change, it retries once.
    """
    target = path or claude_json_path()
    roots = [Path(r) for r in roots]
    data = _read(target)
    pending = [root for root in roots if not _is_trusted(data, root)]
    results = [TrustResult(root, root not in pending) for root in roots]
    backup: Path | None = None
    if not pending:
        return TrustReport(target, results, None)

    real = Path(os.path.realpath(target))
    backup_path = real.with_name(real.name + BACKUP_SUFFIX)
    if real.exists() and not backup_path.exists():
        try:
            shutil.copy2(real, backup_path)
        except OSError as exc:
            raise TrustError(f"Cannot back up {real} to {backup_path}: {exc}") from None
        backup = backup_path

    for attempt in range(2):
        data = _read(target)
        projects = data.setdefault("projects", {})
        if not isinstance(projects, dict):
            raise TrustError(f"'projects' in {target} is not an object; refusing to touch it")
        for root in pending:
            entry = projects.setdefault(str(root), {})
            if not isinstance(entry, dict):
                raise TrustError(f"projects[{root}] in {target} is not an object; refusing to touch it")
            entry[KEY] = True
        try:
            _write_atomically(target, data)
        except OSError as exc:
            raise TrustError(f"Cannot write {target}: {exc}") from None
        if all(_is_trusted(_read(target), root) for root in pending):
            return TrustReport(target, results, backup)
        if attempt == 0:
            time.sleep(0.2)  # a concurrent Claude Code write replaced ours; apply once more
    raise TrustError(
        f"Could not record workspace trust in {target}: another process kept overwriting it. "
        "Close other Claude Code sessions and run `trellis trust` again."
    )


def explain_failure(error: TrustError, project_dir: Path) -> str:
    return (
        f"{error}. Headless sessions need the workspace trusted. Fix the file, or run `claude` once "
        f"in {project_dir} and accept the trust dialog."
    )
