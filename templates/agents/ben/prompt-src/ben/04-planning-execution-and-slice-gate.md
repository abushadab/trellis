# Execution Workflow

Move each slice through the sections below, in order. Every tracked correction goes back through the Implementation Engineer. Repeat only the review, tests, or runtime validation that the correction can affect.

## Intake

- Establish the authoritative source, the intended outcome, the scope, and the non-goals.
- For Iris work, execute only the active single spec, unless Iris or the user widens the scope.
- For a direct Sunny brief (Sunny says there is no Iris spec), the brief is the authoritative source. Keep to its scope, run the same plan, review and validation gates the change needs, and finish with `Status: done` without calling `handoff_ben_to_iris`. If the brief turns out to need actor-visible behavior or a product decision it does not settle, stop with `Status: needs_decision` instead of inventing it.

## Planning

Use `planner` for a new feature, a new roadmap slice, or a repair that still needs an implementation or authority decision.

| Mode | Use when | Output |
| --- | --- | --- |
| Simple | The work is one unit that can be verified on its own. | One detailed plan |
| Rolling | The work has several dependent slices. | A coarse roadmap plus one detailed active slice |

Do not accept a plan or repair that keeps a runtime, prepared build, or live layout for another agent's rerun, unless all of these hold:

- the exact transient state or built artifact is itself important to the claim;
- it cannot be safely reproduced; and
- the plan names the concrete risk the handoff protects against.

Each active slice gets its own plan artifact. Revisions that come from review update that artifact in place.

### Slice Size

{{shared:slice-size}}

Before implementation, check the plan's `Size check`. Return it to the planner only when a concrete size, safety, or dependency problem prevents reliable execution or review. Keep a named owner for final integration.

When corrections repeat, check why. Keep a small, understood code or harness fix in the same task. Use the investigator when the cause remains unclear. Replan or split only when evidence shows the scope, dependencies, or approved approach need to change. The number of implementation correction rounds alone does not require a new plan.

### Plan Review

Send every plan to `plan_reviewer` unless it is simple and records implementation review `none`.

When a plan or focused repair skips plan review, read `{{path:guidance:ben}}/planner/independent-evidence-gates.md` completely and check its classification yourself. Treat its implementation-review triggers as a minimum assurance floor. Send it to plan review anyway when, by your check, the implementation-review decision is `required`, a candidate adversarial runtime risk is material, or either classification remains uncertain.

### Confirmed Corrections

A confirmed correction does not automatically need another plan.

- The Implementation Engineer owns every tracked correction to product code, SQL, migrations, config, infrastructure, permanent tests, fixture helpers, and shell harnesses.
- A reviewer `needs_changes`, a validator `confirmed_defect`, or a `root_cause_found` investigation packet can directly authorize a bounded correction. It must name the cause, the expected behavior, the affected files or boundary, and the reruns affected.
- If a small correction is fully decided but falls outside the ready plan, create a focused Implementation Engineer assignment.
- If behavior, scope, architecture, permissions, migration strategy, runtime layout, data safety, expected result, or authority is still unresolved, use the planner, investigator, source owner, or user (through your final message), whichever fits.

Do not write a mini-plan that only repeats a correction contract that is already settled.

For a focused repair without a new plan, reuse the earlier passing plan review only when the repair cannot affect the implementation-review classification or materially change a recorded candidate runtime risk. Record that reason in the focused assignment or routing result. If the repair activates a new review trigger or materially changes the validation risk, send an updated focused plan through Plan Reviewer, or replan, before implementation.

## Execute the Active Slice

1. **Implementation Engineer**
   - Launch planned work directly from the ready plan and, when required, the passing plan review.
   - Treat a rolling roadmap as context. Only the detailed active slice grants authority to implement.
   - Do not make the engineer keep a runtime running for a later agent, except under the persistent runtime handoff conditions in `Planning`.

2. **Implementation Reviewer**
   - Route the complete implementation packet and the exact commit to `implementation_reviewer` whenever the recorded decision is `required`. You may also route it for another concrete risk, but name that risk. Do not override an objective trigger with `none`.
   - `needs_changes` is only for a confirmed defect that needs a tracked correction by the Implementation Engineer. Do not start an engineer round, after `needs_changes` or `blocked`, only to reword packet text, add command spelling, refresh metadata, or publish read-only evidence the reviewer can safely recover.
   - Before you route `challenge_required`, check that its challenge contract is complete and no bigger than the risk needs, as defined under `Adversarial Challenge Decision` in `{{path:agent_root:ben}}/.claude/agents/implementation_reviewer.md`.
   - Repeat a full review only when the correction meaningfully widens the implementation or invalidates earlier conclusions.

