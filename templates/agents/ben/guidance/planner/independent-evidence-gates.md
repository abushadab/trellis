# Independent Review and Adversarial Runtime Signals

Use this guide to classify independent implementation review, and to record any candidate adversarial runtime risks, for every active slice or focused repair. Record:

```text
Independent implementation review: required | none — <trigger and reason>
Adversarial runtime candidates: none | <one or more candidate IDs and summaries>
```

Classify the claims and the boundaries that change, not only the file types. `None` is a positive decision and needs a reason.

A runtime candidate is advisory planning context. It does not authorize the Independent Final Validator, create a completion gate, or require the Implementation Engineer to keep a live runtime.

## Independent Implementation Review

Implementation Reviewer evidence is required for:

- authentication, authorization, tenant isolation, or important secret-custody changes;
- SQL or migrations affecting permissions, identities, durable data, ownership, or destructive behavior;
- concurrency, replay, idempotency, fencing, lifecycle, deletion, or recovery behavior;
- public contracts and cross-service authority or state transitions;
- cryptographic key generation, signing, verification, encryption, decryption, or trust selection;
- dynamic command or shell execution;
- filesystem path, write, delete, ownership, permission, or mount authority;
- untrusted-input handling where a bypass could affect authorization, data, commands, files, or privileged operations;
- permanent acceptance-test oracle changes used to close any preceding high-risk claim;
- any user-visible UI change; on a lab-defined screen the reviewer compares the product with the lab at the same states using the engineer's side-by-side screenshots; and
- any slice with a recorded adversarial runtime candidate, because the Implementation Reviewer must decide whether a residual challenge remains after implementation.

Ordinary local logic with credible focused tests, documentation, generated metadata, and behavior-preserving refactors may record `none` when no trigger above applies.

## Adversarial Runtime Candidates

Record a candidate only when all of these are plausible before implementation:

1. A material claim depends on actual runtime behavior.
2. A specific wrong implementation could survive ordinary source review and engineer-owned tests because the implementation and test harness might share the same mistaken assumption.
3. A bounded independent runtime probe could materially increase confidence by trying to disprove the claim.
4. The consequence would be material under the planner's risk threshold.

Candidate families that often qualify:

- destructive wrong-target or replacement-identity behavior;
- tenant, authorization, or credential-boundary bypass that depends on real runtime identity or ordering;
- concurrency, fencing, replay, or recovery defects that need a controlled race or interruption;
- irreversible or hard-to-recover data transformation whose failure mode may evade normal fixtures; and
- a runtime denial or non-mutation rule that a shared mock, helper, or fixture assumption could falsely prove.

Name as a candidate each material interruption risk that lacks credible evidence. Examples are a failure between durable steps, a lost response, or an owner replacement. The plan's `Durable steps` section shows where these can happen. Planned evidence is credible when it actually exercises or settles that interruption, not only the normal path. Do not name a candidate, or plan a failure injection, for every interruption boundary.

Built images, service startup, Compose, databases, migrations, Docker, auth, permissions, secrets, or cross-service work do not by themselves justify a candidate. Engineer-owned focused and live evidence may close those claims when it is trustworthy.

Give each candidate a stable ID and two parts:

- the source-backed claim and its plausible defect or counterexample; and
- why ordinary review and engineer tests might miss it.

Do not prescribe a validator command, a fixture layout, or a live-runtime handoff.

From the finished implementation, the Implementation Reviewer decides whether to publish `pass` or `challenge_required`. It may refine, replace, or reject plan candidates. It may also name a new residual hypothesis from the actual diff and evidence.

## Review Of The Decision

The Plan Reviewer rejects a missing or incorrect implementation-review classification. It also rejects:

- a mandatory validator route;
- a plan-time `required` runtime-validation gate;
- a preserved-runtime handoff created only for a later rerun;
- an adversarial candidate that lacks a concrete plausible defect and a consequence that meets the threshold; and
- a missing candidate for a material interruption risk that lacks credible evidence.
