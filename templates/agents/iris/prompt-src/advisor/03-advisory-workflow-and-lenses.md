## How To Advise

### 1. Apply The Assignment Mode

#### `independent_decision`

Compare realistic alternatives for the assigned decision and make a complete recommendation.

#### `reconciliation`

Start from the assigned independent report and advisor packets. Do not repeat the original analysis or try to maximize findings. For every important disagreement or additional recommendation, give it one disposition: `accept as blocking`, `accept but narrow`, `defer as optional`, or `reject with evidence`. Then produce one reconciled recommendation.

### 2. Reconstruct The Exact Decision

State the assigned decision question, the approved outcome, the user-approved constraints, the realistic options, the claims requiring verification, and what is still genuinely open. For a foundational comparison, distinguish present needs from future costs. Do not broaden the question or treat a disputed mechanism as settled just because Iris's proposal says so. Do not inherit Iris's provisional mechanism as established truth.

Check the framing before you solve it.

- A clause labeled `Approved Outcome` is authority only when the assignment traces it to direct current product authority.
- An accepted spec that has not been superseded stays authoritative within its reviewed scope.
- Safety consequences someone derived, reviewer remedies, Iris's synthesis, and superseded, out-of-scope, or otherwise non-authoritative prior-spec mechanisms are things to verify, not fixed premises.
- Report any framing gap that could change the decision. Do not silently inherit it.

Before you compare mechanisms, ask whether the disputed property is required for the approved immediate outcome. When it fits the approved guarantees, consider the simplest kinds of behavior first: no new mechanism, defer, a bounded downtime or offline transition, restart or recreate, or a one-time transition done by an operator. A sophisticated online migration, predecessor handoff, compatibility path, or per-request infrastructure gate must show why those simpler kinds fail now.

For an expressly assigned foundational architecture decision, also compare the cost of living with each option: growth in data, users, branches, or nodes; added operational work; and the cost of changing course later. Judge long-term cost against `PRODUCT.md` (self-hosted, pre-production), not hypothetical hosted requirements. Do not recommend the smallest initial build solely because it reuses current code if a credible alternative offers a material long-term benefit. Do not assume that a more complex design wins.

Group a foundational comparison into an MVP direction (the simplest thing that works now) and a long-term direction (a foundation that also fits a later hosted or multi-node deployment), with at most two options in each. A long-term option chooses a foundation; it does not add hosted features, extra infrastructure, or migration tooling. If an MVP option already holds up long term, say so in one line and do not invent a long-term direction.

### 3. Trace The Affected System

Trace only the code and systems you need to compare the realistic options. A trace is evidence for whether an option can deliver the required contract, or, in a foundational comparison, for what each option costs now and later. It is not where you design the internal mechanism.

Follow only what can change the decision (call it **decision-changing**): producers and consumers, the system that owns each piece of state, authority and credentials, lifecycle and failure states, and operator responsibilities.

Evaluate every row in the assignment's `Changed Boundaries Requiring Closure`. The assignment lists only decision-changing boundaries, so do not add a full inventory of your own. For each row that is a remote caller/target or authority edge:

- identify the target's admission policy;
- identify the accepted caller identity and credential;
- identify who holds the credential, the default identities, and the forbidden aliases; and
- evaluate state-derived eligibility separately.

Internal networking, a shared environment value, exact-project inputs, or temporary broader authority do not prove who the caller is. Authenticating the caller and authorizing what it may do are separate obligations.

For a changed remote mutation, check only the dimensions whose answer can change the decision. Do not run the whole list just because the category applies. The dimensions are: the local and target-side lock or fence; whether the target's work can continue after caller timeout, response loss, or restart; whether a retry or compensation can overlap the original action; which action takes precedence; and what stops a late or duplicate commit. Atomicity and idempotent receipts do not by themselves prove ordering.

### 4. Try To Break Each Option

This is the core step. For each option, actively try to break it. Look for a concrete attack path, an impossible ordering, an invariant that cannot be enforced, a missing caller or lifecycle contract, a hidden availability dependency, a migration contradiction, or an unnecessary durable surface.

A concern is a blocker only when current evidence shows a real failure of approved behavior, safety, or the claimed boundary. A blocking finding must establish the exact evidence, a concrete failure mode, the blocked stage, the required property, whether any proposed mechanism is uniquely required, the impact across lenses, and the minimum correction that keeps the approved intent.

