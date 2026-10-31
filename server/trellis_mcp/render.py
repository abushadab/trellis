"""Render the Trellis templates into a project (DESIGN sections 2, 4 and 8).

``templates/agents/<agent>/prompt-src`` becomes
``<project>/.trellis/agents/<agent>/CLAUDE.md`` plus ``.claude/agents/<role>.md``;
``guidance/`` is copied, ``templates/settings/<agent>.json`` becomes
``.claude/settings.json`` and ``.mcp.json`` is written for the agent.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import ConfigError, TrellisConfig, load_config
from .paths import AGENT_NAMES, GITIGNORE_TEXT, Paths


class RenderError(Exception):
    pass


PART_NAME = re.compile(r"^(?P<order>[0-9]{2})-.+\.md$")
SHARED_DIR = "_shared"
SHARED_PLACEHOLDER = re.compile(r"(?m)^\{\{shared:(?P<name>[a-z0-9-]+)\}\}[ \t]*$")
TAG = re.compile(r"\{\{(?P<tag>if:!?[a-z_]+|else|/if)\}\}")
VALUE_PLACEHOLDER = re.compile(r"\{\{(?P<kind>config|path):(?P<name>[A-Za-z0-9_.:-]+)\}\}")
LEFTOVER = re.compile(r"\{\{(?:shared|config|path|if|else|/if)\b[^}]*\}\}")
MANIFEST_KEYS = {
    "agent",
    "main",
    "guidance_dir",
    "style_doc",
    "roles",
    "required_shared",
    "pointers",
    "shared_guidance",
    "settings",
    "conditional_guidance",
}
POINTER_KEYS = ("project_instructions", "runtime_guide", "product_doc")
TEXT_SUFFIXES = {".md", ".txt", ".yml", ".yaml", ".json"}

Escape = Callable[[str], str]


def _identity(text: str) -> str:
    return text


def _json_escape(text: str) -> str:
    return json.dumps(text)[1:-1]


# -- plugin and template roots -------------------------------------------


def find_plugin_root(explicit: str | Path | None = None) -> Path:
    """The plugin root: explicit, then CLAUDE_PLUGIN_ROOT, then the source checkout."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))  # an explicit root is never second-guessed
    else:
        if os.environ.get("CLAUDE_PLUGIN_ROOT"):
            candidates.append(Path(os.environ["CLAUDE_PLUGIN_ROOT"]))
        candidates.append(Path(__file__).resolve().parents[2])
    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if (candidate / "templates").is_dir() and (candidate / "server" / "pyproject.toml").is_file():
            return candidate
    if explicit:
        raise RenderError(f"{Path(explicit)} is not a Trellis plugin root (no templates/ and server/)")
    raise RenderError(
        "Cannot find the Trellis plugin root. Pass --plugin-root <dir> (the directory that "
        "holds server/ and templates/)."
    )


# -- context --------------------------------------------------------------


@dataclass
class RenderContext:
    config: TrellisConfig
    plugin_root: Path
    templates_root: Path
    escape: Escape = _identity
    flags: dict[str, bool] = field(init=False)

    def __post_init__(self) -> None:
        self.flags = self.config.flags()

    @property
    def paths(self) -> Paths:
        return self.config.paths

    @property
    def server_dir(self) -> Path:
        return self.plugin_root / "server"

    @property
    def trellis_cmd(self) -> str:
        return f"uv run --quiet --project {shlex.quote(str(self.server_dir))} trellis"

    def with_escape(self, escape: Escape) -> RenderContext:
        clone = RenderContext(self.config, self.plugin_root, self.templates_root, escape)
        return clone

    def path_value(self, name: str) -> str:
        paths = self.paths
        if name == "repo_root":
            return str(self.config.repo_root)
        if name == "plugin_root":
            return str(self.plugin_root)
        if name == "server_dir":
            return str(self.server_dir)
        if name == "trellis_cmd":
            return self.trellis_cmd
        if ":" in name:
            kind, _, arg = name.partition(":")
            if kind in ("agent_root", "guidance") and arg in AGENT_NAMES:
                return str(paths.agent_root(arg) if kind == "agent_root" else paths.guidance_dir(arg))
            raise KeyError(name)
        return str(paths.named(name))


