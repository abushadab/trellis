# Artifact and Handoff Contract

## Artifact Discipline

- Keep shared chat to routing pointers, status, and a one-line summary.
- Keep task detail in the authoritative source, plan, assignment, or result artifact.
- Do not copy an existing artifact into another assignment or launch prompt.
- Route from the latest reported target and its direct references. Never search older chat to rebuild authority.
- Keep workitem artifacts under `{{path:workitems_root}}/<workitem-id>/`.

## Assignment Rules

If an accepted artifact already gives the role its authority, use it directly. Create an assignment only where the table says it is required.

| Route | Authority and latest target | Assignment |
| --- | --- | --- |
| Initial planner | `Type: planner_assignment` | Required |
| Plan reviewer | `Plan ready:` or `Plan revised:` and the plan's direct references | None |
| Planned Implementation Engineer | Ready `Plan ready:` when review is not required, or passing plan `Review ready:` | None |
| Focused-repair Implementation Engineer outside a ready plan | `Type: implementation_engineer_assignment` naming source, triggering result, allowed changes, affected reruns, and review ownership | Required |
| Implementation Reviewer | Complete `Implementation packet:` | None |
| Independent Final Validator | Implementation `Review ready:` with `Status: challenge_required` and the complete adversarial challenge contract | None |
| Artifact-driven investigator | Current `Implementation packet:`, `Review ready:`, or `Validation packet:` defining the diagnostic question | None |
| Standalone investigator | `Type: investigator_assignment` | Required |

Create each required assignment with its tool: `create_ben_planner_assignment`, `create_ben_implementation_engineer_assignment`, or `create_ben_investigator_assignment`. Never write an assignment file by hand. A standalone investigator assignment states, in its `Scope`, the decision the investigation must support.

A direct route is valid only when the target and its direct references establish:

- the source, scope, and non-goals;
- who owns the role; and
- the implementation, review, validation, or diagnosis that is required.

If that authority is incomplete, create the right focused assignment, return to planning, or end your turn with `Status: needs_decision` (see `Turn Status`). Never guess what is missing.

### Initial planner assignment check

Pass `plan_output_path` (a Markdown path with a lowercase file name, such as `{{path:workitems_root}}/<workitem-id>/plans/<task-id>-plan.md` with the task ID lowercased) to `create_ben_planner_assignment`, and confirm the returned assignment names it as its `Plan Output Path`. Fixing an initial assignment is still initial planning: send the task identity, not `Revision Round`.

## Initial Launch Inputs

The task identity is these three lines:

```md
workitem_id: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
```

Launches backed by an assignment (planner, Implementation Engineer, investigator) send the task identity. Implementation Engineer launches backed by an assignment also include:

```md
Working branch: {{config:git.work_branch_prefix}}<workitem-id>
```

Direct launches use:

| Route | Launch input |
| --- | --- |
| Plan reviewer | Task identity of the plan's planning task; optional compact review focus |
| Planned Implementation Engineer | Task identity; `Action: implement_and_validate_approved_plan`; Working branch |
| Implementation Reviewer | Task identity; `Review Round: <N>`; Working branch |
| Independent Final Validator | Task identity; `Validation Round: <N>`; `Action: adversarial_runtime_challenge`; Working branch |
| Artifact-driven investigator | Task identity; `Action: diagnose_latest_result` |

A review or validation focus never widens authority beyond the target artifact. Naming the working branch does not widen the task's authority either.

## Revisions and Follow-Ups

When the latest result defines a small, clearly scoped continuation under existing authority, use it directly. Valid latest results:

- Planner: plan `Review ready:` with `Status: needs_changes`.
- Investigator: `Investigation packet:` naming remaining evidence.
- Implementation Engineer: any result in the list below.
- Implementation Reviewer and Independent Final Validator: the same targets as in `Assignment Rules`.

Valid latest results for an Implementation Engineer follow-up:

- Implementation `Review ready:` with `Status: needs_changes`;
- Implementation Reviewer `Review ready:` with `Status: blocked`, naming important engineer-owned execution evidence unavailable to the read-only reviewer;
- `Validation packet:` with `Status: confirmed_defect`;
- `Investigation packet:` with `root_cause_found` naming a correction boundary; or
- blocked `Implementation packet:` whose blocker is resolved.

Leave that result as the latest chat target, unless the receiving role needs a specific pointer shape. These cases need a repeat pointer:

- After you resolve an Implementation Reviewer blocker with no tracked change, post the same complete implementation-packet pointer again before review resumes.
- Before any validator relaunch from the same review (after a resolved `blocked`, or an investigation with `Challenge disposition: retry_same_contract`), post the same still-valid `challenge_required` review pointer again with `append_ben_chat`.

If the investigator reports that a packet for the same target already exists, do not relaunch the same diagnosis:

- `needs_more_evidence`: post that packet's pointer again and send a follow-up round.
- Any other status: post that packet's pointer again and route from its result.

Then follow `Follow up` under `Subagents` for the receiving role.

**Source-correction replan:** A new approved source decision or a spec revision is not a plan-review revision. If it needs a fresh plan for a task that already has a planner assignment, keep that task and its artifacts. Create a new Task ID named `<task-id>-replan-r<N>`, then call `create_ben_planner_assignment` as usual. The new assignment must cite the superseded plan or assignment and the source correction. Do not reuse the old Task ID.

**Plan review limit:** The planner accepts only revision rounds `2` and `3`. When the third plan review of the same plan returns `needs_changes`, do not route a fourth revision:

- If the blocker is a missing decision, end your turn with `Status: needs_decision` (see `Turn Status`).
- Otherwise create a fresh planner assignment under a new Task ID, as for a source-correction replan. It cites the plan and its reviews and asks the planner to re-slice the remaining work.

Revision and follow-up inputs start with the task identity. Add only:

| Role | Additional fields |
| --- | --- |
| Planner | `Revision Round: <N>` |
| Implementation Engineer | `Revision Round: <N>`; Working branch |
| Implementation Reviewer | `Review Round: <N>`; Working branch |
| Independent Final Validator | `Validation Round: <N>`; Working branch |
| Investigator | `Investigation Round: <N>` |

When you relaunch the validator after an investigation packet with `Challenge disposition: retry_same_contract`, also add `Retry correction: <investigation packet path>`.

Each plan, implementation, implementation-review, final-validation, and investigation stream starts at `r1`. Later rounds count up by one. A validator launch from a new `challenge_required` review of the same task continues that task's final-validation stream. A round count alone does not stop a correction. The only exception is the `Plan review limit` above. Escalate when the cause, expected behavior, authority, or a safe correction is still unresolved, or when the change needs replanning.
