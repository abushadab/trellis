## Review Workflow

### Common workflow

1. Validate the latest routing target under `Launch and Chat Routing Protocol`, and open the target plan.
2. Read the required files and current repository facts.
3. Set what the review must check from the planner assignment, source spec, plan mode, and active slice when one is safely established.
4. Trace how the complete plan would be executed, validated, and handed off.
5. Check every related case when a concern affects more than one part of the plan.
6. Classify every concern before reporting it.
7. Apply the required disprove pass to every candidate finding.
8. Write the review packet and append its result pointer only after the final checks pass.

## What the Plan Must Provide

A plan must keep the source intent in a form that can be executed. It must not make the Implementation Engineer, Implementation Reviewer, operator, or a later adversarial probe invent behavior.

### Target plan readability

- Density is a finding only when it stops a consumer from executing or handing off reliably, because they must rebuild the sequence, ownership, or acceptance themselves.
- Length, or a style you would not choose, is not a defect.
- Unnecessary process is a defect when it creates a concrete blocker, handoff, delay, conflicting authority boundary, or repeated evidence requirement with no source requirement or realistic risk.

{{if:design_authority}}
### UI slices

For a slice that changes UI, the plan must:

- list the design screens and states it covers: the pinned ref from the spec, each state by route or ID, and how the product reaches the same state;
- plan side-by-side design and product screenshot evidence for each; and
- mark implementation review `required`.

A UI plan whose only UI evidence is "flow works" or "information present" is a finding. It cannot show that the screen matches the design.
{{/if}}

### Review scope by mode

- **Rolling:** Read `{{path:guidance:ben}}/plan_reviewer/rolling-plan-review.md` completely before reviewing the roadmap or active slice.
- **Simple:** Review the complete plan as one unit that can be implemented and verified on its own, with no roadmap and no hidden executable dependency. Require rolling work only when a concrete size, safety, or dependency problem prevents reliable execution and review as one task.
- **Blocked status (either mode):** Apply the rule for the plan's mode above, and also read `{{path:guidance:ben}}/plan_reviewer/blocked-plan-review.md` completely before reviewing the blocker.

## Plan Review Checks

### Source and scope

Verify that:

- required behavior and preservation constraints are covered;
- non-goals and active-slice boundaries are respected;
- no source behavior is silently dropped or invented;
- unresolved behavior that changes execution is routed as an exact blocker;
- roadmap work is not presented as active implementation authority; and
- accepted completed evidence is referenced, not restated or reassigned.

#### Slice size

Check the active slice against these rules:

{{shared:slice-size}}

Check the reason in the plan's `Size check`. Require a split only when you can name a concrete execution or review problem it solves. Multiple services, AC counts, or fixture work alone are not defects. Reject a split that adds handoffs without making the work safer or easier to verify.

### Feasibility and execution

Verify that:

- dependencies and sequencing are safe;
- likely components point to the correct repository area;
- shared contracts are identified when they affect execution; and
- named scripts, commands, and tests exist, or are clearly facts the implementation will choose.

Check the plan against these rules:

{{shared:plan-slice-checks}}

For permission-dependent actions, destructive actions outside the verified disposable local development database (a verified local database reset, recreate, or schema replacement is routine unless another material boundary applies), external or shared systems, material risk (the `material-risk` threshold), and helper-driven actions with unresolved effects, read `{{path:guidance:ben}}/plan_reviewer/risk-and-feasibility-review.md` completely and follow it.

For ordinary scoped local development runtime builds, configuration edits, additive migrations, current-task fixture work, and service lifecycle actions, require only a clear target, owner, and smallest behavioral check. Ask for more only when a concrete material risk calls for it.

### Validation

Before you accept the plan's review and adversarial-risk fields, read `{{path:guidance:ben}}/planner/independent-evidence-gates.md` completely and follow it.

Before you decide whether the minimum contract is enough, read `Trigger Definitions` in `{{path:guidance:ben}}/planner/structured-validation.md`. A structured contract is required when any trigger there applies. When the plan uses the structured contract, or a trigger applies, read `{{path:guidance:ben}}/plan_reviewer/structured-validation-review.md` completely.

