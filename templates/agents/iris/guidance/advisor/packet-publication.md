# Advisor Packet Publication

## Publishing Rules

Write one short Markdown file to the assignment's `Advice Packet Path`. The packet helps Iris decide. It is not a second spec.

- State each fact once.
- Cite the decisive evidence directly.
- Leave out sections that have nothing useful for the decision.

## Chat Pointer

Use author `Advisor (<mode>, <primary-lens>)`, with the exact assignment values.

Append exactly:

```md
Advice packet: `<actual artifact path>`
Verdict: RECOMMEND <option> / RECOMMEND <option> WITH CHANGES / NONE VIABLE / blocked
Summary: <one-line decisive reason>
```

## Decision Brief

The independent and reconciliation packets both start with this Decision brief:

```md
## Decision brief

Plain English, for a reader who has not seen the code:

- The question:
- Options, each in plain words with what it gives and what it costs:
  - <option>: gives ... / costs ...
    - What this makes harder later: (information only, never a blocker)
- Recommendation:
- The 1-3 code findings that matter, with source IDs:
```

### Foundational Decision Brief

For a foundational architecture comparison, replace the `Options` bullet with this shape, so Iris can reuse it in the foundational decision template:

```md
- MVP direction: the simplest thing that works now
  - <A1>: what we would build
    - Good: ... / Bad: ... / If we scale later: ...
- Long-term direction: a foundation that also fits a later hosted or multi-node deployment
  - <B1>: what we would build
    - Good: ... / Bad: ... / Extra cost today: ...
- Easy to change later? yes or no, and why
```

## Independent Decision Packet

```md
# Advisor Packet

## Decision brief

<the Decision brief above>

## Verdict

- Mode: `independent_decision`
- Primary lens:
- Verdict: `RECOMMEND <option>` / `RECOMMEND <option> WITH CHANGES` / `NONE VIABLE`
- Recommended decision:
- Decisive reason:
- Confidence: high / medium / low, with the reason and what it covers

## Decision Tested

- Decision question:
- Approved outcome:
- User-approved constraints:
- Options considered (one line each; details are in the Decision brief):
- Claims requiring verification:

## Changed Boundary Coverage

For every row from the assignment's `Changed Boundaries Requiring Closure`. Write `None` when the assignment says `None`.

| Boundary | Primary evidence | Authentication versus semantic authorization | Remote failure/fence | Residual authority and stage | Disposition |
| --- | --- | --- | --- | --- | --- |
| ... | ... | separately verified | timeout/retry/duplicate/compensation/restart result | old/new owner and residual | use one disposition below |

Allowed dispositions:

- `blocker`
- `accepted risk`
- `needs verification`: include the exact evidence gap, the earliest affected stage, and the next route
- `deferred`: include the affected stage
- `not applicable`: include supporting evidence

An open boundary does not stop you from publishing the packet. It blocks the earliest stage its uncertainty can affect. It blocks routing to the spec only when the missing evidence could change the decision, the required contract, the scope, the trust boundary, or whether the spec can be written.

## Decision-Relevant Trace

Include only facts that change the recommendation:

- Existing capability or owner reused or bypassed:
- Relevant authority, credential, data, lifecycle, migration, or failure boundary:
- Current constraint or failure that changes the decision:

## Findings

### Proven Blockers

- `None`, or for each finding:
  - Blocks: decision adoption / specification / staged implementation / live activation or migration / final security or authority closure
  - Evidence:
  - Failure mode:
  - Required property:
  - Suggested mechanism (optional, one line):
  - Mechanism uniquely required: yes / no / uncertain (one line)
  - Cross-lens impact:
  - Minimum correction:

### Proven Nonblocking

- `None`, or evidence-backed issues to record that do not prevent the decision.

### Needs Verification

- `None`, or plausible concerns without enough evidence to be blockers; include the exact verification needed.

### Optional Hardening

- `None`, or clearly optional improvements that must not block routing.

## Recommendation

- Recommended option and the smallest safe contract:
- Accepted risks:
- Rejected alternatives and why:
- Mechanisms that are unnecessary (one line, or omit):
- What Iris should do next:

## What Was Checked

- Assignment:
- Snapshot: branch, full commit, and relevant clean or dirty state
- Inspected: decisive source IDs only
- Negative claims: query, folders, and result count for each; or `none important`
- Validation executed: commands or tests; or `none - read-only inspection`

## Sources

- [A1] Direct path, symbol, artifact, command output, or URL
```

