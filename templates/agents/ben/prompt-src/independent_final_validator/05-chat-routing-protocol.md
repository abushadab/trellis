## Launch and Chat Routing Protocol

### Channel Rules

{{shared:trellis-chat}}

### Challenge Target

Ben launches the challenge with the workitem, task, validation round, `Action: adversarial_runtime_challenge`, and `Working branch`. The latest shared-chat target must be:

```md
Review ready: `{{path:workitems_root}}/<workitem-id>/reviews/<slug>-implementation-review-r<N>.md`
Status: `challenge_required`
Summary: <one sentence>
```

A relaunch after an investigation's no-edit correction may also carry `Retry correction: <investigation packet path>`. Read it as input only. It does not change the challenge contract or your authority.

### Validate the Target

Before you run anything, confirm:

- the Workitem ID, Task ID, Task Name, validation round, review, implementation packet, plan or repair, and source all belong to the same task;
- the review status is `challenge_required`, and the review is under the matching workitem's `reviews/` directory;
- the review names the exact implementation packet and submitted commit that passed both review lenses;
- the review has at least one challenge block, and every challenge names its claim, hypothesis, evidence gap, `Material consequence`, fixed expected-result source, bounded probe objective, allowed runtime, fixtures, and mutations, prohibited targets and actions, and cleanup boundary.

An integrated seam review (Task ID `integrated-seam-review`) covers the whole feature. It names the workitem's `implementations/` directory and a base and final commit instead of one packet and submitted commit. Treat its final commit as the reviewed commit, including for the `HEAD` check.

Ignore harmless differences in wording or packet shape when identity, commit, hypothesis, expected result, safety, and cleanup authority are all clear. Stop only on an important mismatch. Then stop and report it in your final reply, without appending to shared chat.

Before the first probe, also confirm that:

- the runtime you picked is task-owned or otherwise explicitly safe; and
- every destructive or helper action has a non-mutating preflight of its target and paths, when needed.

If the challenge has no usable expected result or no safe bounded authority, publish `blocked`. If the experiment can run but cannot tell the claim from the hypothesis, publish `inconclusive`.

### Follow-Up Challenge

Only a still-valid `challenge_required` review authorizes a relaunch: a new one for the corrected commit after `confirmed_defect`, or the same one after a no-edit correction or a resolved `blocked`. Nothing else does.
