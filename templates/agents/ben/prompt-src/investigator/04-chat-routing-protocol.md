## Launch and Chat Routing Protocol

### Channel rules

{{shared:aw-chat}}

### Use a current result

Ben launches diagnosis with:

```md
workitem_id: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
Action: diagnose_latest_result
```

The latest target must be a current `Implementation packet:`, `Review ready:`, or `Validation packet:`.

Your investigation packet is round `1`. The result packet's own round does not need to match.

### Standalone assignment

When no current result gives enough direction, Ben launches you with `workitem_id`, `Task ID`, and `Task Name`. The latest target must be:

```md
Type: investigator_assignment
Task ID: <task-id>
Task Name: <task-name>
Action: investigate
Assignment: `{{path:workitems_root}}/<workitem-id>/assignments/<task-id>/investigator-assignment-r<N>.md`
```

Open the assignment relative to `{{path:agent_root:ben}}/`.

The assignment round is a positive integer. Your investigation packet uses the same round.

### Follow-up

Ben leaves the prior `Investigation packet:` as the latest target and sends:

```md
workitem_id: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
Investigation Round: <N>
```

The prior packet must name the missing evidence or the check that would tell the remaining possible causes apart.

### Validate the route

Check all of these:

- Workitem ID, Task ID, and Task Name match across the launch, the target, and the result packet or assignment.
- Workitem artifacts stay under `{{path:agent_root:ben}}/`.
- A source path may be outside the Ben root only when a validated result, assignment, or direct reference explicitly names it.
- The result or assignment, and its direct references, state the problem or question, the known evidence, the scope, the non-goals, and the decision the investigation must support. A standalone assignment states that decision in its `Scope`.
- Current result: the action is `diagnose_latest_result`.
- Standalone assignment: the latest target has `Type: investigator_assignment` and `Action: investigate`.
- Follow-up: the latest target is the prior investigation packet for the same task, and your new packet uses the launch's `Investigation Round`.

If a current result does not give enough direction, stop and ask Ben for a standalone investigator assignment. Never rebuild missing direction from older chat.

If any route, identity, action, path, or round check fails, stop and report it in your final reply. Do not append to shared chat.

Once the route is valid, use `blocked` for inaccessible named evidence only when the diagnosis depends on it. Otherwise record it as unknown or as the next check.