# -- template syntax -------------------------------------------------------


def _standalone_span(text: str, match: re.Match[str]) -> tuple[int, int]:
    """Span to delete for a tag: the whole line when the tag is alone on it."""
    start = text.rfind("\n", 0, match.start()) + 1
    end = text.find("\n", match.end())
    end = len(text) if end == -1 else end + 1
    line_before = text[start : match.start()]
    line_after = text[match.end() : end].rstrip("\n")
    if line_before.strip() == "" and line_after.strip() == "":
        return start, end
    return match.start(), match.end()


def process_conditionals(text: str, flags: dict[str, bool], where: str) -> str:
    """Evaluate ``{{if:flag}} ... {{else}} ... {{/if}}`` blocks (nesting allowed, ``!flag`` negates)."""
    out: list[str] = []
    stack: list[dict[str, Any]] = []
    cursor = 0

    def active() -> bool:
        return all(frame["on"] for frame in stack)

    for match in TAG.finditer(text):
        start, end = _standalone_span(text, match)
        if start < cursor:  # two tags on one already-consumed line
            start = match.start()
        if active():
            out.append(text[cursor:start])
        cursor = end
        tag = match.group("tag")
        if tag.startswith("if:"):
            name = tag[3:]
            negate = name.startswith("!")
            name = name.lstrip("!")
            if name not in flags:
                raise RenderError(f"{where}: unknown flag `{name}` (known: {', '.join(sorted(flags))})")
            value = flags[name] != negate
            stack.append(
                {"on": value, "cond": value, "else": False, "line": text.count("\n", 0, match.start()) + 1}
            )
        elif tag == "else":
            if not stack or stack[-1]["else"]:
                raise RenderError(f"{where}: `{{{{else}}}}` without a matching `{{{{if:...}}}}`")
            frame = stack[-1]
            frame["else"] = True
            frame["on"] = not frame["cond"]
        else:  # /if
            if not stack:
                raise RenderError(f"{where}: `{{{{/if}}}}` without a matching `{{{{if:...}}}}`")
            stack.pop()
    if stack:
        raise RenderError(f"{where}: `{{{{if:...}}}}` opened on line {stack[-1]['line']} is never closed")
    if active():
        out.append(text[cursor:])
    return "".join(out)


def substitute_values(text: str, ctx: RenderContext, where: str) -> str:
    def replace(match: re.Match[str]) -> str:
        kind, name = match.group("kind"), match.group("name")
        try:
            value = ctx.config.value(name) if kind == "config" else ctx.path_value(name)
        except KeyError as exc:
            raise RenderError(f"{where}: unknown or unset `{{{{{kind}:{name}}}}}` ({exc.args[0]})") from None
        return ctx.escape(value)

    return VALUE_PLACEHOLDER.sub(replace, text)


def check_leftovers(text: str, where: str) -> None:
    leftover = LEFTOVER.search(text)
    if leftover:
        raise RenderError(f"{where}: unresolved or malformed placeholder `{leftover.group(0)}`")


def tidy_blank_lines(text: str) -> str:
    """Collapse runs of blank lines to one, except inside fenced code blocks."""
    out: list[str] = []
    in_fence = False
    blank = False
    for line in text.split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        if not in_fence and not line.strip():
            if blank:
                continue
            blank = True
        else:
            blank = False
        out.append(line)
    return "\n".join(out)


def render_text(text: str, ctx: RenderContext, where: str) -> str:
    """Conditionals, then config/path values, for text that has no shared parts."""
    text = process_conditionals(text, ctx.flags, where)
    text = substitute_values(text, ctx, where)
    check_leftovers(text, where)
    return text


# -- manifest ---------------------------------------------------------------


@dataclass(frozen=True)
class RoleSpec:
    name: str  # subagent name; also the hook's subagent_type
    parts: str  # parts directory under prompt-src/
    frontmatter: str  # frontmatter file, relative to prompt-src/


