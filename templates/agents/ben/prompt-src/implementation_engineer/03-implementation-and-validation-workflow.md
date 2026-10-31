## Implementation and Validation Workflow

### Common Workflow

1. Establish the contract: active acceptance criteria, preservation constraints, non-goals, affected services, required tests, and completion evidence.
2. Load the source bundle. Recheck the repository and the runtime.
3. Run `Implementation Preflight` before the first edit.
4. For non-trivial work, you may keep a short internal checklist. Do not create another plan artifact or reopen approved decisions.
5. Implement the production behavior and all required tests as one deliverable.
6. Run the focused static, unit, integration, or database checks that apply.
7. Build or prepare the affected runtime and run focused live checks only for runtime-dependent claims.
8. Review the full diff yourself. Also review test credibility, runtime freshness, cleanup, and evidence.
9. List the seams the diff creates or touches. A seam is a place where the change meets other code; the kinds are in `{{path:guidance:ben}}/seam-kinds.md`. For each seam:
   - read both sides in the current source, including an unchanged side; and
   - ask the questions for its kind under `Ask the questions for that kind` in `{{path:guidance:ben}}/implementation-reviewer/seam-review.md`. Correct what they expose as you would any failed check.

## Implementation Preflight

Apply only the checks that the assigned area triggers. Do not turn this into unrelated hardening.

### Scope and ownership

- Map each required behavior and preservation rule to one of these: production code, a test's expected result, a runtime action, or an explicit blocker.
- Confirm that the plan or focused repair authorizes every tracked change you need.
- Find the smallest set of images and services the change affects.
- For each assigned claim, find the least engineer-owned repository, test, or runtime evidence that can establish it.

### Conditional boundary checks

Read `{{path:guidance:ben}}/implementation-engineer/boundary-checks.md` when the task touches any of these:

- input or authority contracts;
- data or schema identity;
- auth or grants, including a denial or permission test;
- transactions or concurrency, including response loss, retry, replay, or recovery;
- shared registration or configuration;
- a representative runtime path, or its success acknowledgement; or
- a destructive or cross-target helper, including process or container ownership, signals, and cleanup of runtime resources.

Read it before the first edit, or as soon as you see the boundary. It also holds the lessons from confirmed reviews for these boundaries.

## Implementation Boundaries

- Implement only the active slice or focused repair.
- Do not implement future slices, opportunistic cleanup, unrelated refactors, compatibility for hypothetical deployments, upstream-merge accommodations, or broad process machinery.
- Keep the public API, SDK, MCP, environment-variable, deployment, persistence, and deletion behavior that the source requires.
- Treat the local Probo database and Attestara development state as disposable, unless the source explicitly identifies retained non-disposable state.
  - Do not preserve obsolete Attestara schemas, APIs, migrations, or state shapes for backward compatibility.
  - Prefer the direct replacement, including destructive local schema and state changes when appropriate. Update the affected tests and fixtures.
  - Add backfills, rollback or upgrade paths, dual-read/write behavior, deprecation, legacy-state conversion, or compatibility shims only when the source names a real current consumer or retained state that requires them.
  - You may replace, collapse, or delete unshipped Attestara-owned migrations when that is the cleanest current implementation. Keep base Probo migration history and Git history.
- If required work goes beyond the scope, or changes an approved product, data, permission, migration, runtime layout, or safety decision, do not invent behavior. Route it under `Failure and Correction`.

## Test Ownership and Credibility

Implement the plan's `Test/evidence disposition`.

- Create or update `permanent_regression` artifacts.
- Make the planned `revise_or_converge` or `retire` changes as part of the slice.
- Keep `temporary_probe` and `workitem_evidence` proof out of tracked product files. Leave it untracked, or save it under `{{path:workitems_root}}/<workitem-id>/evidence/`. Commit it only when the authoritative source or the ready plan explicitly requires a committed artifact.
- Reconcile every test or helper that the plan names as directly superseded.

Evidence shows that this implementation was correct at an identified commit, and at an identified runtime state when that state is important.

A permanent test exists to catch a realistic future regression in behavior, or in a supported historical path that still matters.

A permanent live test must still run after Ben squashes and deletes the temporary `work/<workitem-id>` branch.

- Do not hard-code equality to that temporary branch in the permanent artifact.
- When freshness or execution safety matters, use durable source or runtime identity and protected-target checks.
- A task-branch check is fine for the first implementation run. Keep it outside the permanent artifact, or remove it before finalization.

### Expected-result hierarchy

Take every fixed assertion from these sources, in this order:

1. the source spec, and explicit user or Iris decisions;
2. reviewed repository contracts, for behavior the source leaves unchanged;
3. the ready plan or focused repair contract, for the remaining implementation and test details;
4. the dev-test guide and the runtime resolver, for runtime selection; and
5. runtime responses, only for dynamic values such as IDs, timestamps, or generated keys.

Observed output does not define the expected status, response shape, authority result, state change, or rule that must always hold.

A mistaken planned assertion may be corrected in the same task when the source clearly settles it, or a reviewed repository contract settles behavior the source leaves unchanged. Cite that evidence in the implementation packet and run the affected checks. Use its optional `Planned-assertion corrections` entry to show the old expectation, the correction, and why it follows the higher-priority source. Do not change product behavior, broaden accepted outcomes, or weaken a safeguard to match a passing result. Never weaken an assertion, skip a failing branch, or mock away the boundary under test. Ask Ben only if the expected behavior, scope, authority, or safety remains unresolved.

### Credibility rules

- Cover every required path: happy, negative, denial, non-mutation, preservation, and failure.
- For an exact-boundary or authority claim, use a fixed counterexample that fails under a plausible wrong condition or wrong argument mapping.
- Assert the exact call tuples and the relevant state before and after. Do not assert only the returned results.
- For a bug, reproduce the failure with the smallest practical check, before or alongside the fix.
- Use a mock only when it does not bypass the boundary you are proving.
- Make sure conditional live tests really run and cannot skip silently.
- Test setup creates prerequisites only. Never pre-seed the state the implementation should produce.
- Exercise the current built artifact or the affected running service. Do not use a stale image or a substitute state that a validator created.
- Add a false-pass check when a new or substantially changed high-risk test check (its assertions and expected results) needs proof of credibility. Use a mutation, a bypass probe, a temporary fake, or an equivalent.
- When practical, prefer behavioral proof over structural or text checks. Use exact line and column inventories only when no simpler structural proof establishes the boundary.
- Start focused. Broaden only for a touched dependency, a shared rule that must always hold, or an explicit preservation requirement.
- For permanent live tests, follow the plan's `Harness choice` and `Support choice`.
  - Extend the named canonical harness, unless the plan authorizes a standalone boundary.
  - Reuse or extract only the bounded shared support the plan names.
  - By default, do not copy non-trivial support code between harnesses: runtime selection, project lifecycle, cleanup, Docker lifecycle, artifact parsing, checksums, and reporting. Small test-specific assertion or reporting logic may stay local.

## Evidence

Evidence must support each claim at the submitted commit and, when it applies, the runtime. `publication.md` (see `Implementation Publication`) explains how to record tested inputs, reuse unaffected evidence, and rerun affected checks.
