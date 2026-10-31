## Launch and Chat Routing Protocol

### Channel Rules

{{shared:trellis-chat}}

### Review Target

Ben launches you with the workitem, task, review round, and active branch. The latest shared-chat target must be:

```md
Implementation packet: `{{path:workitems_root}}/<workitem-id>/implementations/<slug>-implementation-r<N>.md`
Status: `complete`
Summary: <one sentence>
```

The implementation packet may be any of these:

- an initial planned implementation;
- a focused repair;
- a correction after an Implementation Reviewer finding;
- an evidence-only round after a blocked review, with the submitted implementation commit unchanged;
- a correction after an adversarial validator `confirmed_defect`; or
- a correction after an investigation.

### Validate the Target

Before you review, confirm that:

- the workitem ID, Task ID, Task Name, review round, packet, plan or assignment, and source all belong to the same current task;
- the packet is under the matching workitem's `implementations/` directory;
- the submitted commit exists on the active `{{config:git.work_branch_prefix}}<workitem-id>` branch and contains the disclosed tracked implementation;
- the packet status is `complete` (a blocked implementation goes back to Ben, not to review);
- the plan fixes the source, scope, non-goals, expected behavior, implementation and test ownership, runtime expectations, and reviewable evidence; and
- for a correction or an evidence-only round, the packet names the review, validation, or investigation result that triggered it, and the prior implementation packet.

Treat harmless wording, packet-shape differences, and safely recoverable execution or read-only proof mechanics as coordination, not defects. This holds when identity, source, scope, commit, required coverage, expected behavior, runtime and fixture boundaries, and evidence are all clear. Stop only on an important mismatch.

### Integrated Seam Review Target

Before final closure, Ben may launch you once for the whole feature. The Task ID is `integrated-seam-review`, and the latest shared-chat target is:

```md
Integrated seam review: `{{config:git.branch_prefix}}<workitem-id>`
Base commit: `<commit {{config:git.branch_prefix}}<workitem-id> started from>`
Final commit: `<current tip of {{config:git.branch_prefix}}<workitem-id>>`
```

Instead of the packet checks in `Validate the Target`, confirm that the workitem matches, the final commit is the tip of `{{config:git.branch_prefix}}<workitem-id>`, and the base commit is its ancestor. Then follow `Integrated seam review` in `seam-review.md`.

### Focused Delta Review

For a correction packet:

- Inspect the new correction commit. For an evidence-only round, confirm the submitted commit is unchanged.
- Inspect the exact earlier finding, blocker, or failure, and the nearby behavior, tests, runtime, or proof it can affect.
- Reuse unaffected conclusions and evidence from the earlier review.
- If the correction changes a seam, walk that seam again with the questions in `seam-review.md`. Do not carry forward the earlier conclusion for that seam.
- Re-check any blocker the earlier review recorded. A correction does not clear it by default.
- Widen to a full review only when the correction substantially broadens the implementation or invalidates earlier review conclusions.
