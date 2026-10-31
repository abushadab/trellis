# Research Packet Publication

## Publishing Rules

Write one short Markdown file to the assignment's `Research Packet Path`.

- Do not replay the assignment, your browsing process, or every fact you inspected.
- Use the templates below as a contract for what to cover, not as a form to fill in. Leave out risks, deferrals, searches, or validation details that cannot change the immediate route.

## Chat Pointer

Use author `Researcher (<short-scope>)`. `<short-scope>` is a short stable slug from the assigned question or task. Do not use a bare `Researcher`; several researchers may run at once.

Post exactly:

```md
Research packet: `<actual artifact path>`
Status: ready / blocked
Summary: <one-line summary>
```

## First Packet

```md
# Research Packet

- Assignment: `<assignment path>`

## Summary

3–5 plain lines: what you were asked, what you found, and what should happen next.

## Answers

### <Assigned question>

- Answer:
- Rationale:
- Evidence: [R1]
- Confidence: high / medium / low
- Remaining uncertainty: <omit when none>

## Boundary And Route

- Routing decision supported:
- Immediate boundary and stopping condition:
- Next action: Iris decision synthesis / spec writing / user decision / bounded evidence / blocked
- Status: `ready` / `blocked`

## Changed Boundary Closure

Include only when the assignment concerns an important changed remote edge or authority boundary. One line per boundary: its route-changing dimensions from the prompt's Changed Remote Edges And Authority, and `verified` or `open evidence gap`.

## Evidence

- Inspection or validation: <snapshot and checks that matter, or `read-only inspection`>
- Counter-evidence checked: <strongest challenge, or no important counter-evidence in the searched boundary>
- [R1] <direct path, symbol, command, artifact, paper, standard, or URL>
```

- For several assigned questions, repeat only the answer block.
- Add `Alternatives Considered` only when a real choice affects the route. Compare options as step 6 of the prompt describes, and also state the authority each one needs.
- Add deferred work, constraints, risks, authority issues, or a needed user decision under `Boundary And Route` only when they matter to the decision.
- Label inferences and assumptions inline. Keep each source ID to one coherent source.

## Follow-Up Addendum

In a follow-up round, write a short `# Research Addendum` instead. Point to the prior packet and record only the changed answer, route, and new evidence.

## Blocked Packet

```md
# Research Blocked

- Assignment: `<assignment path>`
- Question:
- Blocker:
- Evidence checked:
- Needed to continue:
- Status: `blocked`
```

## Final Check

Before you post, confirm each item:

- The packet names the routing decision and stopping condition, and every assigned question has a direct answer or an exact blocker.
- Rationale and confidence match the evidence; counter-evidence and important uncertainty are visible.
- Work needed now and later-goal work stay apart; alternatives appear only when they affect the route, and scope growth is not presented as approved.
- Each changed remote or authority boundary keeps caller authentication separate from semantic authorization; each open route-changing row has its gap, earliest stage, and next route.
- A claim that a credential, guard, role, lock, or fence is sufficient cites the target's decision logic and negative evidence.
- Sources and negative-claim searches can be reproduced; status is `ready` or `blocked`.
- Only the assigned packet changed, and the chat post has only the pointer, status, and summary.

After every applicable item passes, post the chat pointer above.
