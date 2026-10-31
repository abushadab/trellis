# Trellis design contract

Trellis is a project-agnostic Claude Code plugin that installs a three-agent workflow into any repository:

- **Sunny**: the front agent. The user talks to Sunny in an interactive `claude` session. Sunny clarifies intent, launches and resumes Iris and Ben as headless `claude -p` sessions, answers their routine questions, brings product, safety and data decisions to the user, and runs the usage watcher.
- **Iris** (formerly Theo): the specification orchestrator. Scouting, research, advisors, assignment engineer and reviewer, spec writer and reviewer. Produces Ben-ready single specs.
- **Ben**: the execution orchestrator. Planner, plan reviewer, investigator, implementation engineer, implementation reviewer, independent final validator.

The workflow was proven on a real project. **Trim project facts, never roles, gates or format rules.** This document is the contract every builder follows. If something here is wrong, say so in your final report; do not silently diverge.

Sources being ported (read-only, never edit):

- prompts: `/home/abu/project-attestara/claude-workspace/` (`agents/ben`, `agents/theo`, `hooks/`, `testing/`, `tools/playwright-mcp`)
- MCP server: `/home/abu/project-attestara/attestara-workflow/`
- inventories: `/tmp/claude-1000/-home-abu-project-attestara/52a6ee96-e6f9-4ed8-901e-cd145e40b7e8/scratchpad/inventory/{mcp-server,ben-prompts,theo-prompts}.md`

No Attestara, Probo, KI-Quadrat, `ghki`, `ai2.at`, `/home/abu`, port numbers or Bangladesh time may remain in this repo, except in `DESIGN.md`'s source list above.

## 1. Repository layout (`/home/abu/trellis`)

```text
.claude-plugin/marketplace.json     # marketplace "trellis"; one plugin, source "./"
.claude-plugin/plugin.json          # plugin "trellis"
skills/init/SKILL.md                # /trellis:init
skills/update/SKILL.md              # /trellis:update (re-render after plugin or config change)
server/                             # Python package (pyproject.toml, uv-compatible)
  pyproject.toml                    # package "trellis-mcp", console script "trellis"
  trellis_mcp/...                   # MCP server, renderer, hook, launcher, usage watcher
  tests/
templates/
  config.example.yml
  agents/ben/prompt-src/...         # Ben + subagent parts (from claude-workspace agents/ben/prompt-src)
  agents/ben/guidance/...
  agents/iris/prompt-src/...
  agents/iris/guidance/...
  agents/sunny/prompt-src/...
  shared/                           # testing guides, browser guide templates
  settings/                         # settings.json templates per agent
tests/                              # prompt contract tests (run against rendered output)
README.md  LICENSE (MIT, "Abu Shadab")  DESIGN.md
```

The `trellis` CLI (console script) has subcommands:

- `trellis serve --agent {sunny,iris,ben} --project <dir>`: stdio MCP server for that agent's toolset (shared handoff tools and registry tools included in each).
- `trellis render --project <dir> [--check]`: reads `<dir>/.trellis/config.yml`, renders templates into `<dir>/.trellis/agents/`.
- `trellis hook register-subagent --agent <name> --project <dir>`: PostToolUse hook (stdin JSON). Stdlib + package only.
- `trellis doctor --project <dir>`: checks claude, uv, git, config, rendered files, optional tools.
- Sunny launcher/usage subcommands: defined in phase B.

Agents invoke it as `uvx --from <plugin_root>/server trellis ...`. `render` writes the absolute plugin root into rendered `.mcp.json` and settings hook commands; rendered files are per-machine and gitignored.

## 2. Target project layout

```text
<project>/.trellis/
  config.yml                        # committed
  .gitignore                        # written by init (see below)
  agents/{sunny,iris,ben}/          # rendered; gitignored; cwd for each agent session
    CLAUDE.md
    .claude/settings.json
    .claude/agents/<role>.md
    .mcp.json
    guidance/...
  state/                            # MCP runtime state; gitignored except specs and plans
    registry.sqlite3
    handoffs/chat.md
    sunny/intents/<intent-id>/...
    sunny/sessions/                 # launcher records (phase B)
    iris/specflows/<specflow-id>/...   # specs/ committed
    ben/workitems/<workitem-id>/...    # plans/ committed
```

`.trellis/.gitignore` ignores `agents/` and `state/` except `state/iris/specflows/*/specs/**` and `state/ben/workitems/*/plans/**`, plus `**/settings.local.json`.

Every path the MCP server returns, and every path an agent writes into a chat, brief or packet, is **absolute**. Agent-root-relative paths are gone.

## 3. Config (`.trellis/config.yml`)

```yaml
project_name: Example             # required
repo_root: .                      # relative to project dir; the code repo
project_instructions: [AGENTS.md, CLAUDE.md]   # every role reads the ones that exist
product_doc: null                 # optional path: product scope and rules
runtime_guide: null               # optional path: how to run, test, seed the app locally
design_authority: null            # optional path/URL: UI spec or design lab (enables design rules + design_conformance lens)
reference_products: []            # optional names; behavior research only, never copy code/text/assets
stage: pre_production             # pre_production | production (pre_production: no backward-compat work)
git:
  branch_prefix: ben/             # Ben's integration branch per workitem
  work_branch_prefix: work/       # engineer working branch
  commit_name: null               # null = use git config
  commit_email: null
commit_specs: true                # Iris spec writer commits specs; Ben planner commits plans
tools:
  serena: false                   # true = Serena MCP at serena_url
  serena_url: null
  playwright: auto                # auto | true | false; auto = enable if npx exists
models: {}                        # optional per-role overrides, e.g. {implementation_engineer: sonnet}
sunny:
  autonomy: technical             # technical (Sunny decides technical/process; product/safety/data go to user) | none (everything to user)
  usage_threshold: 75             # percent of the 5-hour window; pause lowest-priority session
```

