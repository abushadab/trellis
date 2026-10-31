# Rolling Plan Review

This guide is the authoritative procedure for reviewing the roadmap, the active slice, and continuity.

## Scope and Identity

- Review roadmap coverage, dependencies, ordering, preservation constraints, cross-slice obligations, and any declared delta.
- In a ready plan, confirm the active-slice ID and name match exactly one execution-roadmap row.
- Confirm completed-slice IDs are unique, and execution-roadmap IDs are unique.
- In a ready plan, confirm the active-slice ID does not appear in `Completed slices`.
- Review implementation detail only for the active slice. Future slices must stay coarse.

## Continuity

- Every source AC and preservation constraint is covered by a roadmap row or by accepted completed evidence. Later focused slices may point to accepted coverage without restating it.
- Dependencies and order let each slice be implemented and verified on its own.
- A safe internal contract that can be verified on its own may come before full feature integration.
- Apply the `Slice size` check from your prompt to the active slice and roadmap. Require a concrete reason for each split.
- Reject unnecessary splits by file, agent, test owner, or reversible local runtime action.
- Completed slices and open or deferred obligations carry forward from the preceding plan.
- A roadmap change is `none` or a short, evidence-backed delta.
- Cross-slice behavior has a coarse live-acceptance or preservation outcome with a named eventual owner.
