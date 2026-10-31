# Multi-Slice Continuation

In attended runs, do not start the next slice on your own after Ben's handoff. Wait for the owner to start it. Ben's handoff means the slice is ready for the owner's UI check and review, not accepted; the owner decides when the next slice begins.

A completed Ben handoff is the authority that the slice is done. For lane work, a slice counts as implemented only once the integrator has integrated it (`{{path:guidance:iris}}/iris/lanes.md`). Do not verify Ben's work, rerun accepted checks, restamp evidence, or require another review or validation packet. Do not launch a second general verification pass or broad reverification.

Read the current reviewed master (if any), the completed single, and Ben's completion summary only to learn what is now implemented and what roadmap work remains. Route any unresolved blocker or incomplete slice Ben reports to its named owner; otherwise the slice is closed.

## Continuation Contract

Ben's implementation summary and claim map are the continuation contract. Check that every blocking acceptance criterion, preservation rule, and deferred obligation appears once. The row's `Commit` names the durable accepted commit supporting its claim. Evidence from another source commit needs the checked reuse explanation or authorized squash comparison in `Notes`. Without that explanation, it is stale. Use Ben's recorded comparison; do not rerun accepted checks.

Continue when the contract is complete and no open row blocks the next stage.

If the contract is incomplete, route only the exact missing row:

- missing implementation or permanent tests: back to Ben;
- missing or stale evidence: to its named owner;
- a factual contradiction: bounded investigation; and
- a product or authority decision: to its owner.

## Next-Slice Route

When the accepted master has roadmap work left:

1. If the master needs a factual or status refresh for the completed slice, baseline, or artifact pointers, route a fresh Assignment Engineer to create a `master-refresh` Spec Writer assignment for the canonical master, then launch the Spec Writer as the `master-refresh` shortcut in your prompt allows.
2. If Ben's implementation changes an important future master contract (the shortcut's limits), send that change through the normal product and spec path, with normal assignment and spec review. Do not reopen the completed slice.
3. If a factual gap prevents choosing the next capability, use the smallest Scout or Researcher route that closes it, not one that reconfirms Ben's work.
4. Find the next actor-visible capability boundary from the refreshed master and baseline. Route a fresh Assignment Engineer to create the next `single` assignment, then follow the normal Writer, review, revision, readiness, and handoff flow.

When no roadmap slice remains, report the roadmap or run as complete. Do not add a final implementation-verification phase.
