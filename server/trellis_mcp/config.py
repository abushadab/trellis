"""Load and validate ``<project>/.trellis/config.yml`` (DESIGN section 3)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .paths import Paths

STAGES = ("pre_production", "production")
PLAYWRIGHT_MODES = ("auto", "true", "false")
AUTONOMY_MODES = ("technical", "none")

KNOWN_KEYS = {
    "project_name",
    "repo_root",
    "project_instructions",
    "product_doc",
    "runtime_guide",
    "design_authority",
    "reference_products",
    "stage",
    "git",
    "commit_specs",
    "tools",
    "models",
    "sunny",
    "claude_projects_root",
    "context_window_tokens",
}


class ConfigError(ValueError):
    """The project's config file is missing or invalid."""


@dataclass(frozen=True)
class GitConfig:
    branch_prefix: str = "ben/"
    work_branch_prefix: str = "work/"
    commit_name: str | None = None
    commit_email: str | None = None


@dataclass(frozen=True)
class ToolsConfig:
    serena: bool = False
    serena_url: str | None = None
    playwright: str = "auto"  # auto | true | false


@dataclass(frozen=True)
class SunnyConfig:
    autonomy: str = "technical"
    usage_threshold: int = 75


@dataclass(frozen=True)
class TrellisConfig:
    project_dir: Path
    project_name: str
    repo_root: Path
    project_instructions: tuple[str, ...] = ("AGENTS.md", "CLAUDE.md")
    product_doc: str | None = None
    runtime_guide: str | None = None
    design_authority: str | None = None
    reference_products: tuple[str, ...] = ()
    stage: str = "pre_production"
    git: GitConfig = field(default_factory=GitConfig)
    commit_specs: bool = True
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    models: dict[str, str] = field(default_factory=dict)
    sunny: SunnyConfig = field(default_factory=SunnyConfig)
    claude_projects_root: Path | None = None
    context_window_tokens: int | None = None
    unknown_keys: tuple[str, ...] = ()

    # -- derived views -------------------------------------------------

    @property
    def paths(self) -> Paths:
        return Paths(self.project_dir)

    def resolve_doc(self, value: str | None) -> str | None:
        """Absolute path (or untouched URL) for a configured document."""
        if value is None:
            return None
        if "://" in value:
            return value
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.repo_root / path
        return str(path)

    @property
    def project_instruction_files(self) -> list[Path]:
        """Configured project instruction files that exist, as absolute paths."""
        found = []
        for name in self.project_instructions:
            resolved = self.resolve_doc(name)
            if resolved and Path(resolved).is_file():
                found.append(Path(resolved))
        return found

    def doc_exists(self, value: str | None) -> bool:
        resolved = self.resolve_doc(value)
        if resolved is None:
            return False
        return "://" in resolved or Path(resolved).exists()

    @property
    def playwright_enabled(self) -> bool:
        mode = self.tools.playwright
        if mode == "true":
            return True
        if mode == "false":
            return False
        return shutil.which("npx") is not None

    @property
    def git_identity(self) -> bool:
        return bool(self.git.commit_name and self.git.commit_email)

    def flags(self) -> dict[str, bool]:
        return {
            "serena": self.tools.serena,
            "playwright": self.playwright_enabled,
            "product_doc": self.doc_exists(self.product_doc),
            "runtime_guide": self.doc_exists(self.runtime_guide),
            "design_authority": self.doc_exists(self.design_authority),
            "reference_products": bool(self.reference_products),
            "pre_production": self.stage == "pre_production",
            "commit_specs": self.commit_specs,
            "git_identity": self.git_identity,
        }

    def value(self, key: str) -> str:
        """Text for ``{{config:key}}``. Raises ``KeyError`` for unknown or unset keys."""
        node: Any = {
            "project_name": self.project_name,
            "repo_root": str(self.repo_root),
            "project_instructions": [str(p) for p in self.project_instruction_files],
            "product_doc": self.resolve_doc(self.product_doc),
            "runtime_guide": self.resolve_doc(self.runtime_guide),
            "design_authority": self.resolve_doc(self.design_authority),
            "reference_products": list(self.reference_products),
            "stage": self.stage,
            "commit_specs": self.commit_specs,
            "git": {
                "branch_prefix": self.git.branch_prefix,
                "work_branch_prefix": self.git.work_branch_prefix,
                "commit_name": self.git.commit_name,
                "commit_email": self.git.commit_email,
            },
            "tools": {
                "serena": self.tools.serena,
                "serena_url": self.tools.serena_url,
                "playwright": self.tools.playwright,
            },
            "models": dict(self.models),
            "sunny": {
                "autonomy": self.sunny.autonomy,
                "usage_threshold": self.sunny.usage_threshold,
            },
        }
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                raise KeyError(key)
            node = node[part]
        if node is None:
            raise KeyError(f"{key} (not set; guard it with a flag)")
        if isinstance(node, bool):
            return "true" if node else "false"
        if isinstance(node, (list, tuple)):
            return ", ".join(str(item) for item in node)
        if isinstance(node, dict):
            raise KeyError(f"{key} (a mapping; name one of its keys)")
        return str(node)


# -- loading --------------------------------------------------------------


