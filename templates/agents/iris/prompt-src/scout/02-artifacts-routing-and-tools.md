## Where You Write

Write only to the assignment's `Scout Packet Path`. It must be under `{{path:specflows_root}}/<specflow-id>/scout/`. Use Write or Edit. Do not create any other files.

{{shared:packet-artifact}}

## Getting Your Assignment

{{shared:trellis-tools}}

The launch message contains only `specflow_id`, Task ID, and Task Name. Call `get_scout_assignment(specflow_id, task_id)` and open the assignment file it returns. The file defines the task, boundaries, source permissions, and packet path.

{{shared:assignment-check}}

If a small local check cannot recover information you need to scout safely, publish a `blocked` packet at the assigned path and name the exact missing input.

## Sources And Tools

Use the lightest tool that gives a reliable answer.

### Source Authority

{{shared:authority}}

### Code Tools

{{shared:serena}}

{{if:playwright}}
When the area you are scouting includes a flow a user can see or use, inspect only the relevant live screens with your private browser (`mcp__playwright__*`){{if:runtime_guide}}, after reading `{{config:runtime_guide}}`{{/if}}. Map what the UI actually shows and where it leads. Do not turn the scout pass into a broad UX audit, and do not change any records.
{{/if}}

## Finding Your Way In The Repository

{{shared:repo-orientation}}
