# Investigation Publication

## Result Pointer

Use this format:

```md
Investigation packet: `<actual investigation packet path>`
Status: `root_cause_found` / `likely_cause_found` / `needs_more_evidence` / `blocked`
Summary: <one sentence>
```

## Output Format

Write one investigation packet for the current round under `{{path:workitems_root}}/<workitem-id>/investigations/`, named `<task-id>-<target>-investigation-r<N>.md`:

- `<target>` is the file name, without `.md`, of the result packet or assignment you investigate.
- When your launch input has a `Nickname:` line, put it after the Task ID: `<task-id>-<nickname>-<target>-investigation-r<N>.md`. Agents running in parallel on one task must never share a file.
- A follow-up keeps the name of the packet it continues and raises the round.

Each round writes a new packet with Write or Edit; never change an earlier one. If the round-1 file for this target exists, stop and name it and its `Status` in your final reply.

```md
Investigation packet:

Workitem ID: <workitem-id>
Task ID: <task-id>
Task Name: <task-name>
Round: <N>

Issue to investigate:
<Problem or question, scope, non-goals, and decision this investigation must support.>

Source refs:
- Result packet or investigator assignment:
- Source/spec:
- Relevant plan/implementation/review/final-validation/investigation packets:

Current context:
- Repository/working-tree state:
- Runtime/environment identity:
- Evidence time window:

Evidence inspected:
- `<file, command, log, artifact, or observation>`: <fact established>

Hypotheses considered:
| Hypothesis | Evidence for | Evidence against / missing | Result |
|---|---|---|---|
| <hypothesis> | <facts> | <facts or missing check> | leading / weakened / ruled_out / open |

Ruled-out paths:
- <path>: <evidence that excludes it>

Likely / confirmed root cause:
<Label as `Confirmed`, `Likely`, or `Not established`, then state the cause and causal chain.>

Missing evidence:
- <exact evidence or distinguishing check>
- None identified

Recommended next action:
<One primary route and the smallest action.>

Adversarial challenge resolution:
<Omit unless the investigation concerns an `inconclusive` adversarial validation packet (see `Adversarial challenge invalidation`).>
- Challenge review:
- Validation packet:
- Reviewed commit:
- Challenge IDs:
- Challenge disposition: invalidated | retry_same_contract | tracked_correction | unresolved
- Decisive evidence:

Suggested validation:
- <Check that would verify the diagnosis or resulting fix.>

Risks / uncertainty:
- ...

Status:
`root_cause_found` / `likely_cause_found` / `needs_more_evidence` / `blocked`
```

`Challenge disposition` values:

- `invalidated`: only with `root_cause_found`, under the `Adversarial challenge invalidation` route.
- `retry_same_contract`: names a no-edit probe or runtime correction inside the existing challenge authority.
- `tracked_correction`: names the tracked owner.
- `unresolved`: keeps the challenge open and states its next fact or blocker.

Leave out optional source or missing-evidence entries that do not apply. Do not leave placeholders that contradict each other, such as both missing evidence and `None identified`.

If a required section has nothing important to say, write `None identified`.

Keep the packet short and evidence-first. Do not paste long logs, narrate every search, or add speculative future work.

## Final Check

### Routing and Artifacts

- The current-round packet exists under the workitem's investigations directory and has the round-specific filename.
- The target and route pass every check in `Launch and Chat Routing Protocol`.
- You read the required named evidence, or recorded it as missing and made no claim that needs it.
- The shared-chat append has only the actual packet path, the status, and a one-sentence summary.

### Evidence and Claims

- Each evidence entry says what it established.
- The evidence matches the code, runtime, identity, data set, and time window being diagnosed.
- Each ruled-out path has evidence that excludes it. Not having seen something is not shown as disproof.
- The claim label and status meet `Claim Standards` and `Status Model`.

### Scope and Safety

- The investigation stayed inside the stated problem or question, scope, and non-goals.
- The recommended next action is one concrete primary route, not a broad backlog or an implementation plan.
- You changed no repository, Git, runtime, or external state (see `Execution Boundaries`).
- Any diagnostic that would change state is recommended with its command, evidence goal, and required owner, not run.
- Status is exactly `root_cause_found`, `likely_cause_found`, `needs_more_evidence`, or `blocked`.

### Publish

When every applicable check passes, append the result pointer defined in `Result Pointer`.
