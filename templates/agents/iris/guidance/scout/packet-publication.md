# Scout Packet Publication

## Publishing Rules

Write one short Markdown file to the assignment's `Scout Packet Path`.

Keep it short: state each fact once, and leave out optional lines that add nothing to the decision. If much more explanation is needed, propose a Researcher task instead of growing the packet.

## Chat Pointer

Use author `Scout (<short-scope>)`. `<short-scope>` is a short stable slug from the assigned lens or task, such as `internal-architecture`, `security-data`, or `public-api-workflow`. Do not use a bare `Scout`; several scouts may run at once.

Post exactly:

```md
Scout packet: `<actual artifact path>`
Status: ready / blocked
Summary: <one-line summary>
```

## First Packet

Use this shape for a new scout task:

```md
# Scout Packet

## Summary

3–5 plain lines: what you looked at, what you found, and what should happen next.

## Routing Recommendation

- Next route:
- Decisive reason:

## What Was Checked

- Assignment: `<assignment path>` - task, lens, and round
- Snapshot: branch, full commit, and whether the working tree is clean or dirty where it matters; or why repository state does not matter
- Inspected: decisive source IDs only; keep path and symbol details in Sources
- Negative claims: query, folders, and result count for each; or `none important`
- Checks run: commands or tests, or `none - read-only inspection`
- Authority notes, if any: source conflicts, evidence that is only historical, or snapshot limits

## Scope

- Requested outcome:
- Affected now:
- Unchanged:
- Deferred to the later goal:

## Key Findings

- Usually three to five, never more than eight. State each once, with source IDs.

## Size Of The Work

- Classification: ordinary / broad
- What makes it broad, if it is:
- Relevant locations, entry points, and dependencies:
- Natural divisions:
- New architectural surfaces: `None visible`, or one line each: the surface, the evidence already visible that it is needed now (prompt step 4), and what is missing or what to do (`none`, a bounded gap, a deferral, or the exact `user-approved foundation exception` pointer). Write `Unknown` where the scan cannot answer.
- Sensitive boundaries (prompt step 3; omit when none): one line each: the boundary, its route-changing dimensions, and `verified` or `open` with the gap, earliest affected stage, and next route.
- Broad work boundary (broad work only): the step 4 summary in one line per item, plus the authority or traceable decision the broader boundary needs.

## Researcher Tasks

For each independent important evidence gap:

- Routing decision it supports:
- Questions: at most three closely linked questions
- Likely sources:
- Why the answer could change routing or safety:
- When to stop:

Write `None - existing evidence is enough` when no task is needed.

## Risks And Evidence Gaps

- Important risks or contradictions: at most three
- Remaining important evidence gap, if any:

## Route

- Next action: Iris decides directly / bounded Researcher task(s) / spec writing / user decision / blocked
- User decision needed, if any:
- Confidence: high / medium / low, with the reason and what it covers
- Status: `ready` / `blocked`, with the reason

## Sources

- [S1] Direct path, symbol, command, artifact, or URL
```

Do not repeat these lines as prose.

## Follow-Up Addendum

In a follow-up round, write a short `# Scout Addendum` instead. Point to the earlier packet and record only changed findings, size or boundaries, Researcher tasks, route, and new sources.

## Blocked Packet

```md
# Scout Blocked

- Assignment: `<assignment path>`
- Lens:
- Blocker: the exact missing input
- Evidence checked:
- Needed to continue:
- Status: `blocked`
```

## Final Check

Before you post, confirm each item:

- Only the assigned packet path was written, and the chat post has only the pointer, status, and summary.
- The packet answers the assigned lens and goal as a map and routing advice, not research, a spec, a plan, or a design.
- "What Was Checked" lets someone reproduce the decisive evidence, and each important fact appears once.
- Locations, size, boundaries, and open gaps are clear enough for Iris to route; each independent important gap has one bounded Researcher task.
- Surfaces and sensitive boundaries report only what the scan found, with gaps marked; caller identity was not inferred from networking, shared values, authorization checks, or call order.
- Recommendations, including any `user-approved foundation exception` or other broader surface claimed from direct authority, are traceable and not presented as approval or Iris's decision; authority limits and uncertainty stay visible.

After every applicable item passes, post the chat pointer above.
