# Implementation Reviewer Publication

Read this guide only after both review lenses, concern classification, and the completeness and disprove passes are done.

## Result Pointer

Append only after the review packet passes `Final Check`:

```md
Review ready: `{{path:workitems_root}}/<workitem-id>/reviews/<slug>-implementation-review-r<N>.md`
Status: `pass` / `challenge_required` / `needs_changes` / `blocked`
Summary: <one sentence result and correction or next owner when not pass>
```

## Output Format

Write one immutable review file under `{{path:workitems_root}}/<workitem-id>/reviews/`, named `<slug>-implementation-review-r<N>.md`, where `<slug>` is the lowercased Task ID, followed by `-<nickname>` when your launch input has a `Nickname:` line, and `<N>` is the review round.

```md
## Review target
- Workitem ID:
- Task: <Task ID> — <Task Name>
- Review round:
- Target implementation packet:
- Submitted commit:
- Plan or focused repair assignment:
- Source spec:
- Prior implementation and triggering result, when applicable:

## Summary
- Result: pass | challenge_required | needs_changes | blocked
- <One to three sentences.>

## Findings
<Write `None.` when no defect was proven. Otherwise repeat the block below.>

### <Severity> — <short title>
- Lens: implementation correctness | test and evidence credibility
- File and line:
- What fails:
- Evidence:
- Smallest correction:
- Affected checks to rerun:
- Confidence:

## Needs more checking
<Use when the result is `blocked`, or for a blocker recorded alongside `needs_changes`. Otherwise convert non-blocking uncertainty to `Residual limits`. Omit when empty.>

### <short title>
- Possible failure:
- Evidence so far:
- What is missing:
- Next owner or check:

## Questions
<Omit when empty. Include only questions whose answers can change acceptance.>

## Optional suggestions
<Omit when empty. Do not add severity or required routing.>

## Adversarial runtime challenge
<Include only with `challenge_required`. Repeat for each named hypothesis.>
- Challenge ID:
- Source-backed claim:
- Failure hypothesis:
- Why review and engineer evidence cannot resolve it:
- Material consequence:
- Fixed expected-result source:
- Bounded probe objective:
- Allowed runtime, fixtures, and mutations:
- Prohibited targets and actions:
- Cleanup boundary:

## Reviewed
- Checks I ran:
- Seams checked: <one line per seam: kind; both sides (path:line); questions asked, in one short phrase; result>
- Accepted completed slices relied on: <omit when none; link each accepted review>
- Residual limits:
```

Anything not under `Checks I ran` counts as submitted Implementation Engineer evidence.

- Do not add praise, process narration, or padding.
- Do not invent findings to fill the template.
- Say clearly when proof is missing.

## Final Check

Before you publish, confirm:

- the workitem, task, review round, packet, branch, submitted commit, plan or assignment, and source identities match, and the result pointer matches the packet;
- the complete submitted diff got both lenses, and every seam it creates or touches is under `Seams checked` with both sides read (for an integrated seam review, every seam in scope got the seam pass);
- each finding proves a reachable failure or false-pass path, and survives the disprove pass;
- the result meets `Review Result`, and a `challenge_required` result meets `Adversarial Challenge Decision`; and
- you changed no tracked product file and no Git state.
