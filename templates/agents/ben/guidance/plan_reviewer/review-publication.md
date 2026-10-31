# Review Publication

## Writing Quality

These rules add review-specific writing rules to the shared `Writing` rules. They change how the review reads, not your scope or authority as reviewer, and they never turn a preference into a finding.

### Who Reads the Review

A plan review is a decision artifact, not a transcript of every check you ran.

- Ben needs the outcome and the routing signal. Keep the summary to the finding count, the highest-impact effect, and whether execution can proceed.
- The planner needs the exact plan gap, the failure, the evidence, the smallest correction, and how to verify it.

### One Finding, One Failure

Each finding describes one concrete execution failure. Split findings when the failures, the required plan changes, or the ways to verify them are independent. Report several symptoms of one root gap as one finding.

Keep the fields distinct, and do not repeat the same explanation in several of them:

- `Plan gap` names the exact missing or unsafe plan decision.
- `What fails` says what realistically goes wrong.
- `Evidence` proves the gap and the failure.
- `Smallest plan change` states the smallest correction.
- `How to prove the fix` states what the revised plan must require. Do not mix it into `Evidence`.
- `Confidence` reflects the evidence you already have.

### Evidence

Under `Evidence`, put one source or fact in each labeled bullet (`Source`, `Plan`, `Repository`, and `Outside source` only when needed, with a direct link). Put each citation next to its fact, and keep facts apart from the conclusion they support. Connect each fact to the failure.

Do not bury a proven defect under `Needs more checking`.

### Final Readability Test

Before publishing, ask:

- Can Ben identify the route from the summary?
- Can the planner find the exact correction without rereading the investigation?
- Can another reviewer check each evidence claim independently?

If not, restructure the review without lowering the evidence bar.

## Result Pointer

Append only after the review file passes the final check:

```md
Review ready: `<actual review artifact path>`
Status: `pass` / `needs_changes`
Summary: <one sentence result>
```

Choose the status with the `Pass` rules under `Concern Classification`.

## Output Format

Write one review file under `{{path:workitems_root}}/<workitem-id>/reviews/`, named `<slug>-plan-review-r<N>.md`.

`<slug>` is the plan file's slug (`<slug>-plan.md`). `<N>` is `1` for `Plan ready:` and the pointer's `Round` for `Plan revised:`.

Create a new file for each review round. Do not change files from earlier rounds.

Use this template for both `pass` and `needs_changes`:

```md
## Review target
- Workitem ID:
- Planning Task ID:
- Planning Task Name:
- Downstream slice (the plan's active or only slice; for a blocked plan, only when safely established): <ID> — <Name>
- Review round:
- Plan status: ready | blocked
- Target plan:
- Planner assignment:
- Source spec:
- Earlier review (revision only):

## Summary
- Result: pass | needs_changes
- <One to three sentences saying whether the plan can proceed in its declared state.>

## Findings
<Write `None.` when no defect was proven. Otherwise repeat the block below.>

### <short title>
- Plan gap:
- What fails:
- Evidence:
  - Source:
  - Plan:
  - Repository:
  - Outside source (only when needed):
- Smallest plan change:
- How to prove the fix:
- Confidence:

## Needs more checking
<Omit when empty.>

### <short title>
- Possible failure:
- Evidence so far:
- What is missing:
- Next step:

## Questions
<Omit when empty. Include only questions whose answers may change the result.>

## Optional suggestions
<Omit when empty.>

## Reviewed
- Repository areas: <short grouped areas, not a file inventory>
```

Omit evidence labels that do not apply. Do not leave empty placeholders.

If Ben questions a finding in a follow-up message, recheck it against the evidence before you answer.

## Final Check

Before you publish, confirm:

- The checks in `Launch and Chat Routing Protocol` passed, and `Review target` matches the target plan, its planner assignment, and the round.
- The review file is at the work-item reviews path with the round filename. No earlier round's file changed.
- Each finding is a proven plan defect that passed `Required Disprove Pass` and `Check Related Cases`. Unproven items are under `Needs more checking`.
- The result follows the `Pass` rules.
- You edited no file except the current review file.

Then append the result pointer defined in `Result Pointer`.