@dataclass(frozen=True)
class SharedGuide:
    source: str  # relative to the manifest directory
    dest: str  # relative to the rendered guidance directory
    flag: str | None


@dataclass(frozen=True)
class Manifest:
    agent: str
    main: str
    guidance_dir: str
    roles: tuple[RoleSpec, ...]
    required_shared: dict[str, frozenset[str]]  # parts directory -> shared part names
    pointers: dict[str, frozenset[str] | None]  # pointer type -> target names (None = all)
    shared_guidance: tuple[SharedGuide, ...]
    conditional_guidance: dict[str, str]  # path relative to the manifest directory -> flag
    settings: str | None  # relative to the manifest directory


def load_manifest(agent_dir: Path, agent: str, flags: dict[str, bool] | None = None) -> Manifest:
    path = agent_dir / "manifest.yml"
    if not path.is_file():
        raise RenderError(f"Missing {path} (see server/README.md for the manifest schema)")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise RenderError(f"{path}: invalid YAML: {exc}") from None
    if not isinstance(data, dict):
        raise RenderError(f"{path}: must be a mapping")
    unknown = sorted(set(data) - MANIFEST_KEYS)
    if unknown:
        raise RenderError(f"{path}: unknown keys: {', '.join(unknown)}")
    if data.get("agent", agent) != agent:
        raise RenderError(f"{path}: `agent` must be `{agent}`")

    def name_list(value: Any, what: str) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            raise RenderError(f"{path}: {what} must be a list of names")
        return list(value)

    def entries(key: str, fields: tuple[str, ...]) -> list[dict[str, Any]]:
        value = data.get(key) or []
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise RenderError(f"{path}: {key} must be a list of mappings")
        for item in value:
            for field_name in fields:
                if not isinstance(item.get(field_name), str) or not item[field_name]:
                    raise RenderError(f"{path}: every {key} entry needs a `{field_name}` string")
        return value

    known_flags = set(flags or ())

    def check_flag(flag: Any, where: str) -> str | None:
        if flag is None:
            return None
        if not isinstance(flag, str) or (known_flags and flag.lstrip("!") not in known_flags):
            raise RenderError(f"{path}: {where} names an unknown flag `{flag}`")
        return flag

    roles = tuple(
        RoleSpec(r["name"], r["parts"], r["frontmatter"])
        for r in entries("roles", ("name", "parts", "frontmatter"))
    )
    if len({r.name for r in roles}) != len(roles):
        raise RenderError(f"{path}: duplicate role names")

    required: dict[str, frozenset[str]] = {}
    for key, value in (data.get("required_shared") or {}).items():
        required[str(key)] = frozenset(name_list(value, f"required_shared.{key}"))

    pointers: dict[str, frozenset[str] | None] = {}
    raw_pointers = data.get("pointers") or {}
    if not isinstance(raw_pointers, dict):
        raise RenderError(f"{path}: pointers must be a mapping")
    for key, value in raw_pointers.items():
        if key not in POINTER_KEYS:
            raise RenderError(f"{path}: pointers.{key} is not one of {', '.join(POINTER_KEYS)}")
        pointers[key] = None if value in ("all", "*") else frozenset(name_list(value, f"pointers.{key}"))

    shared_guidance = tuple(
        SharedGuide(e["source"], e["dest"], check_flag(e.get("flag"), "shared_guidance"))
        for e in entries("shared_guidance", ("source", "dest"))
    )
    conditional = {
        e["path"]: check_flag(e["flag"], "conditional_guidance")  # type: ignore[misc]
        for e in entries("conditional_guidance", ("path", "flag"))
    }
    settings = data.get("settings")
    if settings is not None and not isinstance(settings, str):
        raise RenderError(f"{path}: settings must be a path string")

    return Manifest(
        agent=agent,
        main=str(data.get("main") or agent),
        guidance_dir=str(data.get("guidance_dir") or "guidance"),
        roles=roles,
        required_shared=required,
        pointers=pointers,
        shared_guidance=shared_guidance,
        conditional_guidance=conditional,
        settings=settings,
    )


