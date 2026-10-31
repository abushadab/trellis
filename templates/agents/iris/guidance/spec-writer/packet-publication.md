# Spec Packet Publication

This guide defines the blocked-spec shape, the final check, the Git commit, and the chat post. It points you to the source and template guides for a normal spec.

## Publication Rules

Use only these routable statuses:

- `ready_for_ben`: a `single` that meets the behavior-ready contract with no important open decision.
- `ready`: a `master`, or a reviewable spec that is not yet ready for Ben.
- `blocked`: no safe spec can be written within the valid assignment and the available authority.

## Writing A Normal Spec

For a spec that is not blocked, first read `{{path:guidance:iris}}/spec-writer/source-references.md` completely. Then read exactly one matching template completely:

- `master`: `{{path:guidance:iris}}/spec-writer/master-spec-template.md`
- `single`: `{{path:guidance:iris}}/spec-writer/single-spec-template.md`

Do not read the other mode's template. If the source guide or the template cannot be read, stop before writing. Report the exact problem.

## Blocked Spec

When missing inputs or decisions prevent a safe spec, and routing gives a valid `Spec Output Path`, write exactly the shape below. A blocked note does not need the normal-spec shape or a separate source registry. Record what you inspected under `Evidence Checked`.

```md
# Spec Blocked

## Status

- Status: `blocked`
- Mode: `master` / `single`

## Missing Required Inputs Or Decisions

- ...

## Why This Blocks Writing

- ...

## Evidence Checked

- ...

## Needed To Continue

- ...
```

For a scope-escalation block, also add:

```md
## Broader Boundary Discovered

- ...

## Narrower MVP Option And Tradeoff

- ...

## Explicit User Decision Needed

- ...
```

## Git Commit

Use one short, stable `<short-scope>` slug for chat authorship and the commit author name. The Git repository is `/home/abu/project-attestara/claude-workspace/`. There is no separate specflows repository. Commit as `Spec Writer (<short-scope>) <abu@ai2.at>`, the Attestara workspace convention, with no `Signed-off-by` trailer.

Every spec is under the ignored `specflows/` folder. Stage only the assigned spec file, with `git add -f -- <spec-file>`. Never force-add another path or change ignore rules.

Your working directory resets between Bash calls, so run every Git command as `git -C "$WS"`.

Other writers and Ben's planners publish to the same repository at the same time, including parallel lane writers. Run the stage, verify, and commit steps in one shell call under the publication lock, and hold it only for those steps:

```bash
flock -w 600 /home/abu/project-attestara/claude-workspace/.git/agents-publication.lock bash -c '
set -e
WS=/home/abu/project-attestara/claude-workspace
git -C "$WS" add -f -- <spec-file>
git -C "$WS" diff --cached --check -- <spec-file>
test "$(git -C "$WS" diff --cached --name-only)" = "<spec-file>"
git -C "$WS" -c user.name="Spec Writer (<short-scope>)" -c user.email="abu@ai2.at" commit -m "Spec r<round>: <task-id> <mode>" -- <spec-file>
'
```

If the wait times out, try again. Never delete the lock file.

The user set up this workflow, so this spec commit is user-authorized. Make it without asking. This does not cover push, pull, fetch, or PRs.

Do not commit other files, push, amend, bypass hooks, or force a failed commit. If staging holds any other path, or the commit fails, report it in your final reply and do not post the chat pointer.

## Chat Pointer

After a successful commit, call `append_chat(specflow_id, author, message)` once. Use author `Spec Writer (<short-scope>)` and post exactly:

```md
Spec packet: `<actual artifact path>`
Mode: `master` / `single`
Status: ready / ready_for_ben / blocked
Summary: <one-line summary>
```

## Final Check

Before you commit, confirm each applicable item:

- **Routing:** launch, lookup, and assignment agree; you read every assigned input or named it unavailable; you wrote only the assigned file, over no unexplained changes.
- **Authority:** every important behavior change traces to a source in Source Authority. Contradictions, assumptions, and open decisions stay visible. The source registry supports every important claim.
- **Scope gate:** the smallest-option rules, `Impact`, caller inputs and shared-mechanism flows, necessity evidence, Broad Work, and the size trigger are applied as your prompt says. The immediate MVP and the later goal stay separate.
- **Finality:** where it applies, the guarantee, its proving record or honest limit, and each non-final state's resume, end, and release are stated.
- **Shape:** the mode is justified. A `single` has stable, evidence-backed, blocking-by-default ACs for independently failing outcomes, and no duplicate sections, criteria for untouched inherited behavior, restated validation, or implementation tasks.
- **Status:** the status and output shape are correct, and no blocker is marked ready.
- **Revisions:** path and task identity are unchanged; only the routed change was made; unaffected content is kept and superseded wording removed.

When every check passes, commit the required file with the required message and identity. Confirm the commit succeeded and holds no unrelated file. Then post the chat pointer once.
