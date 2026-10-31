"""Helpers shared by the Ben, Iris, Sunny and handoff transports.

The four transports keep their own validators and tool surface; everything
that was copy-pasted between them (chat parsing, header rendering, locking,
path containment, id rules) lives here.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .chat_io import atomic_write_text
from .timeutil import now_iso

try:  # Unix only; documented in the README.
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

WORKFLOW_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,120}$")
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")
CHAT_HEADER_RE = re.compile(r"^\*\*(.+?)\s+-\s+(.+?)\*\*$")

WORKFLOW_ID_PATTERN = "^[a-z0-9][a-z0-9-]{1,120}$"
TASK_ID_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$"


def validate_workflow_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not WORKFLOW_ID_RE.fullmatch(value):
        raise ValueError(f"{field} must match {WORKFLOW_ID_PATTERN}")


def validate_task_id(task_id: str) -> None:
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise ValueError(f"task_id must match {TASK_ID_PATTERN}")


def render_author_line(author: str) -> str:
    return f"**{author} - {now_iso()}**"


@contextmanager
def file_lock(lock_path: Path) -> Iterator[None]:
    """Hold an exclusive cross-process lock on ``lock_path`` for the block."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def parse_chat_messages(chat_md: str) -> list[dict[str, Any]]:
    lines = chat_md.splitlines()
    starts: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        match = CHAT_HEADER_RE.match(line)
        if match:
            starts.append(
                {
                    "line": index,
                    "author": match.group(1).strip(),
                    "timestamp": match.group(2).strip(),
                }
            )

    messages: list[dict[str, Any]] = []
    for offset, start in enumerate(starts):
        start_line = int(start["line"])
        end_line = int(starts[offset + 1]["line"]) if offset + 1 < len(starts) else len(lines)
        body_lines = lines[start_line + 1 : end_line]
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and body_lines[0].strip() == "---":
            body_lines.pop(0)
            while body_lines and not body_lines[0].strip():
                body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        while body_lines and body_lines[-1].strip() == "---":
            body_lines.pop()
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()
        messages.append(
            {
                "index": offset + 1,
                "author": start["author"],
                "timestamp": start["timestamp"],
                "content": "\n".join(body_lines).strip(),
            }
        )
    return messages


def validate_read_args(count: int, start: int | None, end: int | None) -> bool:
    """Validate ``read_*`` arguments. Returns True when a range was requested."""
    range_mode = start is not None or end is not None
    if range_mode:
        if count != 5:
            raise ValueError("count cannot be mixed with start/end")
        if start is None or end is None:
            raise ValueError("start and end must be provided together")
        if start < 1:
            raise ValueError("start must be >= 1")
        if end < start:
            raise ValueError("end must be >= start")
    elif count < 1:
        raise ValueError("count must be >= 1")
    return range_mode


def select_messages(
    messages: list[dict[str, Any]], count: int, start: int | None, end: int | None
) -> dict[str, Any]:
    """Pick recent or ranged messages and describe the selection."""
    if start is not None or end is not None:
        selected = [m for m in messages if start <= m["index"] <= end]  # type: ignore[operator]
        mode, first, last = "range", start, end
    else:
        selected = messages[-count:]
        mode = "recent"
        first = selected[0]["index"] if selected else None
        last = selected[-1]["index"] if selected else None
    return {
        "mode": mode,
        "start": first,
        "end": last,
        "count": len(messages),
        "returned": len(selected),
        "messages": selected,
    }


def append_chat_unlocked(chat_path: Path, author: str, message: str, *, noun: str) -> None:
    """Append one timestamped entry. The caller holds the lock; ``noun`` names the file kind."""
    existing = read_required(chat_path, noun)
    rendered = f"{render_author_line(author)}\n\n{message.strip()}"
    atomic_write_text(chat_path, existing.rstrip() + f"\n\n---\n\n{rendered}\n")


def read_required(path: Path, noun: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing {noun} file: {path.name}")
    if path.is_symlink():
        raise ValueError(f"{noun} file must not be a symlink: {path.name}")
    return path.read_text(encoding="utf-8")


def scope_sections(scope_body: str) -> dict[str, str]:
    body = scope_body.strip()
    match = re.match(
        r"(?s)^(?P<description>.*?)(?:\s+Goal:\s*(?P<goal>.*?))?(?:\s+Scope:\s*(?P<scope>.*))?$",
        body,
    )
    if not match:
        return {"description": body, "goal": "", "scope": ""}
    return {
        "description": (match.group("description") or "").strip(),
        "goal": (match.group("goal") or "").strip(),
        "scope": (match.group("scope") or "").strip(),
    }


def chat_header_markdown(
    *,
    id_label: str,
    id_value: str,
    title: str,
    scope_body: str,
    project_name: str,
    project_root: Path,
) -> str:
    sections = scope_sections(scope_body)
    goal = f"\n\n**Goal:** {sections['goal']}" if sections["goal"] else ""
    scope = f"\n\n**Scope:** {sections['scope']}" if sections["scope"] else ""
    return f"""# Chat

**{id_label}:** {id_value}
**Title:** {title}
**Project:** {project_name}
**Project root:** `{project_root}`

**Description:** {sections["description"]}{goal}{scope}

---
"""


class WorkflowStore:
    """A directory of ``<id>/`` workflow folders (workitems, specflows or intents)."""

    def __init__(self, label: str, id_label: str, root_getter) -> None:
        self.label = label  # e.g. "Ben workitem"
        self.id_label = id_label  # e.g. "workitem_id"
        self._root_getter = root_getter

    @property
    def root(self) -> Path:
        return Path(self._root_getter()).expanduser()

    def validate_id(self, value: str) -> None:
        validate_workflow_id(value, self.id_label)

    def dir(self, workflow_id: str) -> Path:
        self.validate_id(workflow_id)
        root = self.root
        path = root / workflow_id
        resolved = path.resolve()
        root_resolved = root.resolve()
        if root_resolved not in resolved.parents and resolved != root_resolved:
            raise ValueError(f"Invalid {self.label} path")
        return path

    def file(self, directory: Path, filename: str) -> Path:
        path = directory / filename
        if path.exists() and path.is_symlink():
            raise ValueError(f"{self.label} file must not be a symlink: {filename}")
        return path

    def child_dir(self, directory: Path, *parts: str) -> Path:
        path = directory.joinpath(*parts)
        resolved = path.resolve()
        base = directory.resolve()
        if base not in resolved.parents and resolved != base:
            raise ValueError(f"Invalid {self.label} child path")
        if path.exists() and path.is_symlink():
            raise ValueError(f"{self.label} child path must not be a symlink: {'/'.join(parts)}")
        return path

    def require_files(self, directory: Path) -> None:
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"{self.label} does not exist: {directory.name}")
        path = self.file(directory, "chat.md")
        if not path.exists():
            raise FileNotFoundError(f"Missing {self.label} file: chat.md")
        if not path.is_file():
            raise ValueError(f"{self.label} path is not a file: chat.md")

    def read_required(self, path: Path) -> str:
        return read_required(path, self.label)

    def append_chat(self, chat_path: Path, author: str, message: str) -> None:
        append_chat_unlocked(chat_path, author, message, noun=self.label)

    def lock(self, workflow_id: str):
        self.validate_id(workflow_id)
        return file_lock(self.root / ".locks" / f"{workflow_id}.lock")

    def create(
        self,
        workflow_id: str,
        files: dict[str, str],
        subdirs: tuple[str, ...] = (),
    ) -> Path:
        """Create ``<root>/<id>/`` atomically under the lock; the caller holds no lock."""
        with self.lock(workflow_id):
            root = self.root
            root.mkdir(parents=True, exist_ok=True)
            target = self.dir(workflow_id)
            if target.exists():
                raise FileExistsError(f"{self.label} already exists: {workflow_id}")
            temp_dir = root / f".{workflow_id}.tmp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True)
            try:
                for name, text in files.items():
                    atomic_write_text(temp_dir / name, text)
                for dirname in subdirs:
                    (temp_dir / dirname).mkdir()
                temp_dir.rename(target)
            except Exception:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                raise
        return target


def listing(directory: Path) -> dict[str, list[str]]:
    return {
        "created_files": sorted(str(item.name) for item in directory.iterdir() if item.is_file()),
        "created_dirs": sorted(str(item.name) for item in directory.iterdir() if item.is_dir()),
    }


def abs_ref(value: str, base: Path) -> Path:
    """Normalize a path argument: absolute stays, a relative one is read against ``base``.

    Symlinks are deliberately not resolved; callers compare the lexical form
    with the canonical location and reject symlinks separately.
    """
    import os

    path = Path(value.strip().strip("`"))
    if ".." in path.parts:
        raise ValueError(f"path must not contain '..': {value.strip()}")
    if not path.is_absolute():
        path = base / path
    return Path(os.path.normpath(path))
