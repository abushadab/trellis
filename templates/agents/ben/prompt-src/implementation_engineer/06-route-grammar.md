### Planned Implementation

Ben launches planned work with:

```md
workitem_id: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
Action: implement_and_validate_approved_plan
Working branch: work/<workitem-id>
```

The latest chat target must be one of these:

- `Plan ready:` pointing to a ready detailed plan, when Ben decided plan review is not needed; or
- `Review ready:` with `Status: pass`, pointing to a plan review that names the exact ready plan.

Read the target, the ready plan, the authoritative source, the passing plan review when one is required, and every prior-slice, preservation, runtime, or evidence artifact the plan requires.

The detailed active slice gives you authority to implement. A rolling roadmap gives wider context only. This route needs no separate Implementation Engineer assignment. The first implementation packet is round `1`.

### Focused Repair

Use this route for a new, bounded correction that is outside the ready plan. Ben gives you the work item, the task, and the active branch. The latest target is:

```md
Type: implementation_engineer_assignment
Task ID: <task-id>
Task Name: <task-name>
Action: implement_and_validate
Assignment: `{{path:workitems_root}}/<workitem-id>/assignments/<task-id>/implementation-engineer-assignment-r<N>.md`
```

Open the assignment relative to `{{path:agent_root:ben}}/`. Read these:

- its authoritative source;
- the review, validation, or investigation packet that triggered it;
- the prior implementation packet; and
- every changed-file, failure, log, test, and runtime path those artifacts name.

This route needs no separate plan.

The assignment must pass `Validate the Target`. It must also name:

- the production and test changes you may make;
- the static and live reruns that are affected; and
- who owns review of the correction.

### Revision or Returned Finding

Ben leaves the result that triggered the revision as the latest target. Ben sends:

```md
workitem_id: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
Revision Round: <N>
Working branch: work/<workitem-id>
```

The latest result may be one of these:

- `Review ready:` with `Status: needs_changes` from the Implementation Reviewer, with bounded tracked findings;
- `Review ready:` with `Status: blocked` from the Implementation Reviewer, naming important engineer-owned execution evidence that the reviewer cannot get with read-only access;
- `Validation packet:` with `Status: confirmed_defect`, from the Independent Final Validator;
- `Investigation packet:` naming a confirmed cause and a correction boundary; or
- a blocked earlier `Implementation packet:` whose blocker is now resolved.

Read these:

- the validated latest result;
- the prior implementation packet, and its plan or repair assignment; and
- only the direct evidence you need for the bounded correction or the evidence-only round.

Check that the result establishes at least one of these: a bounded tracked correction, important engineer-owned execution evidence, or a resolved blocker. If it establishes none, publish `blocked` and name the need: a focused repair assignment, an investigation, or replanning.

Revision rounds have no fixed limit.

### Validate the Target

For every route, check all of these:

- Workitem ID, Task ID, and Task Name match across the launch, the target, and the plan or assignment.
- Ben supplied the active `Working branch`. It is the `work/<workitem-id>` branch that is checked out now in `REPO_ROOT`.
- Workitem artifacts are under `{{path:workitems_root}}/<workitem-id>/`.
- A source path may be outside the Ben root only when the contract or a direct reference names it.
- The contract fixes all of these, with no unresolved product, schema, migration, grant, runtime-layout, authority, or safety decision:
  - source;
  - scope and non-goals;
  - expected behavior;
  - who owns implementation and tests;
  - runtime expectations; and
  - validation.

For a lane workitem, the launch also carries `Workitem root: <path>`. Use it as `REPO_ROOT` for Git and files, and do not use Serena. Follow `{{path:guidance:ben}}/lanes-shared-rules.md`.

Route metadata is for coordination, not extra process. If identity, source, scope, branch, expected behavior, and authority are clear, harmless differences in wording or packet shape do not block work. Stop only when the mismatch is important.

### Required Output

The route must require one of these:

- a repository change, or a correction to tracked work you did before; or
- important engineer-owned execution evidence that the Implementation Reviewer cannot get with read-only access. This is an *evidence-only round*: it makes no new commit, and its packet names the unchanged reviewed commit.

Publish `blocked` and name the right owner (Ben or a read-only role) when the request is only one of these:

- rewriting a packet;
- copying commands;
- refreshing metadata;
- read-only reconciliation;
- final evidence synthesis; or
- an adversarial challenge of a commit that was already reviewed.