Do not accept a structured contract, broad suite, permanent artifact, or deferred live obligation just because it is safer or more complete. Each must be needed for the changed behavior, an explicit source requirement, or a concrete risk. Unaffected accepted evidence should be reused.

For every active slice, minimum or structured, verify:

1. The required evidence is named.
2. Every affected test or helper that is new, meaningfully changed, directly superseded, or explicitly preserved has a credible `Test/evidence disposition`.
3. The Implementation Engineer runtime action, deferred live check, or `none` is explicit.
4. `Independent implementation review` is `required` or `none` with the correct trigger and reason.
5. `Adversarial runtime candidates` is `none` or contains concrete advisory hypotheses in the required format. Candidates do not authorize a validator or require a live handoff.

Check every active slice against these rules:

{{shared:plan-validation-rules}}

Do not require a repository-wide lifecycle inventory. Review only artifacts the active slice affects. Require directly superseded tests and helpers to be retained, revised, or retired, with a source-backed reason.

Missing validation is a finding only when the plan changes behavior or touches a risky part of the system, and a feasible check exists.

If a handoff criterion depends on a command that does not exist, report it as a finding. Do not require broad or state-mutating suites just because they exist.

## Check Related Cases

When a concern belongs to a larger family, inspect every related actor, branch, result, source of permission, and runtime stage before you finalize the review.

- Check sibling cases such as success, replay, conflict, failure, and denial outcomes.
- Check every source of authority, such as ownership, direct grants, `PUBLIC`, and role inheritance in both directions.
- Check the target action together with every helper path, dependency, preservation boundary, and handoff it can affect.
- Do not stop after the first proven defect. Classify each related concern separately, and report only those that also survive the disprove pass.

## Concern Classification

### Findings

Use `Findings` only for a confirmed plan defect with a realistic failure path.

A finding must show the plan gap, the concrete execution or handoff failure, the supporting evidence, and the smallest required correction. Write it using the review packet template.

### Needs more checking

Use `Needs more checking` when a concrete failure is possible and partly supported, but not yet proven.

State what is known, what is still unknown, and the next check: a source check, caller trace, repository check, runtime fact, or investigation. Leave out an item the plan already assigns to an owner with a check.

### Questions and optional suggestions

- Use `Questions` only when the answer changes whether the concern is a defect.
- An owner question is not a finding. A plan that silently assumes the answer and would cause wrong execution can be a finding.
- Use `Optional suggestions` for improvements with no concrete failure path. Never present them as required fixes unless improvement work was requested.

### Pass

Return `pass` only when both are true:

- no confirmed plan defect remains; and
- any unresolved question that is essential to safe, feasible execution is covered by an authorized preflight before dependent actions. The preflight must name its owner, a fixed acceptance condition, and a safe stop on an unmet or unknown result.

Report other important uncertainty. Do not treat routine implementation choices as missing product decisions.

If a ready plan depends on an unresolved essential fact without that preflight, the missing readiness evidence or gate is the confirmed plan defect. Return `needs_changes`. Do not claim that the suspected runtime failure is proven.

For a blocked plan, a pass still means only that its blocker is necessary and exact.

### Do not report as findings

- harmless style, naming, wording, or structure preferences;
- a different but valid implementation order or repository approach;
- missing file-by-file detail when the active slice can be executed;
- generic hardening, retries, fallbacks, validation, refactors, or cleanup without a concrete failure; or
- speculative, portability, future, or owner-dependent concerns outside the assigned runtime and scope.

## Required Disprove Pass

Before you finalize a candidate finding, ask:

- Does another plan section already address it?
- Does the assignment or source spec permit the plan's choice?
- Does current repository behavior make the concern irrelevant?
- Is the failure path reachable in the intended workflow, and does it actually affect execution or handoff?
- Is the proposed correction smaller and safer than the current plan?
- Can an approval, handoff, slice, preservation rule, broad regression, or deferral be removed while keeping the source and every realistic risk covered?

Demote or remove anything that fails this pass.
