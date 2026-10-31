---
name: init
description: Set up Trellis (Sunny, Iris, Ben) in the current git project. Interviews the user, writes .trellis/config.yml, renders the agent folders and runs the health check.
disable-model-invocation: true
---

# /trellis:init

Set up Trellis in the project that Claude Code is running in. Work through the steps in order.
Keep the interview short: offer a detected default for every question and accept "ok" or "defaults".
Use the AskUserQuestion tool when it is available, otherwise ask in plain text. Ask related
questions together in one round.

The plugin lives at `${CLAUDE_PLUGIN_ROOT}`. Use that exact path wherever a command below needs it.

## 1. Prerequisites

Run these checks and report a one-line result for each:

```bash
git rev-parse --show-toplevel
command -v claude && claude --version
command -v uv; command -v uvx
command -v npx
```

- Not a git repository: stop and tell the user to run `git init` (or start Claude Code in the repo), then rerun.
- `claude` missing: stop. Trellis launches Iris and Ben with `claude -p`.
- `uv` or `uvx` missing: stop and point to https://docs.astral.sh/uv/ for installation.
- `npx` missing: continue. Playwright stays off in `auto` mode; say so.

Use the git top-level directory as the project directory. If `$PWD` is a subdirectory of it, ask whether
to set up at the top level instead (recommended) and `cd` there for the remaining commands.

## 2. Existing config

If `.trellis/config.yml` already exists, show its project name and stage and ask whether to keep it.
Never overwrite it without an explicit yes.

- Keep: skip steps 3 and 4 and go to step 5. (If the user only wants to re-render, `/trellis:update` does that.)
- Overwrite: copy the old file to `.trellis/config.yml.bak` first, then continue.

## 3. Interview

Detect defaults first (project name from the directory or repo name, which of `AGENTS.md` and `CLAUDE.md`
exist, likely docs such as `docs/`, `README.md`, a `Makefile` or `package.json` scripts). Then ask:

1. Project name (default: directory name).
2. Repo root, relative to the project directory (default: `.`).
3. Project instructions: which of `AGENTS.md` / `CLAUDE.md` exist (default: the ones that exist).
4. Optional, each can be "none":
   - Product doc: scope and product rules.
   - Runtime guide: how to run, test and seed the app locally.
   - Design authority: a UI spec or design lab path or URL. Setting it turns on the design review lens.
5. Stage: `pre_production` (default; no backward-compatibility work) or `production`.
6. Git: Ben's branch prefix (default `ben/`), working branch prefix (default `work/`), and the commit
   identity for agent commits (default: use git config; show the current `git config user.name` and
   `user.email`).
7. `commit_specs` (default yes): whether Iris commits specs and Ben commits plans.
8. Serena MCP (default off). If on, ask for its URL.
9. Playwright (default `auto`: on when `npx` exists).
10. Sunny autonomy (default `technical`: Sunny decides technical and process questions, product, safety and
    data go to the user; or `none`) and the usage threshold (default 75 percent of the 5-hour window).

Check that every doc path the user gives exists. A missing optional file is skipped by the renderer, but
warn the user so a typo is caught now.

## 4. Write the config

Read `${CLAUDE_PLUGIN_ROOT}/templates/config.example.yml`, apply the answers, and write
`.trellis/config.yml`. Keep the template's comments. Use YAML `null` for unset optional values.
Show the final file to the user.

## 5. Render and check

```bash
uvx --from "${CLAUDE_PLUGIN_ROOT}/server" trellis render --project "$PWD" --plugin-root "${CLAUDE_PLUGIN_ROOT}"
uvx --from "${CLAUDE_PLUGIN_ROOT}/server" trellis doctor --project "$PWD"
```

The first run downloads dependencies and can take a minute. On a render error (exit 2), show the message
and fix the config with the user; do not edit rendered files. Show the doctor output. Explain any
warning in plain English (missing `npx` means no Playwright; a missing docs file means it is skipped).

## 6. Trust the folders

Agents run from `.trellis/agents/{sunny,iris,ben}`. Claude Code applies a project's
`permissions.additionalDirectories` and allow rules only for a trusted folder. Facts to rely on:

- Trust is keyed on the git repository root, not on each subfolder. Trusting the project once covers
  all three agent folders.
- `claude -p` (how Sunny runs Iris and Ben) never shows a trust dialog. If the repository root has not
  been trusted, those sessions run without the project's `additionalDirectories` and allow rules, and
  stderr says "this workspace has not been trusted". So the root must be trusted once from an interactive
  session.
- Hooks and `.mcp.json` servers in the rendered folders work in `-p` regardless of trust.

Check the current state (read only):

```bash
python3 - "$(git rev-parse --show-toplevel)" <<'PY'
import json, os, sys
root = sys.argv[1]
cfg = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~"), ".claude.json")
try:
    projects = json.load(open(cfg)).get("projects", {})
except (OSError, ValueError):
    projects = {}
print("trusted" if projects.get(root, {}).get("hasTrustDialogAccepted") else "not trusted", root)
PY
```

If it prints `trusted`, say nothing more. If `not trusted`, recommend the safe route: start Sunny once
(step 7) and accept the trust dialog, which records trust for the repository root.

Only if the user explicitly prefers to skip the dialog, offer to set
`projects["<repo root>"].hasTrustDialogAccepted = true` in `~/.claude.json` yourself. Ask first, and
explain that it grants the repository's settings the same trust as accepting the dialog. If they agree:
copy the file to `~/.claude.json.trellis-backup`, change only that one key (create the project entry with
`{}` if missing, keep every other key), write to a temporary file in the same directory and rename it over
the original. Warn that a running Claude Code session may rewrite the file, so the change is best made
when no other session is open, and re-read the file afterward to confirm.

If `repo_root` in the config is a different git repository than the project directory, that repository
root needs the same trust.

## 7. Finish

Summarize in a few lines: what was written, the doctor result, and how to start:

```bash
cd .trellis/agents/sunny && claude
```

Tell the user:

- Accept the trust dialog the first time. Without it, `additionalDirectories` is ignored.
- Sunny is the only agent they talk to. It starts Iris and Ben itself.
- Suggest committing `.trellis/config.yml` and `.trellis/.gitignore`. Do not commit for them unless asked.
  Rendered agent folders and runtime state stay ignored, apart from specs and plans.
- After a plugin update or a config edit, run `/trellis:update`.

Never push, and never touch `.trellis/state/`.
