"""A tiny but complete template tree, used to test the renderer without the real templates."""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST = """\
agent: ben
main: ben
guidance_dir: guidance
style_doc: prompt-src/STYLE.md

roles:
  - name: planner
    parts: planner
    frontmatter: planner/frontmatter.yml
  - name: general_advisor
    parts: advisor
    frontmatter: advisor/frontmatter.general.yml

required_shared:
  ben: [writing]
  planner: [writing, lookups, serena]
  advisor: [writing]

pointers:
  project_instructions: [ben, planner]
  runtime_guide: [ben]
  product_doc: [planner]

shared_guidance:
  - source: ../../shared/guide.md
    dest: testing/guide.md
  - source: ../../shared/browser.md
    dest: testing/browser.md
    flag: playwright

conditional_guidance:
  - path: guidance/design.md
    flag: design_authority

settings: ../../settings/ben.json
"""

SETTINGS = {
    "enableAllProjectMcpServers": True,
    "permissions": {
        "additionalDirectories": ["{{path:project_dir}}"],
        "deny": ["Bash(git push:*)"],
    },
    "hooks": {
        "PostToolUse": [
            {
                "matcher": "Agent",
                "hooks": [
                    {
                        "type": "command",
                        "command": "{{path:trellis_cmd}} hook register-subagent --agent ben --project {{path:project_dir}}",
                    }
                ],
            }
        ]
    },
}

FILES = {
    "agents/ben/manifest.yml": MANIFEST,
    "agents/ben/prompt-src/STYLE.md": "Style notes with {{if:...}} examples that are never rendered.\n",
    "agents/ben/prompt-src/ben/01-role.md": (
        "# Ben for {{config:project_name}}\n\n"
        "State lives in `{{path:state_dir}}`; guidance in `{{path:guidance:ben}}`.\n"
        "{{if:pre_production}}\nPre-production: no compatibility work.\n{{else}}\nProduction: keep compatibility.\n{{/if}}\n"
        "Branch prefix: {{config:git.branch_prefix}}\n"
    ),
    "agents/ben/prompt-src/ben/02-shared.md": "{{shared:writing}}\n",
    "agents/ben/prompt-src/planner/01-role.md": (
        "# Planner\n\nPlans for {{config:project_name}}.\n\n"
        "{{if:serena}}\n{{shared:serena}}\n{{else}}\n{{shared:lookups}}\n{{/if}}\n\n"
        "{{shared:writing}}\n"
    ),
    "agents/ben/prompt-src/planner/frontmatter.yml": (
        "name: planner\n"
        "description: Plans work for {{config:project_name}}.\n"
        "model: opus\n"
        "tools: Read, Bash{{if:serena}}, mcp__serena__find_symbol{{if:playwright}}, mcp__playwright{{/if}}{{/if}}\n"
        "{{if:playwright}}\nmcpServers:\n  - playwright\n{{/if}}"
    ),
    "agents/ben/prompt-src/advisor/01-role.md": "# Advisor\n\n{{shared:writing}}\n",
    "agents/ben/prompt-src/advisor/frontmatter.general.yml": "name: general_advisor\ndescription: Advises.\n",
    "agents/ben/prompt-src/_shared/writing.md": "Write plainly for {{config:project_name}}.",
    "agents/ben/prompt-src/_shared/serena.md": "Use Serena first.",
    "agents/ben/prompt-src/_shared/lookups.md": "Use grep for lookups.",
    "agents/ben/guidance/rules.md": "Rules for {{config:project_name}}; chat at {{path:handoff_chat}}.\n",
    "agents/ben/guidance/design.md": "Design rules: {{config:design_authority}}\n",
    "agents/ben/guidance/data.bin": "binary-ish {{not rendered}}",
    "shared/guide.md": "Shared guide for {{config:project_name}}.\n",
    "shared/browser.md": "Browser guide.\n",
}


def write_templates(root: Path) -> Path:
    """Create the fixture tree under ``root`` (the plugin root) and return the templates dir."""
    templates = root / "templates"
    for rel, text in FILES.items():
        path = templates / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    settings_path = templates / "settings" / "ben.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(SETTINGS, indent=2), encoding="utf-8")
    (root / "server").mkdir(exist_ok=True)
    (root / "server" / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    return templates


def write_project(root: Path, config_yaml: str | None = None, *, docs: bool = False) -> Path:
    project = root / "project"
    (project / ".trellis").mkdir(parents=True)
    (project / ".trellis" / "config.yml").write_text(
        config_yaml if config_yaml is not None else "project_name: Example\n", encoding="utf-8"
    )
    if docs:
        for name in ("AGENTS.md", "PRODUCT.md", "RUNTIME.md", "DESIGN.md"):
            (project / name).write_text(f"# {name}\n", encoding="utf-8")
    return project