# -- prompts ----------------------------------------------------------------


def agent_name_from_frontmatter(text: str, source: Path) -> str:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RenderError(f"{source}: frontmatter is not valid YAML: {exc}") from None
    name = data.get("name") if isinstance(data, dict) else None
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise RenderError(f"{source} must declare `name: <agent>`")
    return name


@dataclass
class Target:
    name: str  # agent or subagent name
    parts_dir: Path
    output: Path
    frontmatter: str | None  # processed frontmatter text, or None for the main agent


def discover_targets(
    prompt_src: Path, manifest: Manifest, ctx: RenderContext, agent_root: Path
) -> list[Target]:
    main_dir = prompt_src / manifest.main
    if not main_dir.is_dir():
        raise RenderError(f"{prompt_src}: missing main parts directory `{manifest.main}`")
    targets = [Target(manifest.agent, main_dir, agent_root / "CLAUDE.md", None)]
    parts_dirs = {manifest.main}
    for role in manifest.roles:
        fm_file = prompt_src / role.frontmatter
        parts_dir = prompt_src / role.parts
        if not fm_file.is_file():
            raise RenderError(f"Role `{role.name}`: missing frontmatter {fm_file}")
        if not parts_dir.is_dir():
            raise RenderError(f"Role `{role.name}`: missing parts directory {parts_dir}")
        text = render_text(fm_file.read_text(encoding="utf-8"), ctx, str(fm_file)).strip()
        name = agent_name_from_frontmatter(text, fm_file)
        if name != role.name:
            raise RenderError(f"{fm_file} declares `name: {name}` but the manifest role is `{role.name}`")
        parts_dirs.add(role.parts)
        text = apply_model_override(text, ctx.config.models.get(name))
        targets.append(Target(name, parts_dir, agent_root / ".claude" / "agents" / f"{name}.md", text))

    actual = {
        p.name for p in prompt_src.iterdir() if p.is_dir() and p.name not in {SHARED_DIR, "__pycache__"}
    }
    missing = sorted(parts_dirs - actual)
    unexpected = sorted(actual - parts_dirs)
    if missing or unexpected:
        raise RenderError(
            f"Invalid prompt-src layout in {prompt_src} (missing: {missing or 'none'}; "
            f"directories not named by the manifest: {unexpected or 'none'})"
        )
    return targets


def apply_model_override(frontmatter: str, model: str | None) -> str:
    if not model:
        return frontmatter
    if re.search(r"(?m)^model:.*$", frontmatter):
        return re.sub(r"(?m)^model:.*$", lambda _m: f"model: {model}", frontmatter, count=1)
    return re.sub(r"(?m)^(name:.*)$", lambda m: f"{m.group(1)}\nmodel: {model}", frontmatter, count=1)


