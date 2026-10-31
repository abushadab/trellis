# Spec Review Packet Publication

## Result Pointer

Append to chat only after the packet passes the final check. Use author `Spec Reviewer (<short-scope>)`. `<short-scope>` is a short stable slug from the assigned review task or lens. Do not use a bare `Spec Reviewer`, because several reviewers may run in parallel.

Append exactly:

```md
Review packet: `<actual artifact path>`
Status: pass / needs_changes / blocked
Summary: <one-line summary>
```

## Review Packet Output

Write one concise Markdown file to `Review Packet Path`.

```md
# Review Packet

## Review Summary

- Status: `pass` / `needs_changes` / `blocked`
- Summary: 3–5 plain lines: what you reviewed, what you found, and what should happen next.

## Findings

### F1: <short title>

- Status impact: `needs_changes`
- Spec location:
- Failure mode:
- Evidence:
- Source conflict or missing requirement:
- Minimal fix direction:
- Verification:
- Confidence: high / medium / low

## Overengineering And Scope Check

- Smallest option that fully and safely meets the need: yes / no
- Unsupported behavior or scope delta: none / <exact delta and missing authority>
- Smaller complete option: none / <option and tradeoff>

## Needs Verification

- ...

## Questions / Assumptions

- ...

## Optional Suggestions

- ...

## Reviewed

- Target spec, direct authority, and repository HEAD:

## Status Rationale

- ...
```

If a section has no important content, write `None identified`. If there are no findings, write:

```md
## Findings

No important findings in the assigned review scope.
```

The `Overengineering And Scope Check` is required in every normal packet. Do not invent a concern to fill it.

## Blocked Review Packet

If required inputs are missing or the target cannot be reviewed, and a valid `Review Packet Path` exists, write:

```md
# Review Blocked

## Status

- Status: `blocked`

## Missing Required Inputs Or Access

- ...

## Why This Blocks Review

- ...

## Needed To Continue

- ...
```

Publish the blocked result through the `Result Pointer` with `Status: blocked`.

## Final Check

Before you finish, confirm each item:

- The packet path and the assignment match the handoff.
- You read the target spec, the needed source and input artifacts, and the original approved authority (or recorded them as unavailable).
- Every finding has a concrete failure mode, evidence, context fit, minimal fix, and verification.
- An overengineering finding that claims a narrower option proves it complete and safe and states its tradeoff. A missing-necessity finding keeps the unresolved alternative under `Needs Verification`.
- Optional preferences are not findings; unresolved intent questions sit under `Questions / Assumptions`.
- You applied the `Overengineering And Scope Check`, the Scope Gate, the Authority And Artifact Gate, and the necessity evidence test.
- You did not treat assignments or reviewer findings as product authority. Decision attribution is accurate and traceable, and any `user-approved foundation exception` or other broader surface claimed from direct authority is traced exactly.
- The MVP slice and the later full-feature goal stay separate.
- Status is exactly one of the three values.
- You edited no forbidden file and wrote no rewrite, plan, task list, code design, file-by-file plan, or Ben handoff.
- The chat append has only the pointer, status, and summary.

After every applicable item passes, append the chat pointer above.