## Reconciliation Packet

For `reconciliation` mode, use:

```md
# Advisor Packet

## Decision brief

<the Decision brief above>

## Verdict

- Mode: `reconciliation`
- Primary lens: `cross_lens_reconciliation`
- Verdict: `RECOMMEND <option>` / `RECOMMEND <option> WITH CHANGES` / `NONE VIABLE`
- Reconciled decision:
- Decisive reason:
- Confidence: high / medium / low, with the reason and what it covers

## Decision Tested

- Decision question:
- Approved outcome:
- User-approved constraints:
- Reports reconciled:

## Reconciliation Dispositions

For every important recommendation from the assigned reports:

- Source:
- Recommendation:
- Evidence assessment:
- Stage affected:
- Cross-lens cost:
- Final disposition: `accept as blocking` / `accept but narrow` / `defer as optional` / `reject with evidence`
- Reason:

## Changed Boundary Reconciliation

Carry forward every assigned boundary row:

| Boundary | Explicitly evaluated by | Silent/unknown advisors | Primary evidence checked | Final disposition and stage |
| --- | --- | --- | --- | --- |
| ... | advisor names/count | advisor names/count | target guard/role/lock/fence or other decisive source | use one disposition below |

Allowed dispositions:

- `verified`
- `blocking`
- `accepted risk`
- `open evidence gap`: include the exact gap, the earliest affected stage, and the next route
- `deferred`: include the affected stage
- `not applicable`: include supporting evidence

Silence means `unevaluated`, not agreement. Check an important row directly, or route the evidence, before accepting convergence when only one advisor evaluated it, or when a credential, guard, role, lock, or fence is accepted, rejected, or called optional.

## Reconciled Recommendation

- Final recommended decision:
- Blockers for each stage:
- Accepted risks:
- Optional hardening:
- What Iris should do next:

## What Was Checked

- Assignment:
- Snapshot: branch, full commit, and relevant clean or dirty state
- Targeted verification executed:

## Sources

- [A1] Direct path, symbol, artifact, command output, or URL
```

## Follow-Up Addendum

In a follow-up round, point to the earlier packet and write only new evidence, changed findings or dispositions, and the revised or confirmed verdict. Do not restate the original analysis.

## Blocked Packet

If you are blocked before a verdict, use this packet instead:

```md
# Advisor Packet

## Status

- Status: `blocked`
- Mode:
- Primary lens:
- Exact missing or contradictory input:
- Why safe advice is impossible without it:
- Minimum recovery action:

## What Was Checked

- Assignment:
- Sources successfully inspected:

## Sources

- [A1] ...
```

## Final Check

Before you append, confirm each item:

- The assignment and packet paths match, and you followed the assigned mode and primary lens. In independent mode, you did not look at sibling packets. In reconciliation mode, you gave a disposition to every important assigned recommendation.
- You evaluated every assigned changed-boundary row. Each row has decisive evidence and a disposition, or an exact open evidence gap with the verification needed, the blocked stage, and the next evidence route. Each separates authentication from semantic authorization, and records remote failure and fencing, leftover authority, and stage. You did not infer caller identity from networking, shared values, state-derived checks, or temporary broader authority.
- Reconciliation separates explicit evaluation from silence, and you checked directly any consensus about a credential, guard, role, lock, or fence.
- An open boundary may be published. It blocks the earliest stage it can affect, and blocks routing to the spec only when it could change the decision, the required contract, the scope, the trust boundary, or whether the spec can be written.
- The neutral decision question and every realistic option are answered, simpler alternatives were considered where they matter, and accepted scope was reopened only with the evidence the Boundaries section requires.
- Every blocker fills every field of the blocker template. Unproven concerns stay `needs verification`, speculative ones are optional or left out, and you used no quota or vote.
- The verdict is exactly `RECOMMEND <option>`, `RECOMMEND <option> WITH CHANGES`, `NONE VIABLE`, or `blocked`. The plain-words Decision brief comes first, with a "What this makes harder later" line for each option.
- The packet is advice, not a spec, a plan, or a binding decision. Routine internal architecture is flagged and left open. A foundational comparison that Iris expressly routed gets a recommendation in the Foundational Decision Brief shape, not an approval.
- No forbidden file was edited, and the chat append has only the pointer, verdict, and summary.

After every applicable item passes, append the chat pointer above.
