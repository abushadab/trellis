# Spec Writing Guide

A spec is a decision document, not a transcript of what you found. If it feels long, cut scope or move detail to a later slice. Do not compress unrelated requirements together. Leave out evidence dumps, history that no longer affects routing, and implementation tasks. Prefer established product and SpecFlow terms.

## Master Specs

A master is a direction memo for Iris, not an implementation source for Ben. Do not create or enlarge a master for one bounded outcome, possible future growth, or extra process. Do not expand it into detailed acceptance criteria, data models, implementation instructions, future edge cases, or a history log.

### Keeping A Master Compact

A refreshed master describes the product and repository as they are now. Git keeps the old versions.

- Replace stale `Current Baseline` text. Do not layer history on top of it.
- Keep each roadmap row to: stable ID, outcome, boundary, impact, dependency, status, and spec or verification link.
- A row identifies a slice. The slice's single spec owns the detailed behavior and acceptance criteria.
- Mark completed rows compactly. Remove resolved risks and superseded explanation. Update dependencies or assumptions that implementation changed.
- State product, ownership, preservation, deferral, and success information once, in `Direction`, `Boundaries`, or the relevant roadmap row. Do not make parallel sections for the same facts.

Compact whenever finished history or repeated context outweighs the remaining direction. A reviewer should be able to find the next complete slice, and what it really touches, without reading an implementation chronicle.

## Single Specs

A single is a compact contract for one task. State:

- the outcome or change;
- fixed decisions, only when needed;
- in, preserve, and out boundaries, with the actual impact;
- constraints that matter; and
- verifiable acceptance, with evidence.

Leave out roadmap narrative, speculative behavior, implementation breakdown, and duplicate sections.

### Verifiable Acceptance Criteria

Each criterion needs a stable ID, one observable outcome, and its best practical evidence. All are blocking unless marked non-blocking.

Example:

```md
| ID | Observable result | Best practical evidence |
| --- | --- | --- |
| AC-1 | When branch creation reports success, the branch record already contains the required secret. | Creation-path inspection and the focused persistence test. |
```

Avoid blended criteria such as "auth works well." Add another criterion only when its outcome can fail independently. These are not separate criteria: non-goals, the absence of speculative architecture, untouched completed slices, inherited quality rules, repeated recipients or tests, and validation activities.

Keep must-not-regress behavior in one preservation boundary. Give it a criterion only when this slice touches the shared path or the evidence shows a distinct regression risk. A main flow that passes through a mechanism this slice changes counts as touching the shared path, even when the flow's own code is unchanged. For untouched earlier behavior, the accepted evidence plus a diff inspection is enough.

For proof that is expensive or specific to one topology, label its lifecycle as one of `permanent regression`, `release certification`, or `historical / one-time experiment`. The default to maintain is the smallest permanent regression that tells the cases apart. Keep broader physical or topology proof when its release or one-time purpose is required. Do not turn that certification or experiment into routine permanent test machinery unless there is a current need to run it regularly.

### Sequential Single Specs

For a later single, treat accepted master and completed-slice boundaries as inherited contracts. Name and link the relevant boundary once. Keep only this slice's change, boundaries, acceptance criteria, and evidence self-contained. Never copy an earlier acceptance-criteria matrix.

## Final Writing Test

Before you publish, confirm:

- the decision is clear near the beginning;
- the scope can be understood without relying on non-goals;
- preservation rules are easy to find;
- current work and future work are clearly apart; and
- the document is easy to scan, not just short.
