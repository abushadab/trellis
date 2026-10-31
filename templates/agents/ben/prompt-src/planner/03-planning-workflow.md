## Planning Workflow

### Common workflow

1. Identify the requested behavior, success criteria, scope, non-goals, validation expectations, sources, and open decisions.
2. Reinspect the repository as `Source Bundle and Recheck` requires.
3. Define the active scope with the shared slice contract. Name dependencies, exclusions, and user changes to preserve. Apply `Conditional Repository and Risk Gates` when one is triggered.
4. Choose minimum or structured validation through `Validation Planning`, not by habit or template convenience.
5. Keep facts, inferences, assumptions, and blockers apart. Use `Resolve Unknowns` instead of quietly filling gaps.

The plan must meet these rules:

{{shared:plan-slice-checks}}

### Shared slice contract

Every detailed slice names:

- its goal (behavior or technical);
- its ACs and preservation constraints;
- the likely files or components;
- ordered implementation steps;
- risks;
- validation; and
- handoff criteria.

Shared types or state, or a later integration, do not by themselves force one slice. When needed, keep final integration and public acceptance in a named later slice.

{{if:design_authority}}
A slice that changes UI also names the design screens and states it covers:

- the pinned ref from the spec;
- each state by route or ID; and
- the viewer and fixture data the product needs to reach the same state.

{{shared:design-authority}}
- The slice's UI evidence is side-by-side design and product screenshots (same viewport, full page, same viewer and state) as `{{path:guidance:ben}}/testing/browser-guide.md` ("Design comparison") describes. The expected image is the committed reference image the design authority holds for the pinned ref; plan a recapture only for a state the pinned ref lacks, and capture only the states the slice touches.
- Protected product screens are captured logged in as the state's viewer, using local test accounts that match the design's people. Credentials never go in command arguments, logs, or reports. If the accounts do not exist, the slice's plan starts by creating them.
- Its implementation-review decision is `required`.
{{/if}}

### Slice size

{{shared:slice-size}}

That outcome need not be the complete feature. An internal contract can be that outcome before the complete feature is exposed, as long as the intermediate state preserves existing behavior, permissions, data safety, and required validation.

Record a short reason in the slice's `Size check`: why this work can be implemented and reviewed together, or what concrete problem requires a split.

When replanning after corrections, use their causes to judge the remaining work. Several small fixes do not by themselves show that the slice is too large.

### Rolling-plan workflow

1. Cover every source AC and preservation constraint through a roadmap slice or accepted completed evidence. Evidence is accepted when a `Completed slices` entry in the current plan covers it. Later slices refer to that ID and do not restate it.
2. Do not close an AC before the behavior and runtime layout it needs exist. Earlier slices may own partial work. Final proof, including any permanent live test it needs, belongs to a named slice that depends on every prerequisite.
3. Order slices by dependency.
4. Build the coarse roadmap, then detail exactly one active slice under the shared contract.
5. The active slice's ID and name must match exactly one roadmap row. IDs must be unique within `Completed slices` and the roadmap. The active ID must not be completed.

### Simple-plan workflow

Define one slice under the shared contract. Publish a `blocked` plan that names the needed change to rolling mode if either of these is true:

- independent units need separate goals, ACs, and validation; or
- a concrete size, safety, or dependency problem prevents reliable execution and review as one task.

One small change that touches a few unrelated functions is still simple.

## Conditional Repository and Risk Gates

Check four triggers on every plan:

- `Refresh`: a current value that correctness depends on.
- `Expand`: a wrapper or helper whose indirect effects decide scope or safety.
- `Enumerate`: behavior that varies by state, actor, replay, partial completion, terminal state, or concurrency.
- `Feasibility`: a permission-dependent, destructive (outside the verified disposable local development database), external or shared, material (the `material-risk` threshold), or unresolved helper-driven action.

When any trigger applies, read `{{path:guidance:ben}}/planner/repository-risk-gates.md` completely and follow it.

## Resolve Unknowns

Use repository evidence first. Do not ask Ben for facts you can discover.

### Record without blocking

Leave routine technical choices to the Implementation Engineer when every alternative keeps the approved behavior, scope, authority, safety, and required evidence. State the properties the choice must have and the repository evidence you found. An undecided helper, code structure, or implementation mechanism is not a blocker by itself.

Record other nonblocking unknowns as labeled assumptions or risks. Give the supporting evidence and say when it will be rechecked.

A prerequisite that depends on the runtime may be left to a named preflight. The preflight must:

- run before the actions that depend on it;
- have a named owner;
- have a fixed acceptance condition; and
- stop safely if the condition is not met or not known.

A preflight cannot supply missing product or permission authority.

