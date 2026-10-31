# Implementation Engineer Boundary Checks

The preflight in your prompt says when to read this guide. Run only the checks the task triggers.

- **Input and authority contracts:** validate raw runtime types before coercion. Enforce cross-field and action-specific mappings. Treat caller-supplied time, identity, outcome, and authority as untrusted, unless the contract explicitly delegates them.
- **Data or schema:** define the full identity, or the full set of rules that must always hold. Where it applies, cover success within the same parent, and rejection across parents, types, and versions.
- **Auth or permissions:** map ownership, direct grants, `PUBLIC` and default privileges, role attributes, schema access, `search_path`, and role membership in both directions. Where it applies, run the changed paths as the intended effective role.
- **Transactions or concurrency:** name the point where operations are serialized. Account for awaits, commits, retries, proxy and pool boundaries, and work in flight. For a capacity, one-winner, or exactly-once claim, use deterministic barriers.
- **Shared symbols, helpers, config, imports, or exports:** inspect callers, consumers, registration targets, duplicate application, effects at import time, and the branches you must preserve.
- **Runtime path:** find the smallest representative proxy, pool, startup, Compose, global registration, or built-entrypoint path. A parser, a mock, or a direct database check alone does not prove that boundary.
- **Runtime helpers with destructive or cross-target effects:** verify the repository and runtime roots, where the environment came from, container and network identity, prerequisites, and exact arguments. Before an authorized live action, prefer a render, a dry run, or a fake.

## Lessons from confirmed reviews

Apply each lesson only when your work touches its boundary. The scope limits under `Lessons from confirmed implementation reviews` in your prompt apply here too.

- **Prove a denial happens for the intended reason.**
  - Before a revocation, isolation, or permission negative, show that the exact credentials and claims succeed in the permitted state.
  - Change only the condition under test.
  - Keep the real minted role, key ID, and scope. A different invalid claim can hide a broken authorization condition.
  - For an important security check, show that bypassing the intended condition makes the test fail.
- **Tell caller loss apart from completed work.**
  - A response-loss test must see the real dispatch. It must hold the actual target effect outstanding when the caller disconnects.
  - Assert the required unresolved state before you release. Then release, wait for the work to settle, and check the exact retry outcome.
  - Destroying a response after the headers arrive does not prove loss during outstanding work.
  - On failure, release the test gates and settle the effects you own before cleanup.
- **Prove ownership before you record process identity.**
  - Before you change restart settings or send a signal, prove the container or task belongs to the selected cleanup target.
  - Keep that ownership tied to the same process through the whole capture, including parent discovery. A PID-safe signal cannot fix an earlier ownership mistake.
  - Test the real path from selection to action, with foreign lookalikes and a replacement during capture.
  - Refused cases must cause no update and no signal. The valid case must reach the intended action.
- **Prove the task list is complete before you declare cleanup finished.**
  - Vanished recorded processes, stopped containers, or a capture-complete marker do not prove that omitted or recovered helpers are gone.
  - Before you dispose of storage, require successful evidence that covers all relevant task work and its settlement, including after recovery.
  - Test a surviving, unrecorded helper while every recorded process is gone.
  - If task evidence is missing or unreadable, keep the resources and report failure. Do not signal unknown actors.
- **Connect verification to real success.**
  - Trace the production call chain through its success and its durable acknowledgement. A helper only tests exercise does not protect those paths.
  - When you change grants or schemas, include every consumer of those grants or schemas in the affected flow.
- **Give recovery tests a durable record that proves success.**
  - Seed the valid prerequisites. Do not pre-seed success.
  - Assert the real stored acknowledgement field, on both success and refusal or session loss. A returned boolean does not stand in for it.
  - To test background repair, withhold the foreground replay. Observe the repaired behavior before any extra activation call.
