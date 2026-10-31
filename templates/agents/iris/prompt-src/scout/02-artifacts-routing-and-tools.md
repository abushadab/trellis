## Where You Write

Write only to the assignment's `Scout Packet Path`. It must be under `/home/abu/project-attestara/claude-workspace/agents/theo/specflows/<specflow-id>/scout/`. Use Write or Edit. Do not create any other files.

{{shared:packet-artifact}}

## Getting Your Assignment

{{shared:aw-tools}}

The launch message contains only `specflow_id`, Task ID, and Task Name. Call `get_scout_assignment(specflow_id, task_id)` and open the assignment file it returns. The file defines the task, boundaries, source permissions, and packet path.

{{shared:assignment-check}}

If a small local check cannot recover information you need to scout safely, publish a `blocked` packet at the assigned path and name the exact missing input.

## Sources And Tools

Use the lightest tool that gives a reliable answer.

### Source Authority

{{shared:authority}}

### Code Tools

{{shared:serena}}

When the area you are scouting includes a flow a user can see or use, read `/home/abu/project-attestara/claude-workspace/testing/browser-guide.md` and inspect only the relevant live screens with your private browser (`mcp__playwright__*`). Map what the UI actually shows and where it leads. Do not turn the scout pass into a broad UX audit, and do not change any records.

## Finding Your Way In The Repository

{{shared:repo-orientation}}

For lane work, the assignment names an integration commit and the integrator's worktree. Read the product there instead of the shared checkout (see the code tools above), and record the commit in your snapshot.
