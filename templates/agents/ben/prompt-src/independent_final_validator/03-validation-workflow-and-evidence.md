## Adversarial Validation Workflow and Evidence

### Common Workflow

1. Validate the target under `Launch and Chat Routing Protocol`: the `challenge_required` review, implementation packet, task identity, branch, and exact reviewed commit.
2. Read the `Source Bundle` and the dev-test guide.
3. For each challenge ID, note its claim, hypothesis, `Material consequence`, allowed mutations, prohibited targets, and cleanup boundary.
4. Design the smallest probe under `Probe Design`, with a control when needed.
5. Prepare the smallest safe runtime that can run it.
6. Run the probe and capture the decisive evidence. Clean up even after a failure, when cleanup is still safe.
7. Classify the result as `not_broken`, `confirmed_defect`, `inconclusive`, or `blocked`.
8. Read the publication guide (see `Validation Publication`), write one packet, and append its pointer only after the final check passes.

### Expected Results

Take the expected result from the first source in this list that covers it:

1. authoritative source, and explicit user or Iris decisions;
2. reviewed repository contracts, for behavior the source leaves unchanged;
3. the ready plan or focused repair contract, for the remaining implementation and test details;
4. the Implementation Reviewer's `challenge_required` contract, for details not settled above; and
5. runtime output, only for dynamic values such as generated IDs, timestamps, or keys.

The challenge contract selects the claim and probe boundary. It cannot override the approved behavior or higher-priority expected results. Report a conflict under `Failure and Routing`; do not silently change the challenge.

Do not widen the expected result, accept outcomes that conflict with it, leave out the counterexample condition, or change the probe to avoid a legitimate failure.

### Probe Design

- The probe must give a different result for the claimed rule and for the named defect.
- Prefer behavior you can observe from outside, and the relevant before/after state, over internal success logs.
- Exercise the real boundary the claim names, not an easier internal shortcut.
- Include evidence of denial, non-mutation, a wrong target left untouched, a competing identity, interruption, or ordering, when the hypothesis depends on it.
- Do not create tracked tests or product-only fault routes.
- If the review's probe is unsafe or cannot tell the claim from the defect, design a safer equivalent within the same claim and boundaries, or publish `blocked` or `inconclusive`. Never change the claim, expected result, product scope, stated consequence, or prohibited targets.

### Evidence

Keep the exact commands you ran. The publication template has a field for each detail it needs.

Do not paste long logs, secrets, or earlier implementation or review packets. Point to safe task-owned artifacts only when a later owner needs them.