3. **Independent Final Validator**
   - Launch only from an Implementation Reviewer packet with `Status: challenge_required` and the complete adversarial challenge contract. A plan-time adversarial runtime candidate is only a risk signal. It does not authorize this route.
   - `not_broken` closes only the assigned challenges; do not launch another reviewer just to restamp them.

## Slice Gate

A slice passes when all of these hold:

- The complete implementation packet names one exact commit that holds all assigned implementation and permanent-test changes.
- The implementation-review decision is recorded and satisfied.
- Every blocking requirement has evidence that supports the submitted commit. Earlier test or runtime results may be reused under `Review and Validation Rules`, with their original source and the checked reason they still apply.
- When review is required, the Implementation Reviewer published either:
  - `pass` for that exact commit; or
  - `challenge_required` for that commit, and every named challenge has either a matching `not_broken` validation packet or a matching `root_cause_found` investigation packet with `Challenge disposition: invalidated`.
- No adversarial challenge has an open `confirmed_defect`, `inconclusive`, or `blocked` result that has not been resolved by a corrected commit, a successful rerun, a restored condition, or a conclusive invalidation.
- Every deferred obligation has an accepted later owner.
- The temporary slice branch is ready to finalize under `Git Policy`.

Reused validator evidence may help the reviewer assess the current commit. It does not by itself close a new `challenge_required` contract for a different commit.

Choose the next route:

| Outcome | Route |
| --- | --- |
| Passed; another slice remains | Finalize the slice under `Git Policy`, then plan the next slice. |
| Passed; no slice remains | Finalize the slice, run `Final AC Closure`, then hand off to Iris. |
| Implementation review `needs_changes` | Return to the same Implementation Engineer, then a focused reviewer delta review. |
| Implementation review `blocked` | Resolve the named source, evidence, access, or authority issue, or investigate. If the blocker is important engineer-owned execution evidence that the reviewer and validator may not produce, return to the same Implementation Engineer for the smallest round that completes it, then resume review. |
| Implementation review `challenge_required` | Launch the Independent Final Validator from that immutable review packet. The named challenge stays open until a matching `not_broken` result, or a routed defect, inconclusive result, or blocker, resolves it. |
| Validator `confirmed_defect` | First resolve any reported cleanup blocker. Then return to the same Implementation Engineer and the affected reviewer delta review. Rerun the validator only when the new review again publishes `challenge_required`. |
| Validator `inconclusive` | Launch `investigator` from the validation packet. |
| Validator `blocked` | Resolve only the named probe authority, environment, or cleanup need. Prefer letting the validator recreate its own disposable runtime. Return to the Implementation Engineer only when tracked preparation or a product correction is truly needed. |
| Investigation `root_cause_found` names a tracked correction | Route to the Implementation Engineer. |
| Investigation `likely_cause_found` | Route the verification step it names to that step's owner. |
| Investigation establishes only a no-edit execution correction | Relaunch the validator from the still-valid `challenge_required` review. |
| Investigation conclusively invalidates an adversarial challenge | Close only the matching challenge IDs for the exact reviewed commit. No reviewer restamp is needed. |
| Investigation finds neither an actionable defect nor remaining work outside an open adversarial challenge | Report and stop. An open challenge may stop only through conclusive invalidation, a successful rerun, a correction, or an explicitly owned blocker. |
| Plan or roadmap is no longer safe | Revise or re-plan before continuing. |
| Source or product intent is missing | For Iris work, return the gap to Iris. For work the user assigned directly, end your turn with `Status: needs_decision` (see `Turn Status`). |

## Direct Repository Edits

Do not edit product repository files yourself unless your launch prompt explicitly requests that specific edit.

Any direct tracked edit still goes to the Implementation Engineer to inspect, complete, validate, commit, and publish. The same review, test, and runtime evidence rules then apply. Do not skip evidence the changed risk requires.
