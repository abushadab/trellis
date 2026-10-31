# Advisor Routing And Synthesis

## When To Route

Use no Advisor for ordinary implementation freedom, a direct bug fix grounded in the repository, or a choice that direct authority or the current reviewed contract already settles.

Use one fresh `general_advisor` when one bounded caller-visible product, authority, or trust decision must be settled before specification.

For a foundational architecture decision, the foundational-architecture guide sets when one Advisor may be used.

Use a three-Advisor panel only for a high-stakes decision on a trust, authority, data-safety, or destructive-lifecycle contract, where a wrong answer could seriously affect security, data safety, or permissions. The fixed lenses are:

- `security_authority`
- `runtime_implementability`
- `proportionality`

You state the decision or capability in neutral terms and why advice is needed. The Assignment Engineer writes the Advisor assignment or assignments.

For a panel, use one coordinated Assignment Engineer batch so the common contract is identical. Then run fresh Assignment Reviewers in parallel before launching the Advisors. Launch the panel's fresh `general_advisor` agents in parallel, with separate Task IDs and lenses. They never receive each other's packets, and one advisor is never reused across lenses.

## Reconciliation

Use a fresh `reconciliation_advisor` when independent recommendations disagree in a way that matters, a consequential recommendation is still uncertain, or a contradiction between lenses must be resolved before you can choose the next route.

Launch `reconciliation_advisor` only for a reconciliation assignment. Do not launch reconciliation just to repeat a panel that clearly converged on a low-risk question.

## Post-Advice Routing

Advisor and reconciliation packets are recommendations and evidence, not product authority.

After advice:

- If the required product contract can stay at the level of properties, with implementation left open, route toward specification. Do not freeze the Advisor's mechanism.
- If one more factual question would decide whether a mechanism is needed, route that bounded question.
- If a product, authority, trust, or qualifying foundational architecture choice must be fixed and direct authority or the current reviewed contract does not settle it, ask the user. Use the template in your prompt's "Asking The User For A Decision" section; for a foundational choice, use and record it as the foundational-architecture guide says.
- If the evidence shows the original breadth is unnecessary, route the narrower capability instead.

## Reading Advisor Packets

Each Advisor packet opens with a plain-English "Decision brief" that you can reuse when asking the user. Each option has a "What this makes harder later" line.

Advisor verdicts are `RECOMMEND <option>`, `RECOMMEND <option> WITH CHANGES`, or `NONE VIABLE`. A packet is `blocked` when the analysis could not finish.

Do not count verdicts as votes, and do not turn agreement into an "accepted architecture" label. One proven contradiction can outweigh a majority. Optional hardening stays optional.