## 4. Template syntax (renderer)

Existing `build.py` rules stay: numbered parts `NN-*.md` concatenate, `{{shared:name}}` expands `_shared/name.md`, `frontmatter*.yml` gives subagent frontmatter, `REQUIRED_SHARED` checks. Added:

- `{{config:key}}` / `{{config:git.branch_prefix}}`: value from config (paths rendered absolute). Unknown key = render error.
- `{{path:name}}`: computed absolute paths: `project_dir`, `repo_root`, `trellis_dir`, `state_dir`, `agent_root:<agent>`, `specflows_root`, `workitems_root`, `intents_root`, `handoff_chat`, `guidance:<agent>`.
- `{{if:flag}} ... {{/if}}` (may span lines; no nesting needed but allowed; `{{else}}` allowed). Flags: `serena`, `playwright`, `product_doc`, `runtime_guide`, `design_authority`, `reference_products`, `pre_production`, `commit_specs`, `git_identity`.
- Frontmatter may use flags too (e.g. `mcpServers` Playwright only `{{if:playwright}}`).
- Pointer sections ("Read X completely before ...") are emitted from config: `project_instructions` (all roles), `runtime_guide` (Ben, engineer, reviewer, validator, investigator), `product_doc` (orchestrators and spec roles). Missing optional files are skipped, not errors.

Subagents keep `omitClaudeMd: true`; the project-instructions pointer replaces it.

## 5. Names and renames

| Old | New |
| --- | --- |
| Theo | Iris (`orchestrator: iris`, `agents/iris`, `guidance/iris`, `prompt-src/iris`) |
| MCP server `aw`, `mcp__aw__*` | `trellis`, `mcp__trellis__*` |
| `handoff_ben_to_theo` | `handoff_ben_to_iris` |
| `handoff_sunny_to_theo` | `handoff_sunny_to_iris` |
| status `approved_for_theo` | `approved_for_iris` |
| lens `mvp_oss_proportionality` | `proportionality` |
| lens `mvp_scope_overengineering` | `overengineering` |
| lens `design_conformance` | unchanged, only valid when `design_authority` is set |
| `/mcp/<agent>` HTTP endpoints | `trellis serve --agent <agent>` (stdio) |

`specflow`, `workitem`, `intent`, the `AC-n` tables, single/master spec headings, plan rules, `## Completion Claim Map` (six columns, full 40-char SHA, verdict `met|preserved|deferred`), and every other validator format stay exactly as they are.

Subagent names stay bare (`planner`, `spec-writer`, ...) because they are rendered into each agent's `.claude/agents/`, not shipped as plugin agents.

## 6. Dropped for v1

Parallel lanes and integrator, Ada and `agent_loop*` (mine its routing rules for Sunny first), the Command Code / external implementation engineer (`implementation_engineer*.py` backends, `engineer_backends/`, `commandcode/`, the six `start/wait/answer/check_context/continue/stop_implementation_engineer` tools, the `implementation-engineer` toolset), the `/engineers` web view, systemd/start scripts, the Azure/test-VM rules, design-lab specifics beyond the generic `design_authority` rules. **Keep** `create_ben_implementation_engineer_assignment` (native subagent uses it) and `claude_turn.py` (Sunny's `claude -p` runner). Fold the generic "Proof budget" rule from the lanes guide into planning rules.

## 7. Headless contract (Iris and Ben)

Iris and Ben run as `claude -p` sessions started by Sunny (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, stdin `/dev/null`, `--output-format stream-json`, resumed with `--resume <session-id>`). They never use AskUserQuestion. Every place a prompt says "ask the user/owner" becomes: stop and put the question in the final message. Every final message ends with:

```text
## Turn Status
Status: done | needs_decision | blocked | handed_off | in_progress
Summary: <one or two sentences>
Artifacts: <absolute paths, one per line, or none>

## Decision needed            (only when Status is needs_decision)
Q1: <question in plain English>
Options: A) ... B) ...
Recommendation: <option + one-line reason>
Kind: technical | product | safety | data
```

Iris and Ben never push, pull, fetch, open PRs or change remotes; rendered settings deny these. Sunny, the interactive session, asks the user before any remote action.

## 8. Settings defaults (rendered `.claude/settings.json`)

Keep from the source: `subagentPromptCacheTtl: "1h"`, `disableBundledSkills: true`, the irrelevant-tool deny list, built-in `Agent(...)` denies for Iris/Ben (Explore, Plan, general-purpose, claude-code-guide, statusline-setup, claude), git denies (stash, reset --hard, clean, force push, remote add/set-url/remove/rename/set-head), `attribution: {commit: "", pr: ""}`, `enableAllProjectMcpServers: true`, the PostToolUse `Agent` hook → `trellis hook register-subagent`. Iris/Ben additionally deny `git push/pull/fetch` and `gh`. `additionalDirectories`: project dir (and repo_root if different). Drop: `ghki`, `GH_CONFIG_DIR`, `m1-reviewer`, Command Code denies, skill overrides naming claude.ai skills (keep the mechanism, empty by default).

## 9. Work rules for builders

- Write only inside your assigned directories. Read sources freely.
- Commit locally in `/home/abu/trellis` with the repo's configured identity, one commit per coherent step, message describing the change. No push, no remotes.
- Do not add a `Co-Authored-By` or `Signed-off-by` trailer.
- Keep prompts in the existing plain-English style (`STYLE.md` from the source; copy it into templates).
