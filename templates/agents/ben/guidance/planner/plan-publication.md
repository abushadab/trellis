# Plan Publication

## Writing Quality

These rules add plan-specific writing rules to the shared `Writing` rules.

A complete template does not make a plan ready. After every draft or revision, reread the whole plan before you publish.

### Who Reads the Plan

A plan is a decision document, not a record of everything you found.

- The Implementation Engineer needs steps it can execute, checks matched to the risk, expected results from the source, and the runtime facts it must report to prove its claims.
- The Implementation Reviewer needs the boundaries, the risky areas, what must be proved, and any justified advisory adversarial runtime candidate.

### Sections Do Different Jobs

- A step says what changes. Validation says how it is proved. Handoff criteria say what must be true to move on, without repeating the steps or the whole validation section.
- When several sections use the same contract, define it once. Later sections refer to it and add only what is specific to them.
- Add a short reason only when it prevents a wrong implementation.
- Keep every validation field under `Validation`, including the implementation-review decision and `Adversarial runtime candidates`. Do not scatter their facts, triggers, or reasons across steps, risks, handoff criteria, or a flat command list.
  - Keep fixed expected behavior apart from interface facts the implementation will choose.
  - Group focused and static checks apart from live checks that run after a runtime action.

### Implementation Steps

Number the major outcomes. When an outcome needs more than one change, use lettered or bulleted actions.

```md
1. Establish the internal service runtime.
   a. Register the application in the existing build configuration.
   b. Bootstrap it with the established internal-service conventions.
   c. Expose only the required health route.
```

Split a step that changes more than one part that can be reviewed on its own, or that mixes implementation with test commands or evidence requirements.

### Repo Orientation

Repo orientation records decisions and the evidence that changes the plan. It is not a diary of searches, alternatives, and deductions. Each bullet states one fact or boundary, its source path or evidence, and what it means for the plan when that is not obvious. Split a bullet longer than two rendered lines. Remove facts that do not change scope, order, risk, validation, or handoff.

### Final Readability Test

Before you publish, ask:

- Can the Implementation Engineer scan the active slice and know what to build, which evidence each claim needs, and which runtime facts to publish?
- Can the Implementation Reviewer find the risky areas and the proof without reading every paragraph?

If not, restructure the plan without weakening the technical contract or adding scope.

## Output Format

Earlier slice plan files are immutable evidence. Do not overwrite them.

Use this template for both modes. Leave out sections marked `rolling only` in a simple plan.

### Plan Template

```md
Plan packet:

Workitem ID: <workitem-id>
Planning Task ID: <planner-assignment task-id>
Planning Task Name: <planner-assignment task-name>
Mode: rolling | simple
Assignment:
<Spec/workitem and intended outcome.>

Source refs:
- Planner assignment:
- Iris spec/source:
- Prior rolling plan (rolling follow-on only):
- Prior slice evidence (rolling follow-on only; implementation / implementation review / adversarial runtime-validation packet paths):

Repo orientation:
- <Facts inspected, relevant paths, dirty working-tree note.>

Execution proof: <include only when one or more Refresh/Expand/Enumerate checks trigger; omit otherwise>
- Refresh: <current exact value and source path/read-only command>
- Expand: <exact invocation -> complete relevant transitive effects and target match>
- Enumerate: <compact decision table for applicable states/paths/orderings>

Completed slices: <rolling only; carried forward from the prior plan>
| ID | Name | ACs | Implementation | Implementation review | Adversarial/runtime validation | Status |
|---|---|---|---|---|---|---|
| S1 | <name> | <AC-IDs> | <packet path> | <packet path or `—`> | <packet path or `—`> | done |

Open/deferred validation obligations: <rolling only; carried forward from the prior plan. List open rows only. A row stays until its owning slice records passing evidence. Write `None` when empty.>
| Obligation | Owning slice | Status |
|---|---|---|
| <e.g., "apply migration + live grant checks"> | <e.g., S3> | open |

Roadmap change since prior plan: <rolling only>
- none, or <concise delta plus evidence>

Execution roadmap: <rolling only>
| ID | Name | Outcome | ACs | Depends on |
|---|---|---|---|---|
| S1 | <name> | <coarse outcome> | <AC-IDs, preservation constraints> | <prereq slice or `none`> |
| ... | ... | ... | ... | ... |

Active slice: <write `Slice:` in simple mode>
- ID: <S1 / S2 / ...>
- Name: <name>
- Goal:
- Size check: <why this work can be implemented and reviewed together, or the concrete problem requiring a split>
- ACs and preservation constraints:
{{if:design_authority}}
- Design screens and states: <UI slices only: pinned ref from the spec; each screen and state by route or ID; viewer and fixture needed to reach it>
{{/if}}
- Likely files/components:
- Implementation steps:
- Risks: <including anything still unresolved>
- Validation:
  - Independent implementation review: `required` | `none` — <trigger and reason>
  - Adversarial runtime candidates: `none` | <candidate IDs and summaries>
  - <Minimum contract: Evidence matched to the risk; Test/evidence disposition; Implementation Engineer runtime obligation or none>
  - <OR every labeled field defined in Planner Structured Validation>
{{if:design_authority}}
  - UI conformance: <UI slices only: side-by-side design/product screenshots per state, saved under `{{path:workitems_root}}/<workitem-id>/evidence/ui-conformance-r<N>/`>
{{/if}}
- Handoff criteria:

Durable steps: <include only when the active slice adds saved phases, markers, or intents; omit otherwise>
| Step | Resumed by | Ended by (definite outcome) | Releases | On definite failure | On ambiguous failure |
|---|---|---|---|---|---|
| <phase, marker, or intent> | <what resumes it> | <what ends it> | <what it releases, or the hold that rightly outlives it> | <behavior> | <behavior> |

Remaining-roadmap assumptions: <rolling only>
- <Only assumptions the next planner must recheck, e.g. "schema grants unchanged", "service wiring still uses module X".>

Status:
`ready` / `blocked`
```

