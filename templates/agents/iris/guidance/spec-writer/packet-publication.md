# Spec Packet Publication

This guide defines the blocked-spec shape, the final check, {{if:commit_specs}}the Git commit, {{/if}}and the chat post. It points you to the source and template guides for a normal spec.

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

{{if:commit_specs}}
Use one short, stable `<short-scope>` slug for chat authorship. The Git repository is the one that contains `{{path:project_dir}}`. There is no separate specflows repository, and the project's `.trellis/.gitignore` already excludes specs from its ignore rules.

Stage only the assigned spec file, with `git add -- <spec-file>`. Never stage another path or change ignore rules. In the commands below, `<spec-file>` is the spec path relative to the repository root.

Your working directory resets between Bash calls, so run every Git command as `git -C "$REPO"`.

Other writers and Ben's planner publish to the same repository, possibly at the same time. Run the stage, verify, and commit steps in one shell call under the publication lock, and hold it only for those steps. If `flock` is not installed, run the same steps without it.

```bash
REPO="{{path:project_dir}}"
flock -w 600 "$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir)/trellis-publication.lock" bash -c '
set -e
REPO="{{path:project_dir}}"
git -C "$REPO" add -- <spec-file>
git -C "$REPO" diff --cached --check -- <spec-file>
test "$(git -C "$REPO" diff --cached --name-only)" = "<spec-file>"
{{if:git_identity}}git -C "$REPO" -c user.name="{{config:git.commit_name}}" -c user.email="{{config:git.commit_email}}" commit -m "Spec r<round>: <task-id> <mode>" -- <spec-file>{{else}}git -C "$REPO" commit -m "Spec r<round>: <task-id> <mode>" -- <spec-file>{{/if}}
'
```

{{if:git_identity}}
The identity above is the project's configured commit identity.
{{else}}
The commit uses the repository's own Git identity. Do not set or change it.
{{/if}}
Add no `Signed-off-by` trailer.

If the wait times out, try again. Never delete the lock file.

`commit_specs: true` in the project's Trellis config is the user's authorization for this spec commit. Make it without asking. This does not cover push, pull, fetch, or PRs.

Do not commit other files, push, amend, bypass hooks, or force a failed commit. If staging holds any other path, or the commit fails, report it in your final reply and do not post the chat pointer.
{{else}}
Do not commit. Leave the spec file at its assigned path; the user's Trellis config does not authorize spec commits.
{{/if}}

## Chat Pointer

{{if:commit_specs}}After a successful commit, {{else}}Once the spec is written, {{/if}}call `append_chat(specflow_id, author, message)` once. Use author `Spec Writer (<short-scope>)` and post exactly:

```md
Spec packet: `<actual artifact path>`
Mode: `master` / `single`
Status: ready / ready_for_ben / blocked
Summary: <one-line summary>
```

## Final Check

Before you {{if:commit_specs}}commit{{else}}post the chat pointer{{/if}}, confirm each applicable item:

- **Routing:** launch, lookup, and assignment agree; you read every assigned input or named it unavailable; you wrote only the assigned file, over no unexplained changes.
- **Authority:** every important behavior change traces to a source in Source Authority. Contradictions, assumptions, and open decisions stay visible. The source registry supports every important claim.
- **Scope gate:** the smallest-option rules, `Impact`, caller inputs and shared-mechanism flows, necessity evidence, Broad Work, and the size trigger are applied as your prompt says. The immediate MVP and the later goal stay separate.
- **Finality:** where it applies, the guarantee, its proving record or honest limit, and each non-final state's resume, end, and release are stated.
- **Shape:** the mode is justified. A `single` has stable, evidence-backed, blocking-by-default ACs for independently failing outcomes, and no duplicate sections, criteria for untouched inherited behavior, restated validation, or implementation tasks.
- **Status:** the status and output shape are correct, and no blocker is marked ready.
- **Revisions:** path and task identity are unchanged; only the routed change was made; unaffected content is kept and superseded wording removed.

{{if:commit_specs}}When every check passes, commit the required file with the required message and identity. Confirm the commit succeeded and holds no unrelated file. Then post the chat pointer once.{{else}}When every check passes, post the chat pointer once.{{/if}}