def load_shared_parts(prompt_src: Path) -> dict[str, str]:
    shared: dict[str, str] = {}
    for path in sorted((prompt_src / SHARED_DIR).glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise RenderError(f"Empty shared part: {path}")
        shared[path.stem] = text
    return shared


def merge_parts(parts_dir: Path) -> tuple[str, int]:
    files = sorted(parts_dir.glob("*.md"))
    invalid = [p.name for p in files if not PART_NAME.fullmatch(p.name)]
    if invalid:
        raise RenderError(f"Invalid part names in {parts_dir.name}: {', '.join(invalid)}")
    if not files:
        raise RenderError(f"No parts found in {parts_dir}")
    orders = [int(PART_NAME.fullmatch(p.name).group("order")) for p in files]  # type: ignore[union-attr]
    if orders != list(range(1, len(files) + 1)):
        raise RenderError(
            f"Parts for {parts_dir.name} must be numbered consecutively from 01; "
            f"found: {', '.join(f'{o:02d}' for o in orders)}"
        )
    sections = []
    for part in files:
        text = part.read_text(encoding="utf-8").strip()
        if not text:
            raise RenderError(f"Empty part: {part}")
        sections.append(text)
    return "\n\n".join(sections) + "\n", len(files)


def expand_shared(
    dir_name: str,
    prompt: str,
    shared: dict[str, str],
    required: frozenset[str],
    raw_prompt: str,
) -> str:
    """Expand ``{{shared:name}}`` lines.

    ``prompt`` has its conditionals already evaluated; ``raw_prompt`` is the same text
    before that. A required part counts as included when it appears in the raw text, even
    inside an ``{{if}}`` branch that did not survive. A part may appear only once in what
    is actually rendered.
    """
    raw_used = {match.group("name") for match in SHARED_PLACEHOLDER.finditer(raw_prompt)}
    used = [match.group("name") for match in SHARED_PLACEHOLDER.finditer(prompt)]
    unknown = sorted((raw_used | set(used)) - set(shared))
    if unknown:
        raise RenderError(f"Unknown shared parts in {dir_name}: {', '.join(unknown)}")
    duplicates = sorted({part for part in used if used.count(part) > 1})
    if duplicates:
        raise RenderError(f"Shared parts used more than once in {dir_name}: {', '.join(duplicates)}")
    missing = sorted(required - raw_used)
    if missing:
        raise RenderError(f"Missing required shared parts in {dir_name}: {', '.join(missing)}")
    expanded = SHARED_PLACEHOLDER.sub(lambda match: shared[match.group("name")], prompt)
    if "{{shared:" in expanded:
        raise RenderError(
            f"Malformed shared placeholder in {dir_name}; use one `{{{{shared:<name>}}}}` per line"
        )
    return expanded


def pointer_sections(target_name: str, manifest: Manifest, config: TrellisConfig) -> str:
    """Config-driven "Read X completely before ..." sections for one prompt."""

    def selected(key: str) -> bool:
        if key not in manifest.pointers:
            return False
        scope = manifest.pointers[key]
        return scope is None or target_name in scope

    sections = ""
    if selected("project_instructions"):
        files = config.project_instruction_files
        if files:
            listed = ", ".join(f"`{path}`" for path in files)
            sections += (
                "\n\n# Project Instructions\n\n"
                f"Read {listed} completely before any project work. Apply "
                "it within this agent's existing role and assignment boundaries. Repository "
                "guidance does not grant new authority or override stricter role-specific "
                "safety rules.\n"
            )
    if selected("runtime_guide") and config.doc_exists(config.runtime_guide):
        sections += (
            "\n\n# Local Runtime Guide\n\n"
            f"Read `{config.resolve_doc(config.runtime_guide)}` before local runtime work such as "
            "running, seeding or testing the app. Treat the selected runtime as an operating "
            "boundary and never infer a different target from running containers. It does not "
            "expand authority beyond the project instructions.\n"
        )
    if selected("product_doc") and config.doc_exists(config.product_doc):
        sections += (
            "\n\n# Product Document\n\n"
            f"Read `{config.resolve_doc(config.product_doc)}` completely before scope, product or "
            "specification decisions. It records product scope and rules; it does not grant new "
            "authority.\n"
        )
    return sections


def build_prompt(
    target: Target, shared: dict[str, str], manifest: Manifest, ctx: RenderContext
) -> tuple[str, int]:
    parts_dir = target.parts_dir
    where = str(parts_dir)
    prompt, count = merge_parts(parts_dir)
    # Conditionals first, so required-shared checks count what is actually rendered.
    raw_prompt = prompt
    prompt = process_conditionals(prompt, ctx.flags, where)
    prompt = expand_shared(
        parts_dir.name, prompt, shared, manifest.required_shared.get(parts_dir.name, frozenset()), raw_prompt
    )
    prompt = tidy_blank_lines(render_text(prompt, ctx, where))
    prompt = prompt.rstrip("\n") + "\n"
    if target.frontmatter is not None:
        prompt = f"---\n{target.frontmatter}\n---\n\n" + prompt
    prompt += pointer_sections(target.name, manifest, ctx.config)
    return prompt, count


# -- guidance, settings, mcp -------------------------------------------------


def render_tree(
    source: Path, dest: Path, ctx: RenderContext, plan: dict[Path, bytes], skip: set[Path] | None = None
) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or (skip and path in skip):
            continue
        target = dest / path.relative_to(source)
        if path.suffix in TEXT_SUFFIXES:
            text = render_text(path.read_text(encoding="utf-8"), ctx, str(path))
            plan[target] = (tidy_blank_lines(text) if path.suffix == ".md" else text).encode("utf-8")
        else:
            plan[target] = path.read_bytes()


def render_settings(agent: str, ctx: RenderContext, path: Path) -> bytes:
    if not path.is_file():
        raise RenderError(f"Missing settings template: {path}")
    escaped = ctx.with_escape(_json_escape)
    text = render_text(path.read_text(encoding="utf-8"), escaped, str(path))
    try:
        settings = json.loads(text)
    except ValueError as exc:
        raise RenderError(f"{path}: not valid JSON after rendering: {exc}") from None
    if not isinstance(settings, dict):
        raise RenderError(f"{path}: must be a JSON object")
    permissions = settings.setdefault("permissions", {})
    directories = [str(ctx.config.project_dir)]
    if ctx.config.repo_root != ctx.config.project_dir:
        directories.append(str(ctx.config.repo_root))
    for existing in permissions.get("additionalDirectories", []):
        if existing not in directories:
            directories.append(existing)
    permissions["additionalDirectories"] = directories
    model = ctx.config.models.get(agent)
    if model:
        settings["model"] = model
    return (json.dumps(settings, indent=2) + "\n").encode("utf-8")


def render_mcp_json(agent: str, ctx: RenderContext) -> bytes:
    servers: dict[str, Any] = {
        "trellis": {
            "command": "uv",
            "args": [
                "run",
                "--quiet",
                "--project",
                str(ctx.server_dir),
                "trellis",
                "serve",
                "--agent",
                agent,
                "--project",
                str(ctx.config.project_dir),
            ],
        }
    }
    if ctx.config.tools.serena:
        if not ctx.config.tools.serena_url:
            raise RenderError("tools.serena is true but tools.serena_url is not set")
        servers["serena"] = {"type": "http", "url": ctx.config.tools.serena_url}
    return (json.dumps({"mcpServers": servers}, indent=2) + "\n").encode("utf-8")


# -- orchestration -----------------------------------------------------------


@dataclass
class AgentPlan:
    agent: str
    files: dict[Path, bytes]
    owned_dirs: list[Path]
    summary: list[str]


def plan_agent(agent: str, ctx: RenderContext) -> AgentPlan:
    agent_src = ctx.templates_root / "agents" / agent
    manifest = load_manifest(agent_src, agent, ctx.flags)
    paths = ctx.paths
    agent_root = paths.agent_root(agent)
    prompt_src = agent_src / "prompt-src"
    if not prompt_src.is_dir():
        raise RenderError(f"Missing {prompt_src}")

    files: dict[Path, bytes] = {}
    summary: list[str] = []
    targets = discover_targets(prompt_src, manifest, ctx, agent_root)
    shared = load_shared_parts(prompt_src)
    for target in targets:
        prompt, count = build_prompt(target, shared, manifest, ctx)
        files[target.output] = prompt.encode("utf-8")
        summary.append(f"{target.name}: {count} parts, {len(prompt.split())} words")

    guidance_src = agent_src / manifest.guidance_dir
    guidance_out = paths.guidance_dir(agent)
    if guidance_src.is_dir():
        skip = set()
        for rel, flag in manifest.conditional_guidance.items():
            if not (ctx.flags[flag.lstrip("!")] != flag.startswith("!")):
                skip.add(agent_src / rel)
        render_tree(guidance_src, guidance_out, ctx, files, skip)
    for guide in manifest.shared_guidance:
        if guide.flag and ctx.flags[guide.flag.lstrip("!")] == guide.flag.startswith("!"):
            continue
        source = (agent_src / guide.source).resolve()
        if not source.is_file():
            raise RenderError(f"shared_guidance: missing {source}")
        dest = guidance_out / guide.dest
        if dest.suffix in TEXT_SUFFIXES:
            text = render_text(source.read_text(encoding="utf-8"), ctx, str(source))
            files[dest] = (tidy_blank_lines(text) if dest.suffix == ".md" else text).encode("utf-8")
        else:
            files[dest] = source.read_bytes()

    settings_path = (
        (agent_src / manifest.settings).resolve()
        if manifest.settings
        else ctx.templates_root / "settings" / f"{agent}.json"
    )
    files[agent_root / ".claude" / "settings.json"] = render_settings(agent, ctx, settings_path)
    files[agent_root / ".mcp.json"] = render_mcp_json(agent, ctx)
    # Roles the hook does not already know (see hook.DEFAULT_ROLES) map to their own slug.
    from .agent_registry import normalize_role
    from .hook import DEFAULT_ROLES

    known = DEFAULT_ROLES.get(agent, {})
    roles = {
        normalize_role(role.name): normalize_role(role.name)
        for role in manifest.roles
        if normalize_role(role.name) not in known
    }
    files[agent_root / "roles.json"] = (json.dumps(roles, indent=2, sort_keys=True) + "\n").encode("utf-8")

    owned = [agent_root / ".claude" / "agents", guidance_out]
    return AgentPlan(agent, files, owned, summary)


def available_agents(templates_root: Path) -> list[str]:
    root = templates_root / "agents"
    if not root.is_dir():
        raise RenderError(f"No agent templates at {root}")
    found = {p.name for p in root.iterdir() if p.is_dir()}
    ordered = [a for a in AGENT_NAMES if a in found]
    return ordered + sorted(found - set(AGENT_NAMES))


@dataclass
class RenderReport:
    written: list[Path] = field(default_factory=list)
    unchanged: list[Path] = field(default_factory=list)
    stale: list[Path] = field(default_factory=list)  # check mode: would change
    removed: list[Path] = field(default_factory=list)
    summaries: list[str] = field(default_factory=list)

    @property
    def is_current(self) -> bool:
        return not self.stale and not self.written and not self.removed


def render_project(
    project_dir: str | Path,
    *,
    plugin_root: str | Path | None = None,
    templates_root: str | Path | None = None,
    agents: list[str] | None = None,
    check: bool = False,
    config: TrellisConfig | None = None,
) -> RenderReport:
    try:
        config = config or load_config(project_dir)
    except ConfigError as exc:
        raise RenderError(str(exc)) from None
    root = find_plugin_root(plugin_root)
    templates = Path(templates_root).expanduser().resolve() if templates_root else root / "templates"
    if not templates.is_dir():
        raise RenderError(f"Templates directory not found: {templates}")
    ctx = RenderContext(config, root, templates)

    chosen = agents or available_agents(templates)
    unknown = sorted(set(chosen) - set(available_agents(templates)))
    if unknown:
        raise RenderError(f"No templates for: {', '.join(unknown)}")

    plans = [plan_agent(agent, ctx) for agent in chosen]
    gitignore = config.paths.trellis_dir / ".gitignore"
    all_files: dict[Path, bytes] = {gitignore: GITIGNORE_TEXT.encode("utf-8")}
    for plan in plans:
        all_files.update(plan.files)

    report = RenderReport()
    for plan in plans:
        report.summaries.extend(f"{plan.agent}/{line}" for line in plan.summary)
    for path, data in all_files.items():
        current = path.read_bytes() if path.is_file() else None
        if current == data:
            report.unchanged.append(path)
        elif check:
            report.stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            report.written.append(path)
    for plan in plans:
        for owned in plan.owned_dirs:
            if not owned.is_dir():
                continue
            for existing in sorted(owned.rglob("*")):
                if existing.is_file() and existing not in all_files:
                    if check:
                        report.stale.append(existing)
                    else:
                        existing.unlink()
                        report.removed.append(existing)
            if not check:
                for directory in sorted((d for d in owned.rglob("*") if d.is_dir()), reverse=True):
                    if not any(directory.iterdir()):
                        shutil.rmtree(directory)
    return report
