## Launch and Chat Routing Protocol

### Shared chat

{{shared:trellis-chat}}

### Launch

The launch contains `workitem_id`, the planning task's `Task ID` and `Task Name`, and may say what to focus on. Review authority comes from the target plan and its linked files, not from the launch text.

### Review target

The latest message must point to:

- `Plan ready:` with a readable plan and `Status: ready` or `Status: blocked`; or
- `Plan revised:` with a readable plan, `Status: ready` or `Status: blocked`, and a revision round.

Before reviewing, confirm that:

- the plan is under `{{path:workitems_root}}/<workitem-id>/plans/`;
- other work-item files are under `{{path:workitems_root}}/<workitem-id>/`;
- the source spec is readable (it may be outside the work-item folder, at the path the plan and assignment name);
- the launch `workitem_id`, plan path, and plan `Workitem ID` match;
- the planner assignment is readable, and its `Workitem ID`, `Task ID`, and `Task Name` match the plan's `Workitem ID`, `Planning Task ID`, and `Planning Task Name`;
- the plan mode is `rolling` or `simple`; and
- the target status matches the plan status.

If any check fails, stop without writing to shared chat.
