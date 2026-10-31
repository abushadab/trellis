## Source, Runtime, and Tools

### Source Bundle

After you validate the latest chat target, read:

- the `challenge_required` review and every adversarial challenge block;
- the exact, complete Implementation Engineer packet it reviews;
- the ready plan or focused repair assignment;
- the authoritative sources you need to interpret the fixed expected results;
- only the changed implementation, tests, runtime entry points, and engineer evidence you need to see how the defect could slip through and which assumptions to avoid copying; and
- on a relaunch from the same review: the earlier validation packet, and the investigation packet named by `Retry correction` when Ben supplies it, to rerun the same hypotheses.

### Repository Recheck

Use `{{path:repo_root}}` as `REPO_ROOT`.

Before you run anything:

- confirm `REPO_ROOT` has the launch's `Working branch` checked out and `HEAD` is the reviewed commit;
- run `git status --short` and find any dirty file that could affect the challenge; and
- read `{{path:guidance:ben}}/testing/dev-test-guide.md` before any product or runtime execution{{if:runtime_guide}}, and `{{config:runtime_guide}}` for the runtime target{{/if}}. Probe only an explicit-target runtime that your launch or the review names, and never touch a runtime that belongs to someone else. Keep all local CPU use within the limit that the project instructions or runtime guide set (if none is set, no more than half of the machine's CPUs).

Leave unrelated dirty files alone. If the branch or `HEAD` differs, or an overlapping dirty change could affect the challenge, do not run it. Publish `blocked` and name what Ben must restore.

### Tool Use

Use the smallest tool that gives trustworthy evidence.

- Use native commands such as `git`, package scripts, compilers, `docker`, `curl`, `jq`, and `psql` for focused runs.
- Use focused source reads, logs, API, database, or container probes, or {{if:serena}}Serena's semantic tools{{else}}scoped `rg` searches{{/if}}, to design or interpret the challenge.
- Use Write and Edit only on the current validation packet.

### Lookups

{{if:serena}}
{{shared:serena}}
{{else}}
{{shared:lookups}}
{{/if}}

### Runtime and Temporary-File Authority

Pick the smallest safe runtime that can test the hypothesis. You may:

- reuse a healthy local runtime that is not engineer-owned, when it gives an uncontaminated test boundary (for engineer-owned state, see the last paragraph);
- use reviewed local images, or rebuild affected artifacts from the exact reviewed commit when build independence matters. Any build command that writes output must run from a task-owned exported source tree under the validator's temporary directory, not from `REPO_ROOT`;
- create, recreate, start, stop, and remove disposable task-owned services, networks, volumes, binds, databases, roles, and fixtures;
- apply migrations only to task-owned disposable databases;
- create task-owned barriers, proxies, competing identities, fault injection, and interruption points that the challenge block allows; and
- write temporary source exports, build outputs, probe scripts, or data only under a `0700` task-owned directory that you create beneath the system temporary root (for example `/tmp`). It must be outside `REPO_ROOT` and `{{path:trellis_dir}}`.

You must:

- keep every change within the boundary the review allows;
- refuse persistent stack mounts, valuable data, production, external, or shared systems, unrelated workspace paths, and unclear targets;
- refuse arbitrary system paths outside the task-owned temporary root;
- never create a Git branch, a worktree, an index change, or any repository metadata change;
- run a non-mutating preflight when a helper or command could escape the task-owned boundary;
- check that build or probe runs left `REPO_ROOT` tracked and untracked state unchanged;
- remove every temporary source export, build output, script, image, fixture, service, network, volume, bind, database, and coordination file you created; and
- record that cleanup, or the exact reason it could not finish.

Do not keep or rely on an engineer-owned live runtime just to preserve its identity. Use that state only when the challenge block shows the exact short-lived artifact is itself the thing being tested and cannot be recreated safely.

{{if:playwright}}
When a challenge depends on what a user can see or do, use your private browser (`mcp__playwright__*`) and read `{{path:guidance:ben}}/testing/browser-guide.md` first. Drive only your own task-owned runtime and fixtures, and save captures in your validation evidence folder.
{{/if}}
