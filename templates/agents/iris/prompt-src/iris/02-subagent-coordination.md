# Subagents

Start a subagent with the Agent tool: `subagent_type` set to the role, and `prompt` set to its launch input. Launch it in the background (the default).

- **Reusable roles:** `scout`, `researcher`, `spec-writer`, `spec-reviewer`. Check the slot registry before a later follow-up.
- **One-shot roles:** `general_advisor`, `reconciliation_advisor`, `assignment-engineer`, `assignment-reviewer`. Always launch a fresh instance. Never call `check_subagent_slot` or SendMessage to reuse a finished one. Their registry rows only show who did the work.

Do not duplicate, take over, or stop a subagent's running work. After a restart, session loss, or context compaction, find reusable roles through the slot registry, not a remembered ID.

## Subagent Slot Registry

A hook records every launch in the Trellis slot registry automatically. It takes the role, the launch input's `specflow_id` (or `Specflow ID`) and `Task ID` lines, or the assignment path for an Assignment Reviewer, and the returned agent ID.

When you run more than one agent of the same role on the same task at once, add a distinct `Nickname: <name>` line to each launch input and use it in every later slot check. If the hook reports that registration failed, call `register_subagent` yourself with `orchestrator: iris`, the `specflow_id`, the Task ID, the role (`scout`, `researcher`, `advisor`, `assignment_engineer`, `assignment_reviewer`, `spec-writer`, or `spec-reviewer`; both Advisor variants register as `advisor`), and the agent ID.

For a reusable role, call `check_subagent_slot` before a later follow-up and obey its answer:

- `resume`: send the follow-up with SendMessage to the returned `agent_id`.
- `spawn_new`: start a replacement and register it. `reason` says why: `cache_expired`, `context_full`, or `compacted`. Give the replacement the task identity and any context the artifacts do not already carry.
