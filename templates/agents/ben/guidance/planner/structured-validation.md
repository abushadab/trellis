# Planner Structured Validation

This guide defines the structured-contract triggers and fields once. The rest of the guide applies when a trigger does. Its fields replace the minimum contract's fields. The minimum contract's `Test/evidence disposition` format and the plan validation rules in your prompt still apply.

## Trigger Definitions

A **permanent live-test change** adds a permanent `.sh` test, or changes such a `.sh` test's assertions, runtime target, mutation, fixtures, or cleanup. Comments, formatting, and refactoring do not count.

Use every labeled structured-contract field when any of these categories applies:

- **Test/runtime:** a permanent live-test change, or runtime work with material-risk persistent data or runtime-layout risk.
- **Boundary:** cross-slice behavior, inherited deferred validation, or multi-service behavior whose ordering or contract facts go beyond the minimum contract. One obvious contract across two local services does not trigger this by itself.
- **Risk:** auth, permissions, secrets, data integrity, migrations, public contracts, or preservation claims that need more than minimum validation. A routine additive migration or a small auth or config test change does not trigger this by itself.
- **Execution:** destructive, broad, flaky, external, soak, or non-trivial lifecycle validation.
- **Coordination:** two or more test areas that need shared fixtures or ordering; non-trivial fixture ownership; or interface or runtime facts the Implementation Engineer must resolve during execution because the implementation chooses them.

Terms:

- **Broad** effects go beyond the slice's named targets.
- **Non-trivial lifecycle** goes beyond ordinary `local Probo development runtime` build, recreate, or restart, or uses failure injection, outage recovery, or service sequencing.
- **Non-trivial fixture ownership** means a fixture outlives its creator's run, crosses slices, or has cleanup owned by someone other than its creator.

Routine scoped dev actions do not trigger a category just by happening.

## Structured Contract

The structured contract adds these fields to the implementation-review and candidate fields:

- `Test/evidence disposition`: same format as the minimum contract's field.
- `Harness choice`: for each permanent live-test change (defined above), record `extend <existing path> | new standalone <path> — <reason>`.
- `Support choice`: for each permanent live-test change (defined above), record `reuse <helper> | extract <bounded helper> | local — <reason>`.
- `Acceptance oracle`: test ID -> fixed expected result -> source AC or decision -> the plausible wrong implementation the test must fail on.
- `Fixture and cleanup boundary`: the task-owned fixtures, the changes allowed, the cleanup owner, and any concrete reason state must survive the engineer run. Keep a runtime, prepared build, or live layout for another agent only when all of these hold:
  - the exact transient state or built artifact is itself important to the claim;
  - it cannot be safely reproduced; and
  - the plan names the concrete risk the handoff protects against.

  Never keep it just so another agent can rerun tests or validation can reuse it.
- `Runtime impact`: the runtime class, the Implementation Engineer action, the affected services and state, the known helper or selection rule, the fixture and cleanup owner, and why the class is enough.
- `Commands/checks`: known existing checks, and candidate engineer-run focused or static scenarios and live scenarios to run after preparation. The Implementation Engineer packet supplies the exact final command set.
- `Existing regressions`: suite -> the relevant expected result you inspected -> the risk or preservation AC it touches.
- `Deferred live obligation`: the later owning slice and the reason, or `none`.

## Permanent Live-Test Planning

For a permanent live-test change:

1. Read `/home/abu/project-attestara/claude-workspace/testing/dev-test-guide.md`.
2. Inspect and name the nearest relevant shell exemplar, such as `contrib/testing/test-evidence-flow.sh`, or the closest existing test script under `contrib/testing/` or `e2e/`.
3. The permanent test's future trigger or home must stay valid after the temporary `work/<workitem-id>` branch is squashed and deleted. Do not make permanent execution depend on equality with a temporary work branch. When source or runtime freshness matters, use a durable identity: an accepted commit or tree input, a source or image identity, a resolved runtime identity, or another stable repository contract.
4. Prefer extending the nearest standard harness. Use `new standalone` when the runtime layout, isolation, fixture ownership, destructive risk, or acceptance boundary clearly differs, and say why.
5. Prefer an existing helper for non-trivial shared work: runtime selection, project lifecycle, cleanup, Docker lifecycle, artifact cleanup, or similar support. Use `extract <bounded helper>` only when two or more real consumers need the same behavior. Keep small test-specific assertion or reporting logic `local`. Do not centralize it just to cut lines.

Do not copy the full harness guide into the plan, and do not invent names the implementation will choose. The Implementation Engineer follows the dev-test guide. The plan must not require a prepared-runtime handoff, a no-build validator route, or a preserved runtime layout just for an independent rerun.
