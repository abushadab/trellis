# Multi-Slice Continuation

A run covers the goal Sunny gave you. Finish that goal, and do not start the next slice unless the goal says to. When the goal covers only the slice Ben just finished, end your turn with `Status: done` and let Sunny decide when the next slice begins. Ben's result means the slice is ready for the user's check and review, not accepted.

Ben's result reaches you through `handoff_ben_to_iris`. Sunny's prompt tells you when it has arrived. Read it with `read_handoffs`.

A completed Ben handoff is the authority that the slice is done. Do not verify Ben's work, rerun accepted checks, restamp evidence, or require another review or validation packet. Do not launch a second general verification pass or broad reverification.

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
