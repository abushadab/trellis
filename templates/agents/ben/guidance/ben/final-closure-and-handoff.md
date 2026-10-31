# Final Closure and Handoff

Read this guide after the required implementation slices are complete. It is the only detailed procedure for the integrated seam review, the implementation summary, the completion claim map, the Iris handoff, and optional lesson candidates.

## Integrated Seam Review

Run one integrated seam review after the last slice is finalized and before you write the summary. Each slice review saw only its own change, so defects where slices meet can pass every slice review.

Skip it when the workitem had only one implementation slice. That slice's review already covered the whole diff. Record the skip and its reason in the implementation summary.

1. Post this target to shared chat:

   ```md
   Integrated seam review: `{{config:git.branch_prefix}}<workitem-id>`
   Base commit: `<commit {{config:git.branch_prefix}}<workitem-id> started from>`
   Final commit: `<current tip of {{config:git.branch_prefix}}<workitem-id>>`
   ```

2. Spawn a fresh `implementation_reviewer`. Never resume a slice reviewer, and do not pass earlier review verdicts. Launch it with the task identity, using Task ID `integrated-seam-review` and Task Name `Integrated seam review`, plus `Review Round: <N>`.
3. A correction from this review gets the usual delta review of the seams it affects and is finalized under `Git Policy`. It does not need a second integrated review. A validator launched from this review gets `Working branch: {{config:git.branch_prefix}}<workitem-id>`.

## Minimal Completion Contract

Write one short implementation summary for the final accepted state. Leave out empty sections and repeated packet summaries. Publish it only at:

```text
{{path:workitems_root}}/<workitem-id>/summaries/implementation-summary.md
```

Name the commit once, in this form:

```md
**Final accepted implementation commit:** `<40-character commit SHA>`
```

The summary names the authoritative source, the delivered outcome, important non-goals or deviations, one compact completion claim map, and, only when they exist, unresolved gaps, approved deferrals, and the next owner.

Build it directly from the repository and the accepted evidence. Do not create a reconciliation, verification, or summary-only packet.

{{if:design_authority}}
For a slice that changes UI, the summary must also give the requester's independent UI check what it needs, because that check runs outside the workflow roles after this handoff:

- the product commit and branch;
- the design authority's pinned ref;
- the state ids covered;
- the `ui-conformance` evidence folder, with the side-by-side pairs; and
- the accounts used for the product captures (names only, never credentials).

Describe the slice as "ready for the requester's UI check and review". Never describe it as accepted.
{{/if}}

## Completion Claim Map

Add one row for every blocking acceptance criterion, preservation rule, and deferred obligation. {{if:design_authority}}A slice that changes UI gets one UI row per design screen (its states may share the row): `UI matches design <screen> at <states>, design@<pinned ref>`. Its evidence is the side-by-side evidence directory and the accepted implementation review. {{/if}} Combine requirements only when they are closely related and share the same verdict and evidence.

```md
| Requirement | Verdict | Evidence | Evidence type | Commit | Notes |
|---|---|---|---|---|---|
| <AC, preservation rule, or deferred obligation> | <verdict> | <decisive paths, test IDs, or accepted packet> | <type> | <exact commit> | <only a qualification, owner, or route that matters> |
```

`Commit` names the durable accepted commit for which the row makes its claim. This may be the slice's squash commit or a later accepted commit. When evidence was produced on another source commit, `Notes` records that source and the checked reason the evidence still applies. Do not use a temporary engineer commit as the row's durable target after its branch is removed.

Evidence types: `repository` (static evidence in the accepted commit), `review` (accepted Implementation Reviewer evidence), `test` (a focused automated check with its actual tested source recorded), {{if:design_authority}}{{else}}and {{/if}}`runtime` (accepted execution evidence with its source and relevant runtime inputs recorded){{if:design_authority}}, and `ui-conformance` (side-by-side design and product screenshots for every listed state, taken from that commit's runtime, with the design image being the committed reference image at the pinned ref (recaptured from a task-owned copy only when that ref lacks it), same viewer, state, and size (full page), saved side by side in the workitem's `ui-conformance` evidence folder, and accepted by the Implementation Reviewer){{else}}.{{/if}} A row may cite several types.

Use short, true verdicts such as `met`, `preserved`, `deferred`, `missing`, `stale`, `failed`, `unclear`, or `unsupported`. A `deferred` row names the source-approved reason, the owner, and the stage. Never present an open verdict as passing evidence.

Pick the lightest evidence that establishes each claim. Static claims may close with direct `repository` evidence. Claims that depend on services, environment, timing, integration, migrations, deployment state, or observable runtime behavior require focused `test` or `runtime` evidence. Do not require Independent Final Validator evidence for a claim established directly by repository, review, focused test, or trustworthy engineer runtime evidence. Cite a review only on the rows it supports. Do not rerun accepted evidence just to write the summary.

## Freshness

Keep the original test and runtime attribution; do not present reuse as a new execution. Follow `Review and Validation Rules` for affected reruns.

Evidence naming another commit is usable only when `Notes` records checked reuse under `Review and Validation Rules` or the authorized squash comparison below. Without that explanation, it is stale for the row's claim.

### Authorized Squash Rebinding

Evidence accepted for an Implementation Engineer commit may be rebound only to the final squash commit created by `Git Policy` when Ben proves exact tree equality between those commits. Repository and review evidence then transfer. Test or runtime evidence transfers only when Ben also confirms that relevant configuration, images, migrations, services, fixtures, mutation boundaries, and external inputs did not change.

For the squash itself, the claim row names the durable final squash commit in `Commit`. Its `Notes` name the source Engineer commit and the equality check. This special identity transfer covers only the authorized squash.

## Iris Handoff Gate

Route an incomplete row to the owner of its gap, as under `Slice Gate`: missing work or engineer evidence to the Implementation Engineer, needed independent review to the Implementation Reviewer, a factual contradiction to a bounded investigation, and a decision to its authority owner. Do not launch broad reverification.

Call `handoff_ben_to_iris` only when:

- the claim map accounts for every blocking acceptance criterion, preservation rule, and deferred obligation;
- every blocking row is `met`, `preserved`, or source-approved `deferred` beyond the current stage, with fresh evidence that fits the claim;
- for more than one slice, the integrated seam review published `pass`, or every finding, challenge, and blocker it raised is closed as in `Slice Gate`; and
- the final branch satisfies `Git Policy`.

Open rows stay explicit and block only the stage they affect. Iris continues from the summary and checks it. Iris does not routinely reverify the implementation.

After the tool accepts the handoff, end your turn with `Status: handed_off` (see `Turn Status`). `handoff_ben_to_iris` is the only writer of completion. Do not add a completion-like message or a second summary. To replace an invalid handoff, record the replacement in the summary and call the tool once after closure. Keep and disclose unrelated user changes. The tool checks shape only; you own whether the evidence is true and complete.

## Lesson Candidates (Optional)

After the summary, you may propose 0–2 lessons from this workitem's confirmed review findings. This never delays the handoff. A lesson qualifies only when it rests on distinct confirmed failures, or one serious established failure (count each defect once); its mechanism is reusable; and it applies beyond this case. Publish at `{{path:workitems_root}}/<workitem-id>/lesson-candidates.md`. Mark product or spec authority `Needs Iris confirmation`. Never edit any guidance; the user decides.
