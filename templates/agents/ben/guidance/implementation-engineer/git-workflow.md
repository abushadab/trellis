# Implementation Engineer Local Git Workflow

Use this guide only for authorized Implementation Engineer changes in `{{path:repo_root}}`, or, for a lane workitem, in the `Workitem root` your launch names. Run each Git command below through `git -C <REPO_ROOT>`, where `REPO_ROOT` is the workitem root for a lane workitem.

## Commit the Implementation

The user set up this workflow, so the commits this guide defines are user-authorized. Make them without asking.

After implementation and engineer-owned validation:

1. Review `git status --short` and the full worktree diff.
2. Stage only authorized paths or hunks, with explicit `git add -- <path>...`.
3. Inspect `git diff --cached --name-only` and the full `git diff --cached`.
4. Run `git diff --cached --check`.
5. Commit with both author and committer set to:

   `Abu Shadab <abu@ai2.at>` (workspace `AGENTS.md`), with no `Signed-off-by` trailer

   Use a short subject in the imperative. For substantial work, add a compact body with `Why:`, `What changed:`, and `Validation:`. Add no trailers that copy packet contents.

6. Verify the new commit. Record its SHA in the implementation packet.

The commit must contain every tracked Implementation Engineer edit for that packet. It must contain nothing outside the assigned scope. Do not publish a completed implementation packet without the commit it names.

A `blocked` packet does not commit unproven work. Leave in-progress tracked edits uncommitted, so the same session can finish them once the blocker is resolved. List each uncommitted path under `Gaps / risks`, and write `Commit: none — uncommitted edits listed in Gaps / risks`.

Each review correction gets its own commit and its own SHA. Never amend or replace a commit that you already handed to review.

## Prohibited Actions

Do not:

- use `git add -A`, `git add .`, `git commit -a`, or broad wildcard staging;
- commit secrets, generated runtime artifacts, unrelated changes, or another role's edits;
- amend, rebase, reset, restore, revert, cherry-pick, merge, squash, or rewrite history;
- push, fetch, pull, create a PR, or change remote state;
- change Git configuration; or
- bypass hooks (`--no-verify`). A failing hook is a failing check.

Never create an empty commit.

- If you are blocked before any tracked edit, record `No commit required` and the exact blocker.
- If completed work has no tracked difference, report that mismatch to Ben, except in an evidence-only round (see `Required Output`).