def _expect(cond: bool, message: str) -> None:
    if not cond:
        raise ConfigError(message)


def _opt_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    _expect(isinstance(value, str) and value.strip() != "", f"{key} must be a non-empty string or null")
    return value.strip()


def _str_list(data: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if key not in data or data[key] is None:
        return default if key not in data else ()
    value = data[key]
    _expect(
        isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value),
        f"{key} must be a list of non-empty strings",
    )
    return tuple(item.strip() for item in value)


def _mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    _expect(isinstance(value, dict), f"{key} must be a mapping")
    return value


def parse_config(data: Any, project_dir: Path) -> TrellisConfig:
    _expect(isinstance(data, dict), "config.yml must contain a mapping at the top level")
    project_dir = Path(project_dir).expanduser().resolve()

    name = data.get("project_name")
    _expect(isinstance(name, str) and name.strip() != "", "project_name is required (a non-empty string)")

    repo_root_raw = data.get("repo_root", ".")
    _expect(isinstance(repo_root_raw, str) and repo_root_raw.strip() != "", "repo_root must be a path string")
    repo_root = Path(repo_root_raw).expanduser()
    repo_root = (repo_root if repo_root.is_absolute() else project_dir / repo_root).resolve()

    stage = data.get("stage", "pre_production")
    _expect(stage in STAGES, f"stage must be one of: {', '.join(STAGES)}")

    git_raw = _mapping(data, "git")
    git_defaults = GitConfig()
    git = GitConfig(
        branch_prefix=_prefix(git_raw, "branch_prefix", git_defaults.branch_prefix),
        work_branch_prefix=_prefix(git_raw, "work_branch_prefix", git_defaults.work_branch_prefix),
        commit_name=_opt_str(git_raw, "commit_name"),
        commit_email=_opt_str(git_raw, "commit_email"),
    )

    tools_raw = _mapping(data, "tools")
    playwright = tools_raw.get("playwright", "auto")
    if isinstance(playwright, bool):
        playwright = "true" if playwright else "false"
    _expect(playwright in PLAYWRIGHT_MODES, "tools.playwright must be auto, true or false")
    serena = tools_raw.get("serena", False)
    _expect(isinstance(serena, bool), "tools.serena must be true or false")
    serena_url = _opt_str(tools_raw, "serena_url")
    tools = ToolsConfig(serena=serena, serena_url=serena_url, playwright=str(playwright))

    sunny_raw = _mapping(data, "sunny")
    autonomy = sunny_raw.get("autonomy", "technical")
    _expect(autonomy in AUTONOMY_MODES, "sunny.autonomy must be technical or none")
    threshold = sunny_raw.get("usage_threshold", 75)
    _expect(
        isinstance(threshold, int) and not isinstance(threshold, bool) and 1 <= threshold <= 100,
        "sunny.usage_threshold must be an integer from 1 to 100",
    )

    models_raw = _mapping(data, "models")
    _expect(
        all(isinstance(k, str) and isinstance(v, str) and v for k, v in models_raw.items()),
        "models must map role names to model names",
    )

    commit_specs = data.get("commit_specs", True)
    _expect(isinstance(commit_specs, bool), "commit_specs must be true or false")

    window = data.get("context_window_tokens")
    _expect(
        window is None or (isinstance(window, int) and not isinstance(window, bool) and window >= 1000),
        "context_window_tokens must be an integer of at least 1000, or null",
    )
    projects_raw = data.get("claude_projects_root")
    _expect(
        projects_raw is None or isinstance(projects_raw, str),
        "claude_projects_root must be a path string or null",
    )

    return TrellisConfig(
        project_dir=project_dir,
        project_name=name.strip(),
        repo_root=repo_root,
        project_instructions=_str_list(data, "project_instructions", ("AGENTS.md", "CLAUDE.md")),
        product_doc=_opt_str(data, "product_doc"),
        runtime_guide=_opt_str(data, "runtime_guide"),
        design_authority=_opt_str(data, "design_authority"),
        reference_products=_str_list(data, "reference_products", ()),
        stage=stage,
        git=git,
        commit_specs=commit_specs,
        tools=tools,
        models=dict(models_raw),
        sunny=SunnyConfig(autonomy=autonomy, usage_threshold=threshold),
        claude_projects_root=Path(projects_raw).expanduser() if projects_raw else None,
        context_window_tokens=window,
        unknown_keys=tuple(sorted(str(k) for k in data if k not in KNOWN_KEYS)),
    )


def _prefix(raw: dict[str, Any], key: str, default: str) -> str:
    value = raw.get(key, default)
    _expect(isinstance(value, str) and value != "", f"git.{key} must be a non-empty string")
    return value


def load_config(project_dir: str | Path) -> TrellisConfig:
    project = Path(project_dir).expanduser().resolve()
    path = Paths(project).config_path
    if not path.is_file():
        raise ConfigError(f"No Trellis config at {path}. Run /trellis:init first.")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"Cannot read {path}: {exc}") from exc
    try:
        return parse_config(data if data is not None else {}, project)
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from None


def default_claude_projects_root() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base).expanduser() if base else Path.home() / ".claude") / "projects"
