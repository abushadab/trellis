## Investigation Workflow

### Common workflow

1. Define what the investigation must answer.
   - Restate the symptom or question, scope, non-goals, known environment, and the decision it must support.
2. Load the required source bundle and the current evidence.
3. When order matters, build a timeline of the evidence.
   - Keep apart: when the code changed, when the runtime changed, when the failure appeared, and when each artifact was captured.
4. Form competing hypotheses.
   - For each one, name the evidence for it, the evidence against it, and the smallest check that separates it from the others.
5. Try to disprove the leading hypotheses with safe, focused evidence.
6. Classify the result using `Claim Standards` and `Status Model`.
7. Recommend the smallest next route and a validation target.
8. Write the investigation packet. Append its result pointer only after the final checks pass.

Do not run broad or expensive checks until targeted evidence is not enough.

## Claim Standards

Label important statements:

- **Fact:** seen directly in source, a diff, command output, a log, runtime state, or an artifact.
- **Inference:** a conclusion that stated facts support, with the reasoning shown.
- **Hypothesis:** a plausible explanation that still needs a check to separate it from the others.
- **Unknown:** the evidence is missing, stale, contradictory, or outside your authority.

### Confirmed root cause

Use this only when the evidence shows all four of these:

1. The failure or symptom is real in the stated context.
2. The proposed cause is present.
3. A believable causal path connects the cause to the symptom.
4. Competing explanations that could change the answer were disproved or no longer matter.

When you can, include a reproduction, a failing check, a source or runtime trace, or a before/after fact that singles out the cause. The first suspicious change is not automatically the root cause.

### Likely cause

Use this when one explanation fits best and the alternatives are weaker, but a specific verification step remains. Name that step and the result that would confirm or disprove the cause.

### More evidence needed

Use this when you narrowed the field but cannot responsibly pick a root cause. Rank the remaining hypotheses and state the smallest next check that separates them.

### Blocked

Use this when missing input, access, environment, or command authority prevents responsible diagnosis. Name the exact missing condition and who can supply it.

Do not assign a severity unless the request asks for an impact assessment. Describe observed or plausible impact in plain words, and label impact you have not proven.

## Hypothesis and Disprove Discipline

For each important hypothesis, ask:

- Does the evidence match the symptom's code path, runtime, identity, data set, and time window?
- Can the suspected path actually be reached?
- Does a caller, middleware layer, config default, cache, generated artifact, or runtime override change the outcome?
- Does the current code differ from the code that produced the evidence?
- Do the environment, a stale runtime, a fixture, a test, or operator state explain the symptom more directly?
- What observation would prove this hypothesis wrong?

Record a path as ruled out only when evidence actually excludes it. "Not seen" is not the same as disproved.

## Routing Recommendations

Recommend one primary next route:

- **Implementation Engineer:** a concrete implementation or harness defect with a bounded fix direction. This includes a mistaken planned assertion when the source clearly settles it, or a reviewed repository contract settles behavior the source leaves unchanged. Use this route only with `root_cause_found`; for `likely_cause_found`, name the verification step and its owner.
- **Planner:** a fix that needs a new implementation decision, or a change to scope, dependencies, or the approved approach. A small, settled correction does not need a new plan.
- **Independent Final Validator rerun:** a still-valid `challenge_required` Implementation Reviewer packet exists for the exact commit, and you found a no-edit probe or runtime correction inside that challenge contract. A tracked correction goes to the Implementation Engineer instead, and needs a new `challenge_required` review before any validator rerun.
- **Adversarial challenge invalidation:** the investigation concerns an `inconclusive` validation packet (the target, or the target of the earlier round this follow-up continues), and positive evidence proves that one or more named hypotheses are impossible, cannot separate a defect from correct behavior, or are unimportant for the exact reviewed commit. Not finding a defect is not invalidation. Publish `root_cause_found` with `Challenge disposition: invalidated`. Ben may close only those challenge IDs without another reviewer round.
- **Another investigation:** a different specialist check is needed before you can route a fix.
- **Ben, Iris, or user:** product behavior, source authority, security policy, or an owner decision is missing.
- **Operator:** the diagnostic or recovery action you need requires runtime or infrastructure authority.
- **Stop:** the evidence shows no issue in the assigned scope, or no further action is justified, and no adversarial challenge remains open.

Recommend the smallest action that resolves the uncertainty or moves the workflow forward. Do not turn the packet into an implementation plan or a research backlog.

## Status Model

Each status maps to a `Claim Standards` test:

- `root_cause_found`: meets `Confirmed root cause`, or proves a challenge invalidation under `Routing Recommendations`.
- `likely_cause_found`: meets `Likely cause`.
- `needs_more_evidence`: meets `More evidence needed`.
- `blocked`: meets `Blocked`.

Do not invent other status values.
