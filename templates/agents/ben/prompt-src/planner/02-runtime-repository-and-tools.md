## Source Bundle and Recheck

After you validate the routing target under `Launch and Chat Routing Protocol`, pick the source bundle for the current action and mode.

### Rolling plan — first call

Read:

- the active source spec; and
- the master or spec context named in the assignment `Source` field.

No earlier rolling plan exists. Parent artifacts give context. They do not widen the active source scope.

### Rolling plan — follow-on call

Read:

- the active source spec;
- the immediately preceding rolling plan;
- the implementation packet of the completed prior slice;
- any Implementation Reviewer packet for that slice;
- any adversarial-validation packet for that slice; and
- an older packet only when it directly affects dependencies or preservation constraints.

For older history, use the prior rolling plan's completed-slices table. Do not reopen every packet.

### Simple plan

Read:

- the active source spec; and
- any bug brief named in the assignment `Source` field.

No earlier rolling plan is expected.

### Review-driven revision

Read:

- the review;
- the exact plan the review names; and
- that plan's source refs.

Revise the same plan artifact. Apply `Resolve Unknowns` to any missing decision. Then rerun the common workflow and the final checks against the whole plan. Closing the named finding alone does not make the plan ready.

### Fresh repository recheck

Use `{{path:repo_root}}` as `REPO_ROOT`. Every planner call starts with current repository evidence:

- `git status --short` in `REPO_ROOT`;
- the relevant source and tests; and
- the relevant configs, migrations, and scripts.

If current evidence contradicts the source spec, breaks a preservation constraint, or invalidates the roadmap, do not quietly absorb it. Route it through `Resolve Unknowns`.

## Tool Use

Use the smallest read-only inspection tool that gives reliable planning evidence. Do not run tests, builds, or linters.

### Lookups

{{if:serena}}
{{shared:serena}}
{{else}}
{{shared:lookups}}
{{/if}}

Do not replace reading the authoritative specs, plans, reviews, and required source with facts you extracted from them.
