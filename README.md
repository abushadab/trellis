# Trellis

Trellis is a Claude Code plugin that adds a three-agent workflow to any git repository. You talk to one
agent; it runs the other two for you.

- **Sunny** is the front agent. You chat with Sunny in a normal `claude` session. Sunny clarifies what you
  want, starts and resumes the other two, answers their routine questions, and brings product, safety and
  data decisions to you.
- **Iris** writes the specs. She scouts the code, researches, consults advisors, and produces single
  specs that Ben can build from, each reviewed before hand-off.
- **Ben** builds. He plans, has the plan reviewed, investigates, implements, has the work reviewed, and
  has an independent validator check the result.

```text
you <-> Sunny --intent--> Iris --reviewed spec--> Ben --validated work--> branch for you to review
          ^                  |                      |
          +---- questions ---+----------------------+
```

Iris and Ben run as headless `claude -p` sessions started by Sunny. They never talk to you directly and
never push.

## Install

Inside Claude Code:

```text
/plugin marketplace add abushadab/trellis
/plugin install trellis@trellis
```

Then, in the project you want to use it in (a git repository):

```text
/trellis:init
```

Init checks your tools, asks a few questions with detected defaults, writes `.trellis/config.yml`,
renders the agent folders and runs `trellis doctor`.

Requirements: `claude`, `git`, `uv`, and optionally `npx` for Playwright. Linux and macOS.

## Daily use

```bash
cd .trellis/agents/sunny && claude
```

Describe what you want to Sunny. `/trellis:init` marks the project's git root as a trusted workspace
(`trellis trust`) so the headless sessions Sunny starts keep the rendered permissions; there is no dialog to accept.

## Config

Settings live in `.trellis/config.yml`. Every key, with a comment, is in
[`templates/config.example.yml`](templates/config.example.yml). The main ones:

| Key | Meaning |
| --- | --- |
| `project_name`, `repo_root` | Name and code repository (relative to the project directory) |
| `project_instructions` | Files every role reads first, such as `AGENTS.md` and `CLAUDE.md` |
| `product_doc`, `runtime_guide`, `design_authority` | Optional docs. A design authority enables the design review lens |
| `stage` | `pre_production` (no backward-compatibility work) or `production` |
| `git.*` | Branch prefixes and the commit identity for agent commits |
| `commit_specs` | Whether specs and plans are committed by the agents |
| `tools.serena`, `tools.playwright` | Optional MCP tools |
| `mode` | `standard` (proven setup) or `saver` (cost saving, see below) |
| `models`, `efforts` | Per-role model and effort overrides on top of the mode |
| `sunny.autonomy`, `sunny.usage_threshold` | What Sunny may decide alone, and the usage pause level |

After editing the config, run `/trellis:update`.

### Modes

| Agent | `standard` | `saver` |
| --- | --- | --- |
| Sunny, Iris | Opus medium | Opus medium |
| Ben | Opus medium | Sonnet high |
| planner, assignment-engineer, spec-writer | Opus medium | Opus medium |
| plan_reviewer, implementation_reviewer, independent_final_validator, investigator, spec-reviewer, general_advisor | Opus high | Opus medium |
| assignment-reviewer | Opus medium | Sonnet high |
| reconciliation_advisor | Opus high | Sonnet high |
| implementation_engineer, researcher | Sonnet high | Sonnet high |
| scout | Sonnet medium | Sonnet medium |

`saver` never runs Opus at high effort. Switch by setting `mode` and running `/trellis:update`; running sessions keep their old setting until they are started again.

## Folder layout

```text
<project>/.trellis/
  config.yml                  your settings
  .gitignore                  written by Trellis
  agents/{sunny,iris,ben}/    rendered prompts, settings and .mcp.json; one working folder per agent
  state/                      registry, handoff chat, intents, specflows (specs/), workitems (plans/)
```

## Committed and ignored

Commit `.trellis/config.yml` and `.trellis/.gitignore`. Also committed are specs
(`state/iris/specflows/*/specs/`) and plans (`state/ben/workitems/*/plans/`). Everything else is ignored:
`agents/` is rendered per machine (it holds absolute paths), and the rest of `state/` is runtime data.

## Usage watcher

Sunny can watch your 5-hour Claude usage window. When usage reaches `sunny.usage_threshold` (default 75
percent), the lowest-priority running session is paused; Sunny resumes it after the window resets. The
watcher reads your Claude Code login token to ask Anthropic for usage numbers. If no readable token exists
(for example a macOS keychain login), it reports `usage: unavailable` and stays off.

## Optional tools

- **Serena**: set `tools.serena: true` and `tools.serena_url` to add a Serena MCP server to the agents.
- **Playwright**: `tools.playwright: auto` turns browser testing on when `npx` is installed. Use `true` to
  force it or `false` to turn it off.

## Safety defaults

- Iris and Ben never push, pull, fetch, open pull requests or change remotes. The rendered settings deny
  these, along with `gh`, force pushes, `git reset --hard`, `git clean` and `git stash`.
- Only Sunny talks to you, and Sunny asks before any push, pull request, or deletion of branches or data.
- Trellis writes no plugin-level hooks or MCP servers. Everything is rendered per project and can be
  inspected under `.trellis/agents/`.

## Updating

```text
/plugin marketplace update trellis
/plugin update trellis@trellis
/trellis:update
```

`/trellis:update` re-renders the agent folders and runs the health check. It never touches `state/`.
Restart Sunny afterward.

## Known limitations

- The git deny rules are a guardrail against accidental remote or destructive commands, not a sandbox. They cover the common spellings (including `git -C`, global options and an absolute path to `git`), but a determined agent could still find another route.
- `trellis trust` rewrites `~/.claude.json`. If Claude Code writes that file at the same moment, the concurrent change can be lost. Trust is written once per project, so run `/trellis:init` while no other Claude sessions are busy.

## Development

```bash
cd server && uv run --extra test pytest -q                                  # tests
uv run --quiet --project ./server trellis render --project <dir> --plugin-root "$PWD" --check   # is the render current?
uv run --quiet --project ./server trellis doctor --project <dir>
claude plugin validate .
```

See [`DESIGN.md`](DESIGN.md) for the contract and [`server/README.md`](server/README.md) for the
template syntax and tools.

## License

MIT. See [LICENSE](LICENSE).