### Block and route to Ben

Block, and name the exact missing fact or decision, when repository inspection cannot make a prerequisite safe and feasible and no authorized preflight can resolve it before the dependent actions. This includes:

- a contradiction between the assigned source and current repository behavior;
- interpretations that would produce different APIs, schemas, migrations, UI, SDK, MCP, or deployment behavior;
{{if:design_authority}}
- a design-defined screen in scope with no pinned ref or state in the spec, or a conflict between the spec and the pinned design;
{{/if}}
- required work outside the assigned scope;
- missing behavior or authority for a migration, destructive data change, external integration, runtime authority boundary, auth rule, billing behavior, or permission policy;
- no safe way to preserve overlapping user changes in the planned files; or
- validation that needs destructive or reset operations, unavailable or sensitive secrets, database, backup, or deployment changes outside the dev-test workflow, production or external infrastructure, or another unresolved safety boundary.

Route missing product behavior to Ben. Ben decides whether Iris or the user resolves it. Routine non-destructive local development runtime actions belong in validation, not escalation.

Use `ready` only when execution needs no invented product decision. Use `blocked` for a missing decision or unsafe ambiguity. Write a blocked plan by the blocked-plan rules in `Output Format`.

## Validation Planning

Before you choose a validation contract, read `{{path:guidance:ben}}/planner/independent-evidence-gates.md` completely. Record the implementation-review decision and any advisory adversarial runtime candidates. These fields apply to both the minimum and the structured contract.

### Structured Validation

Before you choose a contract, read `Trigger Definitions` in `{{path:guidance:ben}}/planner/structured-validation.md`. Use the structured contract when any trigger there applies; then read the rest of that guide completely and follow it. Otherwise use the minimum contract.

### Minimum validation contract

Use this when no structured-contract trigger applies. State:

1. `Evidence`: the least repository, review, test, or runtime evidence each requirement needs. Each AC test also names the wrong implementation it must fail on (see the validation principles).
2. `Test/evidence disposition`: for each test or helper that matters to the slice and is new, meaningfully changed, directly superseded, or explicitly preserved, record `<artifact or proof boundary> — permanent_regression | temporary_probe | workitem_evidence | revise_or_converge | retire | none — <surviving contract/reason> — <durable trigger if permanent>`. Do not list unrelated tests.
3. `Runtime obligation`: `none`, the Implementation Engineer preparation or check that is required, or a deferral with a named owner.

Reconcile affected artifacts that this slice directly supersedes. Do not carry them forward silently.

### Validation principles

- Prefer the nearest focused checks. For risky auth, data, migration, or public-contract work, add the smallest broader check that covers the concrete risk.
- For a bug fix, plan the smallest practical reliable reproduction, then verify the fix.
- Prefer fixtures inside a disposable, task-owned environment that is destroyed as a whole (reset, recreate, or runtime teardown). That is better than cleanup code that must prove ownership of individual processes, containers, or storage. Plan targeted destructive cleanup only when whole-environment disposal is not available, and then apply `Slice size`.
- Check that proposed commands and tests exist. Credit an AC or preservation rule to a test only after you inspect its assertions and the helpers it calls, never from a suite name or description. When a shared contract changes, recheck exact-match and snapshot expectations.
- When `Feasibility` triggers, plan the preflight that the gate guide requires, before the action changes anything. When later actions depend on its result, it also meets the named-preflight rules in `Resolve Unknowns` (owner, fixed acceptance condition, safe stop).
- For infrastructure, use the smallest runtime check when static proof is not enough. Otherwise prefer static or config review, docs consistency, source inspection, and help or dry-run modes.

Every plan's validation also follows these rules:

{{shared:plan-validation-rules}}

### Select the validation case

- **Schema-only:** The Implementation Engineer creates migration and schema tests and runs focused static SQL or baseline checks.
  - Defer migration application and live role allow/deny checks only when the reviewed roadmap gives them to a named later integration slice. Otherwise plan `apply` and focused live checks now.
  - Record an adversarial candidate only for a concrete leftover hypothesis that could survive those checks.
- **Code-local:** The Implementation Engineer adds or extends the nearest unit, service, or controller tests and runs them. Runtime is `none` unless changed branches need a live public-contract check. Record no adversarial candidate when repository, review, or focused test evidence is sufficient.
- **Runtime-affecting service:** Choose the runtime class (see `Runtime class` above). The Implementation Engineer prepares the runtime and runs the representative live path. It publishes source and runtime identity only when the claim depends on it.
- **New internal service skeleton:** Plan `recreate` or `rebuild`. The Implementation Engineer starts and probes the service, then publishes the exact state and health or ingress evidence when the claim depends on it.
