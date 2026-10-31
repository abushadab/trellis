## Review Workflow and Standards

### Steps

1. Validate the target under `Launch and Chat Routing Protocol`: packet, task identity, source, branch, and submitted commit.
2. Establish the active acceptance criteria, preservation constraints, non-goals, changed boundaries, and claimed evidence.
3. Do the implementation-correctness pass.
4. Do the seam pass in `seam-review.md`. List the seams, read both sides, and answer the questions for each kind.
5. Do the test-and-evidence-credibility pass against the same changed behavior.
6. Classify each concern as a confirmed finding, needs more checking, question, optional suggestion, or residual limit.
7. Do the completeness pass and the disprove pass.
8. If no confirmed finding or blocker prevents acceptance, decide whether a residual runtime hypothesis meets all five conditions in `Adversarial Challenge Decision`. If one does, publish `challenge_required` with the complete adversarial challenge contract. Otherwise publish `pass`.

Code or tests that differ from the plan's wording are not automatically wrong. Ask whether the submitted implementation causes any of these:

- wrong behavior;
- unsafe operation;
- missing required behavior;
- a test that passes on wrong behavior; or
- a concrete residual runtime risk that review and engineer evidence cannot resolve.

{{if:pre_production}}
{{config:project_name}} is pre-production unless the source states otherwise. Local development state is disposable.

- Do not request compatibility shims, data-preserving upgrade paths, rollback, backfills, dual behavior, legacy support, or mixed-version handling. The one exception is a concrete current consumer or explicitly retained non-disposable state.
- When such machinery was added without a source-backed need, treat its unnecessary complexity as a review defect.
- Do not mistake a clean breaking replacement for a regression just because it does not preserve obsolete development state.
{{/if}}

## Concern Classification

### Findings

Use `Findings` only for a confirmed defect or regression with a realistic failure path.

Fill every field of the `Findings` block in the publication guide.

### Needs More Checking

Use `Needs more checking` when an important failure is plausible and partly supported, but proof still needs a caller trace, an isolated check, a missing artifact, a runtime fact, or an investigation.

- State the possible failure, the evidence so far, the missing fact, and the next owner or check.
- If the missing fact stops you trusting the implementation, publish `blocked`.
- Otherwise record it under `Residual limits`. Do not leave an open `Needs more checking` item.

### Questions and Optional Suggestions

- Use `Questions` only when the answer changes whether the submitted implementation is acceptable.
- An unresolved owner or source question is not a confirmed defect.
- Use `Optional suggestions` only for improvements with no concrete failure path. Never route them as required corrections.

### Severity

Give a severity only to confirmed findings:

- **Critical:** large-scale or irreversible data loss, exploitable credential or sensitive-data exposure, an irreversible destructive action, or a complete core outage with no practical workaround.
- **High:** likely core-workflow failure, serious unauthorized access or privilege escalation, a serious regression, or a serious runtime failure.
- **Medium:** a confirmed defect with limited scope, lower likelihood, a practical workaround, or non-core impact.
- **Low:** a confirmed minor defect.

Choose severity from actual impact, likelihood, affected workflows or data, recovery, and workarounds. Do not raise severity just because the code touches security, SQL, migrations, or infrastructure.

## Required Completeness Pass

For every rule, boundary, or evidence claim the submitted commit changes, inspect the related actors, callers, branches, outcomes, negative paths, preservation paths, runtime claims, and test claims that the change can affect.

Stay inside the active implementation and the seams it touches. Do not rerun the whole source's acceptance criteria.

## Required Disprove Pass

Before you finalize each candidate concern, ask:

- Does the approved source or focused repair allow the behavior?
- Does another changed or existing reachable path already handle it?
- Does a caller, middleware layer, database contract, or framework convention prevent the failure?
- Can the path be reached in the selected MVP runtime?
- Do types, tests, build output, runtime evidence, or repository behavior contradict the concern?
- Is there a correction smaller and safer than the submitted implementation? Judge the failure separately from the fix. If the only fix you see is too broad, keep the finding and narrow the fix. Do not drop a real failure because of its remedy.
- Is the cautious behavior actually intended? Apply `Failing closed is not automatically correct` in `seam-review.md`.
- Would the finding only ask for a metadata refresh, duplicate validation, optional hardening, or another review round that does not change your confidence?
- Can you recover the missing evidence safely by reading source or running a focused check, instead of creating an adversarial challenge?

Demote or remove anything that fails.

## Do Not Report as Findings

- Style, naming, wording, structure, comments, or preferred architecture with no concrete failure.
- Generic best practices, hardening, retries, abstractions, fallbacks, cleanup, or extra tests with no reachable risk.
- Future-slice concerns, unless they break the active slice or a required preservation constraint.
- Packet, command, metadata, or read-only proof mechanics that you can safely recover, and that do not change coverage, expected behavior, mutation or fixture scope, runtime identity, or confidence. Derive and verify a trustworthy replacement yourself, for the same rule and with no tracked changes; that needs no engineer round.

## Adversarial Challenge Decision

Publish `challenge_required` only when all five are true:

1. The implementation and test/evidence lenses are otherwise trustworthy.
2. A source-backed claim that matters depends on runtime behavior.
3. A specific wrong implementation could plausibly survive the reviewed tests and source analysis because they may share the same assumption, such as the same mock, fixture, identity, ordering, or helper.
4. A bounded, independent probe can try to disprove that claim safely.
5. The consequence is material, as defined under `Material Risk`.

A material interruption risk that lacks credible evidence meets condition 3, because tests of only the normal path cannot catch a wrong recovery. Examples are a failure between durable steps, a lost response, or an owner replacement. The plan's `Durable steps` section shows where these can happen. Evidence is credible when it actually exercises or settles that interruption. Do not require a challenge at every interruption boundary.

A broad technology category (Docker, a database, migrations, auth, permissions, secrets, or several services) or a general wish for more confidence is not a hypothesis.

Each challenge fills every field of the `Adversarial runtime challenge` block in the publication guide.

You may use plan candidates as leads. Decide from the actual implementation. Do not make a frozen runtime, an engineer-owned waiter, an exact validator command, or a test rerun the purpose of the challenge.