Keep the plan factual. Leave out research notes, speculative future work, unrelated cleanup, and implementation code. Future rolling slices stay coarse. Simple plans have no roadmap or dependency list.

For a blocked plan:

- keep the identity, the sources, and the facts the source or repository supports;
- when evidence does not support a slice choice, replace the slice section with `Active slice: not established` (rolling mode) or `Slice: not established` (simple mode);
- do not invent a slice ID, a slice name, or any detail the blocker prevents; and
- name the exact decision required.

## Final Check

Before you {{if:commit_specs}}commit{{else}}publish{{/if}}, confirm:

- The plan is at the assigned path. That path had no unexplained overlapping changes before you edited it, and you wrote no other artifact.
- `Workitem ID`, `Planning Task ID`, and `Planning Task Name` match the planner assignment. A ready plan names its downstream slice ID and name.
- A blocked plan follows the blocked-plan rules above. Each blocker is an exact decision, not vague uncertainty.
- For a review-driven revision, you rechecked the whole plan, not only the named findings.
- `Execution proof` and `Durable steps` appear only when triggered, never filled with `none` or `N/A`. When present, `Durable steps` has one row per step with every column filled.
{{if:design_authority}}
- For a ready plan that changes UI: `Design screens and states` names the pinned ref and the design route of every screen-state AC, `UI conformance` names the side-by-side evidence path, and implementation review is `required`.
{{/if}}
- If `Feasibility` applied to a helper-driven action, the plan has the non-mutating preflight that `repository-risk-gates.md` requires.
- The plan meets the rest of your prompt and the guides you read: slice size, gates, validation, implementation review and candidates, and the rolling or simple workflow.

{{if:commit_specs}}
## Git Commit

Commit only after the final check passes. Use one short, stable `<short-scope>` slug for every revision of the plan. Your working directory resets between Bash calls, so run every Git command as `git -C {{path:project_dir}}`. Commit only the exact assigned plan file. Plan paths are tracked project artifacts, so add only the validated path:

```bash
P={{path:project_dir}}
git -C "$P" add -- <plan-file>
git -C "$P" -c user.name="Planner (<short-scope>)" \
    {{if:git_identity}}-c user.email="{{config:git.commit_email}}" {{/if}}commit --only -m "Plan r<round>: <task-id> <mode>" -- <plan-file>
git -C "$P" diff-tree --no-commit-id --name-only -r HEAD
```

The user set up this workflow, so this plan commit is user-authorized. Make it without asking. This does not cover push, pull, fetch, or PRs.

Initial planning is round `1`. A review-driven revision uses its assigned `Revision Round`.

Do not:

- stage or commit another path;
- change unrelated staged or working-tree changes;
- push, amend, bypass hooks, reset, or stash; or
- force a failed commit.

After committing, check that the new commit contains exactly the assigned plan file. If the commit fails, or you cannot establish that single-file scope, report the problem in your final reply and do not append the chat pointer.
{{else}}
## No Plan Commit

This project does not commit plans. Leave the plan file in place, uncommitted. Do not stage or commit any path, and do not push, amend, reset, or stash.

Initial planning is round `1`. A review-driven revision uses its assigned `Revision Round`.
{{/if}}

## Result Pointer

Append a result only after the plan packet passes its final checks{{if:commit_specs}} and its plan-only commit succeeds{{/if}}.

For initial planning, append only:

```md
Plan ready: `{{path:workitems_root}}/<workitem-id>/plans/<slug>-plan.md`
Status: `ready` / `blocked`
Summary: <one sentence>
```

For a revision, use the same `Revision Round` and append only:

```md
Plan revised: `{{path:workitems_root}}/<workitem-id>/plans/<slug>-plan.md`
Status: `ready` / `blocked`
Round: <N>
Summary: <one sentence>
```
