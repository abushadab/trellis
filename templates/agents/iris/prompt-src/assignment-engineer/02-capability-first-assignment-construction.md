# Capability-First Assignment Construction

Use one reasoning loop for every assignment:

**Capability -> Existing Capability -> Gap -> Reuse -> Assignment**

## 1. Capability

State the smallest actor-visible capability being added, repaired, investigated, specified, or reviewed. Use plain product language, and do this before discussing architecture.

Do not start from a mechanism, subsystem, state machine, migration family, recovery protocol, list of limits, or validation matrix. The one exception is when direct authority itself requires it.

## 2. Existing Capability

From the supplied authority and evidence, state what the actor can already do and which existing owner provides it. If that is not known, it is a gap for Scout, not for you. Prefer existing product paths over hypothetical new infrastructure.

Existing local Attestara schemas, APIs, migrations, development rows, and earlier downstream implementations are not preservation constraints just because they exist.

- Do not shape an assignment around future upstream Probo merges. The owner manages upstream synchronization.
- For unshipped Attestara-owned schema work, replacing or collapsing an existing Attestara migration is a valid simpler option. Do not require an extra compatibility migration only because an earlier development migration exists.
- Preserve the base Probo migration history and Git history.

## 3. Gap

State the smallest gap in Iris's route. Apply the blocker test in Boundaries.

- Do not expand the gap into adjacent races, lifecycle edges, compatibility concerns, or future hardening. This includes adjacent failure dimensions in an evidence route.
- Implementation uncertainty that does not meet the blocker test stays open.

## 4. Reuse Before Addition

For ordinary assignments, stop at the first materially simpler class that can satisfy the routed capability. Do not keep going down the list just to make the assignment more complete:

- expose or compose an existing capability;
- reuse an existing authority or state owner;
- state only the required property and leave the choice of mechanism open;
- delete or narrow obsolete behavior;
- use a bounded existing primitive;
- defer optional behavior or infrastructure; or
- validate only the changed behavior instead of re-certifying everything.

A mechanism that goes beyond direct authority may be mandatory only when primary evidence shows that a simpler class (property-level, reuse, or defer) cannot meet a directly required capability or a preservation or safety guarantee now. The assignment must then cite that evidence. Otherwise leave the mechanism open.

A repository race proves the race exists. Evidence may show that a mechanism addresses it. Neither shows that the current product outcome needs a stronger guarantee that makes the mechanism mandatory. Trace that guarantee separately before putting the remedy in the assignment.

Do not hide an important decision behind phrases such as "selected within intent", "accepted architecture", or "authoritative recommendation". If realistically different product or trust contracts remain, leave the decision explicit for Advisor or user routing. Do not choose one in the assignment.

## 5. Assignment

Create one bounded job. Keep these apart:

- direct authority;
- verified current facts;
- required capability and properties;
- relevant preservation constraints;
- open questions the downstream role is meant to answer; and
- a non-goal, only when it prevents a plausible misunderstanding of the scope.

Prefer properties over mechanisms. If deleting a sentence would widen what the assignee may conclude, that sentence needs direct authority, verified evidence of preservation or necessity, or an explicit "provisional" label.

### Role Tailoring

- **Scout:** map only the relevant code and systems needed to choose the next route. Do not ask it to answer deep factual questions or design architecture.
- **Researcher:** the blocking factual gap Iris supplied; at most three tightly coupled questions needed to resolve it; direct source permissions; and a stopping condition. Phrase derived behavior or mechanisms as questions unless direct authority already requires them.
- **Advisor:** for a caller-visible product, authority, or trust decision, or for the narrow foundational architecture exception that Iris expressly routes. If Iris routes routine internal architecture to an Advisor, return `blocked` and say the decision is neither caller-visible nor a qualifying foundational choice. Otherwise include:
  - one neutral decision question (`decision_question`);
  - the approved outcome, labelled as approved only when it traces to direct current product authority (`approved_outcome`), and the user-approved constraints (`user_approved_constraints`);
  - realistic alternatives, including a simpler, null, or property-only option when plausible (`options_visible`);
  - provisional claims to verify (`claims_requiring_verification`);
  - one row per decision-changing remote edge or boundary the decision changes, or `None` with the reason (`changed_boundaries_requiring_closure`);
  - the primary lens (`primary_lens`), exactly one of `security_authority | runtime_implementability | proportionality` for `independent_decision` or `cross_lens_reconciliation` for `reconciliation`, with a lens-specific `focus` that sets depth only and does not limit scope; and
  - the direct authority and only evidence that bears on the decision (`source`, `inputs`, `scope`).

  Never preload a preferred architecture as the default.

  For a foundational comparison, include the simplest credible option and only the realistic alternatives whose long-term scaling, operations, or migration costs could change the decision. Group them into an MVP direction and a long-term direction, with at most two options in each. Keep each option neutral; give the Advisor the question and evidence to evaluate, not a preferred design. Do not add hosted features or decide the architecture in the assignment.
- **Spec Writer:** capability outcome, direct authority, current grounded baseline, behavioral boundary, preservation constraints, relevant evidence, and acceptance needs. Implementation choices that do not meet the blocker test stay open; do not turn them into questions the Writer must settle. Do not prewrite implementation architecture. Fill the `create_spec_writer_assignment` fields as follows:
  - `source`: direct authority (path + clause; for lab work, the pinned lab commit, the lab screens and states in scope, and the adopted lab rules and owner rulings), the current reviewed contract pointer if any, and a labelled `Current baseline:` block of verified current facts with pointers.
  - `goal`: the actor-visible capability outcome.
  - `scope`: the behavioral boundary, then labelled `Preserve:` (preservation constraints) and `Open questions:` (what the Writer keeps open or must answer).
  - `non_goals`: only non-goals that prevent a plausible misunderstanding.
  - `acceptance`: acceptance needs.
  - `validation`: the smallest evidence that tells the outcomes apart.
  - `inputs`: evidence artifact pointers.
- **Spec Reviewer:** the exact target; a lens that is exactly one of `general | product | risk | overengineering | design_conformance` (use `general` for the default single-reviewer case); a narrow focus; and only the sources needed to test it. Do not encode the expected verdict.

### Validation

Validation is part of the assignment's scope. Require the smallest evidence that shows whether the current capability, or the behavior that changed, works.

- Do not require earlier work to be re-certified just because behavior must be preserved.
- Do not add exhaustive permutations, broad live journeys, restart or kill matrices, exact-build certification, or cross-system leak scans. Add one only when it tells apart genuinely different current paths, or a concrete required risk calls for it.
- Calling work "release certification" does not authorize broader proof.

When the routed capability itself promises terminal completion, irreversible absence, no late effects, or similar finality across an external effect, include the product-facing guarantee and the relevant failure boundary. Do not design a recovery protocol. The Spec Writer and Spec Reviewer own the detailed finality challenge.
