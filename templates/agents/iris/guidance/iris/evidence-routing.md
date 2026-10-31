# Evidence Routing

## Choose The Route

Use no evidence subagent when direct authority plus the current evidence you already know are enough to choose the next route.

Use a Scout when the open question is **where the relevant capability lives, how much of the code and systems it touches, or which separate factual questions remain**.

Use a Researcher when one bounded factual question could change the next route, the capability boundary, or whether a spec is possible. A Scout is not required first when the relevant code and systems are already known.

Send external public facts (official docs, standards, maintainer sources) to a Researcher. Its source permissions allow bounded public research by default.

Before routing any evidence task, state the one decision its answer can change. Do not gather evidence just because more repository complexity is visible.

## Routing Brief

Give the Assignment Engineer only:

- the actor-visible capability or context;
- the exact factual gap;
- why that fact changes the next route; and
- the strongest direct authority and current evidence pointers you already know.

The Assignment Engineer turns that brief into the Scout or Researcher assignment. Do not write research questions, inventories, bound taxonomies, failure matrices, or architecture hypotheses into the assignment yourself.

Parallelize only independent factual gaps. Stop gathering evidence once the routing decision is supported.

When the evidence reveals a product, authority, or trust choice instead of a factual gap, leave Evidence Routing and use Advisor or user-decision routing. Do the same for a foundational architecture choice that qualifies under the foundational-architecture guide. Do not investigate distant future options by default.
