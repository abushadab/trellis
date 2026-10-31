# Run Iris And Ben

| Tool | Use |
| --- | --- |
| `start_session(agent, prompt, label, priority=50)` | Start a headless session. `agent` is `iris` or `ben`. Returns `session_id`. Higher priority is more important. |
| `resume_session(session_id, message)` | Send the next message to an idle session. It refuses while the session runs. |
| `list_sessions()` | Every session: agent, label, priority, status, PID, last Turn Status. |
| `read_session_result(session_id)` | The latest final message, with the parsed `## Turn Status` and `## Decision needed`. |
| `set_session_priority(session_id, priority)` | Change a priority. |
| `pause_session(session_id)` | Pause one session by its exact PID. |

When your own session starts, call `list_sessions`. Tell the user about unfinished work before you start anything new.

## Resume Or Start Fresh

- Resume the same session for follow-ups on the same specflow or workitem: an answer, a correction, a retry.
- Start a fresh Iris for each new slice and a fresh Ben for each new workitem.
- Never put two launches into the same workitem at once. Ben's subagents read only the latest chat pointer of a workitem. Launch one, wait for its result, then launch the next.

## Wait Without Polling

After a start or resume, run this with Bash in the background (`run_in_background`):

```text
{{path:trellis_cmd}} wait --project "{{path:project_dir}}" --session <session_id>
```

It exits when that session finishes its turn, and the harness wakes you. Never wait with a sleep loop or repeated `list_sessions` calls. You may keep talking with the user meanwhile. When it wakes you, call `read_session_result`.

## Brief Rules

Iris and Ben cannot ask you anything while they run. The brief is all they know.

- Use full absolute paths, and check each exists before you send.
- Point to artifacts. Do not copy their contents into the brief.
- State the goal, where the run ends, the non-goals, and every decision already made, with who made it.
- End every brief with:

```text
Rules for this run:
- Never use AskUserQuestion. Put every question in your final message, in a `## Decision needed` block.
- Push nothing. Do not pull, fetch, open pull requests, or change remotes.
- End with the `## Turn Status` block.
```

Brief to Iris:

```text
Goal: <what the user wants, in two or three sentences>
Capability: <what changes>
Actor-visible outcome: <what an actor can see or do>
Non-goals: <list>
Constraints: <list>
Intent brief: <absolute path, or "none">
Run ends when: <completion boundary>
Decisions already made: <each with who decided it, or "none">
```

For a next slice after Ben, also give the absolute paths of Ben's implementation summary and the master spec.

Brief to Ben from Iris:

```text
workitem_id: <lowercase slug of the task ID>
Task ID: <task-id from Iris's handoff>
Task Name: <task-name from Iris's handoff>
Spec: <absolute path to the single spec>
Call read_handoffs for the active single spec. Execute only that spec.
When it is done, call handoff_ben_to_iris and end with Status: handed_off.
Run ends when: <completion boundary>
Decisions already made: <each with who decided it, or "none">
```

Brief to Ben without a spec. It must stand alone, because Ben cannot see this conversation:

```text
workitem_id: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
This is a direct work item. There is no Iris spec and no handoff. Do not call handoff_ben_to_iris. End with Status: done.
What to change: <exact change, with absolute file paths>
Expected result: <how anyone can see it is right>
Do not change: <non-goals>
Run ends when: <completion boundary>
```

## Stop Or Pause

Use `pause_session`, or `kill <pid>` with the exact PID from `list_sessions`. Never use `pkill -f`, `killall`, or any name pattern. Check the PID still belongs to that session first. Tell the user what you paused or stopped, and why.
