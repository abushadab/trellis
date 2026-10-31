# {{config:project_name}} Development and Test Guide

This is the workflow's generic development and test guide for the repository at `{{path:repo_root}}`.

{{if:runtime_guide}}
`{{config:runtime_guide}}` is the project's runtime guide. It names the local runtime targets, how to start and seed them, and how to run the project's tests. Read it before any runtime work. When it and this guide disagree, the runtime guide wins.
{{else}}
This project has no runtime guide. Use the repository's own documentation, build files, package manifests, and current configuration as command authority. This guide records only the workflow's operating conventions and must not override newer repository behavior.
{{/if}}

## Repository Context

- Product repository: `{{path:repo_root}}`
- Workflow state: `{{path:state_dir}}`
- Integration branch for a workitem: `{{config:git.branch_prefix}}<workitem-id>`
- Temporary slice branch: `{{config:git.work_branch_prefix}}<workitem-id>`

Read the repository's own instructions before you change shared architecture, generated surfaces, authentication, or shared primitives.

## Environment

- Find the runtime target before you rely on it: check listeners, processes, and containers with the project's own commands, because ports and services are checkout-local facts.
- A built or served artifact can lag the working tree. Check that a running build matches the commit you are validating before you use it as evidence.
- Do not print, paste into artifacts, or commit environment files, tokens, cloud credentials, signing keys, or full environment dumps. Load only the specific credential an authorized integration test needs.

## Validation Selection

Choose the smallest credible checks for the changed risk, then broaden before final acceptance when the feature crosses layers.

| Changed area | Focused checks |
|---|---|
| One package or module | The project's focused test command for that package |
| Code with generated outputs | The generator, a focused test, then the broader suite when warranted |
| Frontend package | The package's type check, focused tests when present, and its build |
| Cross-package change | The project's check, lint, and build commands as warranted |
| API or schema change | The relevant generators, backend tests, and affected client checks |
| CLI or tool surface | Focused tests plus an actual command or tool invocation |
| Database or schema change | Focused schema and migration tests plus a disposable local apply |
| External integration | Unit fixtures, failure tests, and a real sandbox run (see below) |
| Full product behavior | The narrowest applicable end-to-end test |

Do not report an unrun check as passing. Record the exact blocker and the owner of any evidence that cannot be produced locally.

## External Integration Testing

External behavior needs real sandbox evidence before final acceptance. Mocks and recorded fixtures may support development before sandbox access exists, but they do not close the claim.

- Use a dedicated sandbox, trial, or disposable account, never a production or customer account.
- Grant only the permissions the tested behavior needs. Start read-only.
- Verify creation, update, disappearance, repeat runs, and permission failures with disposable resources.
- Confirm possible billing before you enable a paid service.
- Never use shared credentials or a billing-impacting service without explicit authorization.

Bind runtime evidence to the exact implementation commit. Record which account, project, configuration class, and fixture you used, without recording secrets.

## Git Safety

- Preserve unrelated user changes.
- Do not rewrite shared history or rebase shared branches.
- Do not push, pull, fetch, merge, open pull requests, or change remotes. Sunny asks the user for those.
- Follow the repository's commit rules (for example sign-off requirements) when its instructions state them.

## Destructive Operations

The local development runtime and task-owned local fixtures have standing disposable-state authority. After you verify the exact local target, you may reset or recreate them without a separate preservation step. Volume deletion outside that runtime, cloud-resource deletion, credential rotation, and other externally visible actions still need the exact target and authority from the active task. Never destroy unrelated Git work, external or shared state, credentials, production or customer data, or any state the active task marks non-disposable. Prefer task-owned fixtures with deterministic cleanup.