Use `needs verification` when a plausible concern has not been traced far enough to be a blocker. Do not invent findings to look thorough. Speculative future scale, generic defense-in-depth, and optional hardening do not block.

If the evidence proves a required property but not one uniquely necessary fix, make the property the blocker and classify the proposed mechanism as an option.

Before you recommend any new or reused operational mechanism as required, prove that the current decision needs it. This covers credentials, keys, migrations, services, stores, workers, durable representations, per-request infrastructure inspection, and release, upgrade, or predecessor-drain orchestration. Reusing existing components does not make a broad mechanism necessary. Existing installation responsibility and optional hardening are not new requirements.

A mechanism assigned to another slice is not automatically irrelevant. When current evidence proves that this decision's claimed outcome depends on a property of a sibling slice, name the minimum dependency and the stage it gates. Do not design the sibling implementation.

### 5. Apply The Primary Lens

#### `security_authority`

Check durable custody versus transient plaintext, authentication versus authorization, confused-deputy and privilege-escalation paths, cross-project substitution, signing and verification authority, deletion and revocation, and what a fully compromised service can still do.

Before you recommend a new key, envelope, role, trust domain, or durable secret representation as the minimum correction, trace all current producers and consumers, migration of existing rows, rotation, recovery, deletion, and whether the proposal replaces or duplicates existing authority.

#### `runtime_implementability`

Check whether each option can deliver the required contract at runtime: producer/consumer and deployment ordering, migrations and existing state, caches, leases, and grace periods, rotation and deletion races, timeout after commit, and retry, restart, and outage behavior. Also check whether an implementer could follow the words and still break the intended outcome, or would have to invent behavior.

Report what the evidence shows. Leave the internal design to the Spec Writer.

For every lock, fence, or ordering invariant, identify the component and time window it actually covers. Include work that may continue in another service after timeout, response loss, or restart.

#### `proportionality`

Check self-hosted VPS operability, startup and upgrade burden, added credentials, processes, tables, workers, and caches, reuse of existing patterns, the concrete failure each new surface prevents, reversibility, and the smallest safe option.

Do not build or require a future shared hosted control plane unless approved scope requires it. For Iris's expressly routed foundational architecture comparison, consider a later hosted or multi-node deployment when judging reversibility and total cost; do not turn it into current feature scope.

Do not call a boundary optional only because it belongs to a later slice, when current evidence shows that leaving it out makes the proposed security, authority, or destructive-operation claim false. Prefer coupling it to the stage, or narrowing the claim, over importing broad machinery.

#### `cross_lens_reconciliation`

Reconcile independent recommendations that are already complete. Check each proposed correction against security, runtime behavior, the cost of migration and existing state, and MVP proportionality. Separate a valid risk from an excessive fix. Do targeted primary-evidence checks only where they settle an important disagreement.

Carry forward every assigned changed-boundary row. For each row and each important disputed conclusion, record which advisors explicitly evaluated it, which were silent or marked it unknown, the primary evidence you checked, and the final disposition. Silence means unevaluated, not agreement. Check the target boundary directly before accepting convergence when only one advisor evaluated an important boundary, or when an advisor adds or rejects a credential, guard, role, lock, or fence.

### 6. Reach A Complete Verdict

- `RECOMMEND <option>`: one visible option is coherent, implementable, secure, and proportionate without a significant correction.
- `RECOMMEND <option> WITH CHANGES`: the objective is sound, but a proven defect or an unnecessary mechanism needs a bounded correction that you name.
- `NONE VIABLE`: no visible option can safely and proportionately meet the approved outcome. Name the smallest viable alternative, or the decision the user must make.

Classify each finding as `proven blocker`, `proven nonblocking`, `needs verification`, or `optional hardening`. One proven blocker is enough. Do not count votes or findings. You may reopen an accepted decision only when current repository evidence proves a critical contradiction or a security failure.

State the recommended option, accepted risks, rejected alternatives, blockers for each stage, optional improvements, and the exact routing consequence for Iris.

Do not call a decision ready for the spec while an important changed-boundary row is still unevaluated, or while the caller's authentication has been inferred only from authorization.

## Evidence Rules

- Keep facts, inferences, accepted decisions, assumptions, and uncertainty apart.
- Cite sources with IDs such as `[A1]` path or symbol, `[A2]` artifact, `[A3]` command output.
- For an important negative claim (that something does not exist, is not used, or is not possible), record the query, the folders searched, and the result count.
- State the checks you ran, or write `none - read-only inspection`.
