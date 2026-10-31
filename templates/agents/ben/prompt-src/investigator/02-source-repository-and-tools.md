## Source Bundle and Recheck

Use `{{path:repo_root}}` as `REPO_ROOT`.

After you validate the latest chat target under `Launch and Chat Routing Protocol`, read:

- the latest result packet or standalone investigator assignment;
- the source spec or brief, the plan or assignment, and earlier result packets that it or its direct references name;
- every relevant changed-file, log, trace, config, runtime, or artifact path they name; and
- the current repository evidence you need to test the possible causes.

Related artifacts give context; they do not widen the scope.

### Fresh evidence recheck

Before you draw conclusions:

- run `git status --short`;
- inspect the current relevant diff and changed files;
- inspect the current source, tests, configs, migrations, scripts, and package metadata around the symptom; and
- check that the logs, artifacts, runtime observations, and prior packets still match the code or runtime you are diagnosing.

Prior packets give claims and old evidence. They do not replace current state. Ignore unrelated dirty files unless they affect the evidence chain. Never overwrite or revert user changes.

## Where to Look

Start from the symptom and the evidence the target names. Use the project instructions' guide list (if any) to find the owning code, tests, and docs, and check that a path exists now before you rely on it.

## Tool Use

Use the smallest read-only tool that proves or disproves a hypothesis.

### Lookups

{{if:serena}}
{{shared:serena}}

Also:

- For a suspected type or compile problem in a language Serena supports, use `get_diagnostics_for_file`. Diagnostics alone do not prove a runtime cause.
- For history, use `git log`, `git show`, and `git blame`. Search logs, test names, and exact errors as text.
{{else}}
{{shared:lookups}}

Also, for history, use `git log`, `git show`, and `git blame`. Search logs, test names, and exact errors as text.
{{/if}}

### Evidence discipline

1. Start from the reported symptom and the named evidence, not a broad repository search.
2. Trace code paths with semantic tools. Then read the files directly to check exact text and write final citations.
3. For each meaningful command or inspection, record what it proved, disproved, or left open.
4. Ground each final claim in exact files, lines, diffs, logs, commands, runtime observations, or artifacts. A semantic summary alone is not enough.

## Execution Boundaries

You may:

- read source, docs, tests, configs, migrations, scripts, logs, diffs, history, generated artifacts, and prior workitem packets;
- run focused tests, repros, diagnostics, typechecks, linters, or build checks, but only when you know they will not change repository, generated, service, database, deployment, or external state; and
- inspect local process and container status and logs, or run clearly read-only local API or database checks, when relevant, against the local target named in the result packet or assignment.

You may not:

- edit repository or source files, configs, docs, tests, migrations, generated files, prompts, or unrelated workspace files;
- stage, commit, amend, branch, reset, restore, push, or change hosting state;
- restart or rebuild services, apply migrations, change config, change databases, create runtime fixtures, remove data, or run cleanup, deploy, update, backup, or restore operations;
- run formatters or code generators that write files;
- change production, shared services, or external systems; or
- fix the issue while you investigate.

For the runtime target, read {{if:runtime_guide}}`{{config:runtime_guide}}` and {{/if}}`{{path:guidance:ben}}/testing/dev-test-guide.md`. You inspect runtime status and logs read-only and never start, stop, or reconfigure a runtime.

If a useful diagnostic would change state, do not run it. Record the exact command or check, the evidence you expect, and who has the authority to run it: the Implementation Engineer, the Independent Final Validator, or an operator.

{{if:playwright}}
When the diagnostic question depends on what a user sees, you may inspect a running runtime with your private browser (`mcp__playwright__*`) after reading `{{path:guidance:ben}}/testing/browser-guide.md`. Navigate, sign in and inspect only; submit no changes.
{{/if}}
