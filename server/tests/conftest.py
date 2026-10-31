from __future__ import annotations

import sys
from pathlib import Path

# Tests import helper modules (support, fake_claude) from this directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_claude_config(tmp_path, monkeypatch):
    """Never let a test read or write the real ~/.claude.json (workspace trust lives there)."""
    config_dir = tmp_path / "claude-config-isolated"
    config_dir.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))
