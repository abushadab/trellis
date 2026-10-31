from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(filepath: Path, content: str) -> None:
    """Atomically write UTF-8 text to a file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{filepath.name}.",
        suffix=".tmp",
        dir=str(filepath.parent),
        text=True,
    )
    temp_path = Path(temp_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, filepath)

        try:
            dir_fd = os.open(filepath.parent, os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except (OSError, AttributeError):
            # Some platforms/filesystems do not support directory fsync.
            pass
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise
