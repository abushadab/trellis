# Planner Repository and Risk Gates

Read this guide when any `Conditional Repository and Risk Gates` trigger applies. Apply only the triggered checks. Record only evidence that affects the plan.

## Refresh

Trigger when a stale, exact fact taken from the repository could invalidate execution, validation, preservation, or handoff. Examples: a commit, version, migration endpoint, route, signature, role, config key, command, or flag.

- Observe it again during this planner call. Record the source path or read-only command.
- Use prior plans and packets for navigation or history, never as the only source of a current value.
- If the current value conflicts with the assignment, accepted evidence, or a preservation boundary, resolve or route the conflict. Do not choose silently.

## Expand

Trigger when the indirect behavior of a helper, script, generator, provisioner, migration wrapper, deployment or lifecycle command, or stateful test decides the runtime scope or safety. A focused build, test, typecheck, or lint command triggers this only when its wrapper adds relevant side effects.

- Inspect the exact invocation, defaults, and flags. Record the affected services, dependencies, files, persistent state, and nested actions.
- For a stateful test, inspect the default fixture selection, shared-state changes, fixture lifetime, and cleanup.
- Compare the expansion with the affected services and state the plan states (`Likely files/components`, and `Runtime impact` or `Runtime obligation`).
- If it goes beyond the intended action, pick an established narrower invocation or an explicit command. Block when no safe in-scope path exists.

## Enumerate

Trigger when correctness or side effects vary by prior state, actor or entry path, retry or duplicate, partial completion, terminal state, or concurrency ordering.

- Add a compact table for the applicable combinations. Give the entry path or actor, the authoritative prior state, the serialization or authority point that applies, the action admitted and its side effects, and the durable result or error.
- Compare sibling paths that should enforce the same rule, such as method or context, manual or automatic, API or background, create or update, first call or replay.
- Resolve uncovered or contradictory cases before marking the plan ready. Do not leave the Implementation Engineer, Implementation Reviewer, operator, or a later adversarial probe to invent the condition.

## Feasibility

Do the full check when a step does any of these:

- changes or depends on permissions;
- is destructive outside the verified disposable local development database;
- affects external or shared state;
- is material (the `material-risk` threshold in your prompt); or
- leaves a helper-driven runtime boundary unresolved.

The full check:

- Name the performer or owner, the action, and the target.
- Verify the exact permission or authority when it is part of the risk.
- Define what each actor may and may not do, and the unrelated grants to preserve. For every new or changed database object, check ownership, direct grants, `PUBLIC`, and relevant role membership in both directions.
- Verify the required transactions or locks.

For a helper action covered here, use `Expand` to find its indirect effects. Inspect the rendered configuration. Plan a non-mutating preflight that shows:

- the resolved file and bind paths;
- the target service and its dependencies; and
- proof that off-target persistent data, volumes, and unrelated services stay safe.

A local database reset, recreate, or schema replacement does not trigger the full check just because it is destructive. Verify the exact local target, then use the routine path below unless another material boundary applies.

For routine actions below the material-risk threshold, including a verified local database reset, recreate, or schema replacement, name only the target, the owner, and the smallest behavioral check. If the feasibility or boundary of a material-risk step is still unproven, use `Resolve Unknowns`.
