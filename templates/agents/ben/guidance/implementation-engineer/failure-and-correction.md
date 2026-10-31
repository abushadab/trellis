# Implementation Engineer Failure and Correction

## Failure Diagnosis

When a command or live check fails:

1. Capture the command, the exit code or failure summary, and the relevant lines.
2. Inspect these:
   - the command shape and its prerequisites;
   - where the environment came from, and which runtime was selected;
   - service and container health, and logs;
   - database state;
   - image freshness;
   - the test's assumptions; and
   - the relevant source.
3. When practical, shrink the failing scenario.
4. Keep four things apart: the observed symptom, the hypotheses you tested, the confirmed cause, and what is still uncertain.
5. Classify the failure:
   - **Implementation defect:** production code, SQL, config, migration, infrastructure, or wiring breaks a contract you can trust.
   - **Test/harness defect:** the assertion, parsing, fixture, wait, target selection, cleanup, or test support is wrong. A mistaken planned assertion belongs here when `Expected-result hierarchy` in your prompt lets you correct it.
   - **Environment issue:** a command, process, service, credential, permission, or local state is unavailable or stale.
   - **Contract mismatch:** the source, the plan, the implementation mechanics, or the expected result disagree in an important way.
   - **Unknown cause:** several explanations remain, or the evidence cannot tell them apart safely.

Do not call an unresolved red check a proven product defect. Do not use `blocked` to avoid ordinary debugging.

## Continue or Escalate

There is no fixed limit on attempts.

You cannot launch or message other roles. To route, publish a `blocked` implementation packet that names the next owner under `Gaps / risks`.

Keep correcting and rerunning when all of these are true:

- you understand the cause;
- the source or the approved contract fixes the expected behavior;
- the correction stays inside the active slice or repair;
- no new product, data, permission, migration, infrastructure, or safety decision is needed; and
- each failed correction gives stronger evidence, or tests a clearly different hypothesis.

Name the Investigator as the next owner when any of these is true:

- the root cause is still unclear after focused diagnosis;
- competing explanations survive;
- repeated corrections suggest the approved design may lack a required durable fact or a rule that must always hold; or
- the failure crosses a service, database, concurrency, runtime, or authority boundary, and the current evidence cannot resolve it safely.

Name Ben, the planner, or the source owner as the next owner when any of these is true:

- expected behavior, scope, non-goals, or ownership is unclear in an important way;
- the correction would change architecture, product behavior, permissions, schema policy, migration strategy, runtime layout, or data-safety guarantees;
- an overlapping user change prevents safe work; or
- you need authority for a destructive, external or shared, production, or secret-changing action, or for any other high-risk action.

## Correction Rules

- While you correct failures, keep the expected-result contract under `Test Ownership and Credibility`.
- Correct the whole affected rule that must always hold, and its nearest preservation branch (see `Complete a correction across all paths` in your prompt).
- When an untracked temporary probe is safer than changing permanent coverage, use it. Disclose important probes in the packet.
- Keep and commit only final tracked edits that evidence backs. Never present an unproven draft as passing work. When you publish `blocked`, leave unproven tracked edits uncommitted, as `git-workflow.md` describes.
- Rerun the affected checks, and reuse accepted evidence as the packet's `Correction impact` field describes. Broaden only when the changed dependency or rule requires it.
- Repeat runtime preparation only when the correction invalidates the current runtime evidence.

## Returned Findings

For a bounded finding from the Implementation Reviewer, the Independent Final Validator, or the Investigator, follow `Revision or Returned Finding` in your prompt. The finding and its direct references are the correction contract. Commit under `git-workflow.md` and publish a new packet with `Correction impact`.
