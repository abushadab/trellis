# trellis-mcp

The Python package behind Trellis: the per-agent MCP servers, the template renderer, the
subagent-registry hook and the `claude -p` turn runner. See `../DESIGN.md` for the contract.

Requires Python 3.11+. Linux and macOS only (it uses `fcntl` locks; the process-liveness
check in `claude_turn.py` uses `/proc` when present and a signal probe otherwise).

```bash
uvx --from <plugin_root>/server trellis --help      # how agents and skills call it
cd <plugin_root>/server && uv run --extra test pytest -q   # the test suite
```

## Commands

| Command | What it does |
| --- | --- |
| `trellis serve --agent {sunny,iris,ben} --project DIR` | stdio MCP server for one agent. The server is built in `main()`; importing the package starts nothing. Logs go to stderr only. |
| `trellis render --project DIR [--check] [--agent A ...] [--templates DIR] [--plugin-root DIR]` | Renders the templates into `DIR/.trellis/agents/`. `--check` writes nothing and exits 1 when any output is stale. Exit 2 is a render error. |
| `trellis hook register-subagent --agent A --project DIR` | PostToolUse hook on the `Agent` tool: reads the event on stdin, registers the subagent in `.trellis/state/registry.sqlite3`. Exit 2 (message on stderr) when registration fails. |
| `trellis doctor [--project DIR]` | Checks `claude`, `uv`, `git`, `npx`, the config, whether `trellis usage` can read an OAuth token, the rendered files and whether they match the templates. |
| `trellis wait --project DIR [--session ID ...] [--interval S] [--timeout S]` | Exits when a named session (or, with none named, any session running now) ends its turn. Prints `<session_id> Status: <Turn Status value>`. |
| `trellis usage --project DIR` | Prints 5-hour and 7-day utilization with reset times. Prints `usage: unavailable` (exit 0) when no OAuth token is readable. |
| `trellis watch-usage --project DIR [--threshold N] [--interval 300]` | Pauses the lowest-priority running session at the threshold and exits with `PAUSED ...`; exits with `RESET`, `IDLE ...` or `usage: unavailable` otherwise. |

The plugin root (the directory that holds `server/` and `templates/`) is found from
`--plugin-root`, else `$CLAUDE_PLUGIN_ROOT`, else the source checkout this package runs from.
An installed (non-editable) package cannot see the checkout, so skills pass
`--plugin-root "${CLAUDE_PLUGIN_ROOT}"`.

## Config keys beyond DESIGN section 3

`.trellis/config.yml` may also set:

```yaml
claude_projects_root: null     # where Claude Code keeps transcripts; default $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects
context_window_tokens: null    # null = 200000 for a subagent, 1000000 when its model id says [1m] or its usage already passed 200000
claude_executable: null        # null = `claude` on PATH; the session launcher runs this (tests point it at a fake)
```

Relative paths in `product_doc`, `runtime_guide`, `design_authority` and
`project_instructions` are read against `repo_root`; `repo_root` is read against the
project directory. A URL in `design_authority` is kept as written. Unknown top-level keys are
reported by `trellis doctor` and otherwise ignored.

## Template syntax

Implemented by `trellis_mcp/render.py` (DESIGN section 4).

- Parts: `prompt-src/<dir>/NN-*.md`, numbered consecutively from `01`, joined with a blank line.
- `{{shared:name}}` alone on a line expands `prompt-src/_shared/name.md`. A part may appear once per prompt.
- `{{config:key}}`, e.g. `{{config:project_name}}`, `{{config:git.branch_prefix}}`. Lists render
  comma-joined, paths render absolute, an unknown or unset key is an error (guard optional keys with a flag).
- `{{path:name}}`: `project_dir`, `repo_root`, `trellis_dir`, `state_dir`, `specflows_root`,
  `workitems_root`, `intents_root`, `handoff_chat`, `agent_root:<agent>`, `guidance:<agent>`, plus
  `plugin_root`, `server_dir` and `trellis_cmd` (`uvx --from <plugin_root>/server trellis`).
- `{{if:flag}} ... {{else}} ... {{/if}}`: nesting allowed, `{{if:!flag}}` negates, tags may sit inline in
  one line (frontmatter `tools:`). A tag that is alone on its line removes the whole line. Runs of blank
  lines in rendered Markdown are collapsed to one (not inside code fences).
- Flags: `serena`, `playwright`, `product_doc`, `runtime_guide`, `design_authority`,
  `reference_products`, `pre_production`, `commit_specs`, `git_identity` (needs both `git.commit_name`
  and `git.commit_email`). A document flag is true only when the document is configured and exists.
- Frontmatter files (`frontmatter*.yml`) and settings templates use the same syntax. The `models`
  config replaces the `model:` line of a role's frontmatter (or adds one) and sets `model` in the
  agent's settings. Settings values are JSON-escaped when substituted.

Order of evaluation for a prompt: conditionals, `{{shared:}}` expansion (required-part check), conditionals
again (inside shared parts), `{{config:}}`/`{{path:}}`, then the pointer sections. Anything that still looks
like `{{...}}` afterwards is an error.

