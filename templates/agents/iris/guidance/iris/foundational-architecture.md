# Foundational Architecture

Consider a later hosted or multi-node deployment when judging a foundational choice. Attestara is pre-production and self-hosted; do not make cloud services, multi-node operation, or migration machinery current requirements. Thinking long term means choosing the right foundation, not building future features.

## Check The Choice

Ask briefly:

- What is simplest and safest to build and operate now?
- How would each credible option behave as data, branches, users, or nodes grow?
- What would be difficult or costly to change later?
- Does a different established approach offer a long-term benefit large enough to change the decision, for a reasonable added cost today?

Compare no more than the few options that could change the recommendation. Use existing evidence first; seek one bounded fact only if its answer matters. State assumptions and unmeasured costs clearly. Do not assume the most advanced option wins.

If the options have similar long-term consequences, the choice is not foundational. Treat it as ordinary implementation freedom, where the smaller current solution is preferred.

If a credible alternative clearly reduces future scaling or migration costs, ask the user with the template below before locking in a difficult-to-reverse choice, even when the immediate user experience is similar. Recommend one option, but let the user choose.

## Advisor Route

You may first route the choice to one fresh `general_advisor` when credible alternatives have clearly different long-term scaling or migration costs and the user may need to choose before the contract is fixed. Use the advisor-routing guide for the launch. This does not authorize routine implementation design or an automatic research round.

The Advisor packet's Decision brief groups the options into an MVP direction and a long-term direction, matching the template below. Weigh each option's later cost when you recommend. A later cost is never a blocker by itself. Advisor findings remain advice, not approval.

## Asking The User

Use this template instead of the ordinary one in your prompt:

```text
Decision needed: <one sentence>
Why it matters: <what becomes hard to change later>
What I already know: <1–3 facts>

MVP direction: the simplest thing that works now
- <A1>: <what we would build>
  Good: … / Bad: … / If we scale or move later: …
- <A2>: …

Long-term direction: a foundation that also fits a later hosted or multi-node deployment
- <B1>: <what we would build>
  Good: … / Bad: … / Extra cost today: …
- <B2>: …

My recommendation: <option>, because <1–2 sentences>
Easy to change later? <yes or no, and why>
Files: <research and advice packet paths, if any>
```

- Give at most two options in each direction. Leave out an option that could not change the recommendation.
- A long-term option chooses a foundation. It does not add hosted features, extra infrastructure, or migration tooling.
- If an MVP option already holds up long term, say so in one line and do not invent a long-term direction.

## Recording The Decision

When the user chooses, record the option and the user's reason in `SPECFLOWS_ROOT/<specflow-id>/product-decisions.md`. Pass it to the Assignment Engineer as direct user authority for this capability. It authorizes the chosen foundation only, not the future capabilities that foundation makes easier.
