# Ben Git and GitHub Workflow

Use this guide for Git operations in `{{path:repo_root}}`.

User instructions, Ben's system prompt, and repository policy come first. If this guide contradicts them, stop before you change anything in Git.

## Authority

Ben owns creating and switching branches, finalizing slices, and cleaning up local temporary branches. Remote actions are not yours (see `Remote Operations`).

Only the Implementation Engineer may create specialist commits in the product repository. It may do so only on the temporary slice branch that Ben prepared under this guide. It may not create or switch branches, rewrite history, or change remote state. The Implementation Reviewer, the Independent Final Validator, the planners, and the investigator stay read-only in the product repository.

Managing local workitem and slice branches, and preparing and committing local squashes, are standing workflow authority. Do them without asking. Fetch, pull, push, PR creation, merge, and deleting user-facing or remote branches are not yours: see `Remote Operations`.

## Branch Model

Use:

- one user-facing branch for the workitem: `{{config:git.branch_prefix}}<workitem-id>`; and
- one temporary branch for the active slice: `{{config:git.work_branch_prefix}}<workitem-id>`.

Create the temporary branch from the current `{{config:git.branch_prefix}}<workitem-id>`. When the slice passes, squash it into the user-facing branch right away and delete it. For the next slice, recreate `{{config:git.work_branch_prefix}}<workitem-id>` from the updated user-facing branch.

Before you create or switch branches:

1. Check `git status --short`, the current branch, and the intended base.
2. For a new user-facing branch, work out the base instead of guessing when stacked work is possible.
3. Keep every unrelated user change. If switching would overwrite, hide, or mix with that work, stop and put the question in your final message (`Status: needs_decision`, `Kind: technical`).

Never stash, reset, restore, move, or discard user work to make a branch switch possible. Use a separate worktree only when your launch prompt approves it.

## Sequential Write Ownership

Only one specialist that changes files may own the repository at a time.

Before you launch the Implementation Engineer:

- confirm the active temporary slice branch;
- confirm there is no unexplained dirty state from another writer; and
- identify the relevant user changes that already exist.

Give the engineer the active branch name. It commits every tracked implementation or correction before it publishes a `complete` implementation packet and hands ownership on. A `blocked` packet leaves in-progress tracked edits uncommitted and lists them under `Gaps / risks`.

The Implementation Reviewer and the Independent Final Validator inspect or run against the exact commit that accepted packets name.

## Verify Implementation Engineer Commits

Before you accept an Implementation Engineer commit or route it to another evidence role, check that:

1. the SHA exists and is on the active temporary slice branch;
2. author and committer are both {{if:git_identity}}`{{config:git.commit_name}} <{{config:git.commit_email}}>`{{else}}the identity set in the repository's Git config{{/if}};
3. the commit diff and paths match the packet and the assigned scope;
4. no unrelated user change, secret, or generated runtime artifact was committed; and
5. no tracked edit that belongs to the workitem is left uncommitted.

For a `blocked` packet (`Commit: none — uncommitted edits listed in Gaps / risks`), skip these checks. Instead confirm that the listed paths match the dirty working tree, and keep those edits for the engineer's resumed round.

A correction uses a new commit. Do not amend, replace, rebase, or otherwise rewrite a commit that has gone to review.

## Finalize Each Slice

After the slice gate passes:

1. Verify the temporary slice branch is clean and contains the exact commit that the slice gate accepted. Required implementation review must accept that commit, and every required adversarial challenge must be closed under `Slice Gate`. Earlier test or runtime results may support acceptance under `Review and Validation Rules`; keep their actual execution source and checked reuse explanation in the workitem.
2. Switch to `{{config:git.branch_prefix}}<workitem-id>`.
3. Run `git merge --squash --no-commit {{config:git.work_branch_prefix}}<workitem-id>`.
4. Inspect the staged names, the complete staged diff, and `git diff --cached --check`.
5. Create one commit with {{if:git_identity}}`{{config:git.commit_name}} <{{config:git.commit_email}}>`{{else}}the identity set in the repository's Git config{{/if}} as author and committer.
6. Compare the final commit tree with the temporary branch using `test "$(git rev-parse HEAD^{tree})" = "$(git rev-parse {{config:git.work_branch_prefix}}<workitem-id>^{tree})"`.
7. Keep the source Implementation Engineer commit and the final squash commit for the summary. When test or runtime evidence will transfer, also check `Authorized Squash Rebinding` in the closure guide.
8. Delete the squash-only branch with `git branch -D {{config:git.work_branch_prefix}}<workitem-id>`.

A tree mismatch is an implementation change, not cleanup. Stop and return to the Implementation Engineer.

Only this squash may rebind accepted evidence to the final commit by exact tree equality. Ordinary reuse across later commits follows `Review and Validation Rules` and keeps the actual execution source. Do not use tree equality to transfer evidence through a rebase, cherry-pick, rewritten commit, or unrelated commit.

Never create an empty commit. If a slice produces no tracked difference, note that briefly and remove the temporary branch. Do not invent extra fields to record who did what.

## Identities

Use this identity:

- Implementation Engineer commits and the final slice commit: {{if:git_identity}}`{{config:git.commit_name}} <{{config:git.commit_email}}>`{{else}}the identity set in the repository's Git config{{/if}}, with no `Signed-off-by` trailer

Supply the identity to each commit, or use repository-local configuration that is already correct.

The final slice commit may carry workitem, slice, and AC trailers when they help.

## Remote Operations

You never fetch, pull, push, create or merge a PR, delete a remote branch, or change a remote. The rendered settings deny these commands. Sunny, the interactive agent, asks the user before any remote action and runs it.

- Do not fetch, pull, merge, or rebase only because a base moved. If the base moved and it matters, say so in your final message with `Status: needs_decision`.
- When required closure has passed, report the final user-facing branch (`{{config:git.branch_prefix}}<workitem-id>`), the final user-facing commit, and the validation state. Sunny offers the push or PR to the user from that report.
- Never print or commit tokens, private keys, kubeconfig files, or database dumps.
