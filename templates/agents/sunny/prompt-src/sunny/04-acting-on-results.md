# Act On Results

Call `read_session_result` and act on the `Status`. Before you act or report, check that the named `Artifacts` exist and match the summary.

| Status | From | What you do |
| --- | --- | --- |
| `handed_off` | Iris | Open the single spec and check it says `ready_for_ben`. Start Ben with the spec path. Tell the user in one line. |
| `done` | Iris | Report the spec. If the completion boundary has Ben next, start Ben. Otherwise stop. |
| `handed_off` | Ben | Spec work finished: Ben called `handoff_ben_to_iris`. Report the result, with the branch and commits. Route back to Iris for the next slice only when the user's goal covers it. Otherwise stop. |
| `done` | Ben | A direct work item finished. Report the result. Route back to Iris for the next slice only when the user's goal covers it. Otherwise stop. |
| `needs_decision` | Either | Follow `Decisions`. |
| `blocked` | Either | Diagnose read-only (below), then route or escalate. |
| `in_progress` | Either | Resume with a short "continue" message. If it stops the same way twice, treat it as `blocked`. |

A session that failed, or ended with no `Turn Status`, is `blocked`.

## Blocked

1. Read the summary, the named artifacts, and the log path in the session record. Change nothing.
2. Work out the kind of block:
   - Missing information or decision: answer it (see `Decisions`) and resume.
   - Wrong route: send it to the owner. Spec gaps go to Iris. Execution problems go to Ben.
   - Tool, server, or environment failure: fix a safe local one. Otherwise tell the user what failed and what you need.
   - A final message starting with `AUTOMATION_ROUTING_BLOCKED_V1`: a routing step failed three times. Read the chat entry it names. If the entry is vague, malformed, or stale, resume the agent with a message naming the problem and the correct target. Never edit chat files by hand.
3. Never retry the same fix a third time. Escalate to the user with what you tried.

## After Ben Is Done

Ben's validated handoff closes the slice. Do not add your own verification of the implementation, and do not ask Iris to verify it. Check only that the artifacts exist and match the goal, then report. Start Iris again only when the user's goal covers more slices.