## `templates/agents/<agent>/manifest.yml`

Every agent template directory needs one. Unknown keys are errors.

```yaml
agent: ben                      # must equal the directory name
main: ben                       # parts directory under prompt-src/ rendered to CLAUDE.md (default: agent)
guidance_dir: guidance          # directory under the agent template copied to .trellis/agents/<agent>/guidance/
style_doc: prompt-src/STYLE.md  # for editors only; never rendered

roles:                          # one entry per subagent, rendered to .claude/agents/<name>.md
  - name: planner               # the subagent name; must equal `name:` in the frontmatter file
    parts: planner              # parts directory under prompt-src/ (several roles may share one)
    frontmatter: planner/frontmatter.yml   # relative to prompt-src/

required_shared:                # parts directory -> shared parts it must include through {{shared:name}}
  planner: [writing, lookups]   # counted on the text before conditionals, so both branches of an
                                # {{if}}/{{else}} pair may be listed; only one may survive rendering

pointers:                       # pointer type -> prompts (main agent name or role names) that get the section
  project_instructions: [ben, planner]   # "Read <files> completely ..." for the files that exist
  runtime_guide: [ben]                   # only when runtime_guide is set and exists
  product_doc: [planner]                 # only when product_doc is set and exists
                                         # a missing type means no prompt gets it; `all` means every prompt

shared_guidance:                # templates/shared guides copied into the rendered guidance directory
  - source: ../../shared/dev-test-guide.md   # relative to this manifest's directory
    dest: testing/dev-test-guide.md          # relative to .trellis/agents/<agent>/guidance/
    flag: playwright                         # optional: skipped when the flag is off (`!flag` negates)

conditional_guidance:           # guidance files rendered only when the flag is on
  - path: guidance/spec-reviewer/design-conformance-lens.md   # relative to this manifest's directory
    flag: design_authority

settings: ../../settings/ben.json   # settings template (default: templates/settings/<agent>.json)
```

Outputs under `<project>/.trellis/agents/<agent>/`: `CLAUDE.md`, `.claude/agents/<name>.md`,
`.claude/settings.json` (from `settings`, with `permissions.additionalDirectories` set to the project
directory and `repo_root` when different), `.mcp.json` (the `trellis` server with `--agent`, and Serena when
`tools.serena` is on), `guidance/**` and `roles.json`. `roles.json` holds the manifest roles the hook does
not already know, so the hook registers them under their normalized slug. Role slugs are lowercase with
underscores: `spec-writer` and `spec_writer` are the same role. `render` also writes `.trellis/.gitignore`.
Files it no longer produces under `.claude/agents/` and `guidance/` are deleted; `settings.local.json` is never touched.

## MCP tools

All tools return absolute paths. Every agent also gets `register_subagent`, `check_subagent_slot`,
`check_subagent_context`.

- **ben**: `create_ben_workitem`, `create_ben_planner_assignment`, `create_ben_implementation_engineer_assignment`,
  `create_ben_investigator_assignment`, `handoff_ben_to_iris`, `append_ben_chat`, `count_ben_chats`,
  `read_ben_chats`, `append_handoff`, `count_handoffs`, `read_handoffs`.
- **sunny**: `create_sunny_intent`, `create_sunny_discovery_assignment`, `create_sunny_intent_writer_assignment`,
  `create_sunny_review_assignment`, `handoff_sunny_to_iris`, `append_sunny_chat`, `count_sunny_chats`,
  `read_sunny_chats`, `append_handoff`, `count_handoffs`, `read_handoffs`.
- **iris**: `create_specflow`, `create_{scout,research,advisor,spec_writer,spec_reviewer}_assignment`,
  `get_{scout,research,advisor,spec_writer,spec_reviewer}_assignment`, `append_chat`, `count_chats`,
  `read_chats`, `append_assignment_log`, `read_assignment_log`, `count_handoffs`, `read_handoffs`, `handoff_to_ben`.

Spec review lenses: `general`, `product`, `risk`, `overengineering`, and `design_conformance` (accepted only
when `design_authority` is set). Advisor primary lenses: `security_authority`, `runtime_implementability`,
`proportionality`, `cross_lens_reconciliation`.

Path arguments are absolute. The legacy forms relative to an agent's state directory
(`workitems/<id>/...`, `specflows/<id>/...`) are still accepted where the server validates a path
(`plan_output_path`, `implementation_summary_path`, the planner pointer, a previous spec output path).
Chat timestamps are ISO 8601 with the machine's local offset.

## Sessions (Sunny)

`start_session` runs `claude -p <prompt> --session-id <uuid> --output-format stream-json --verbose
--permission-mode bypassPermissions` from `.trellis/agents/<agent>/` with
`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` and stdin `/dev/null`; `resume_session` uses `--resume <id>`.
The process is detached (`start_new_session=True`, output in files) and outlives the MCP server. State is
`state/sunny/sessions/<id>.json` plus `<id>/turn-<n>.jsonl`. Status comes from the live PID (matched by
process start time, never by name) and the last `result` event of the stream; one run can emit several,
the last is final. `pause_session` sends SIGINT to that exact PID only.
