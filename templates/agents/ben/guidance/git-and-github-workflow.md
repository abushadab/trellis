# Ben Git and GitHub Workflow

Use this guide for Git and GitHub operations in `{{path:repo_root}}`, and in lane worktrees (see `Lane Workitems`).

User instructions, Ben's system prompt, and repository policy come first. If this guide contradicts them, stop before you change anything in Git.

## Authority

Ben owns creating and switching branches, finalizing slices, cleaning up local temporary branches, and every remote or GitHub action.

Only the Implementation Engineer may create specialist commits in the product repository. It may do so only on the temporary slice branch that Ben prepared under this guide. It may not create or switch branches, rewrite history, or change remote state. The Implementation Reviewer, the Independent Final Validator, the planners, and the investigator stay read-only in the product repository.

Managing local workitem and slice branches, and preparing and committing local squashes, are standing workflow authority. Do them without asking. Fetch, pull, push, PR creation, merge, and deleting user-facing or remote branches need the user's authority, as described below.

## Branch Model

Use:

- one user-facing branch for the workitem: `ben/<workitem-id>`; and
- one temporary branch for the active slice: `work/<workitem-id>`.

Create the temporary branch from the current `ben/<workitem-id>`. When the slice passes, squash it into the user-facing branch right away and delete it. For the next slice, recreate `work/<workitem-id>` from the updated user-facing branch.

Before you create or switch branches:

1. Check `git status --short`, the current branch, and the intended base.
2. For a new user-facing branch, work out the base instead of guessing when stacked work is possible.
3. Keep every unrelated user change. If switching would overwrite, hide, or mix with that work, stop and ask the user.

Never stash, reset, restore, move, or discard user work to make a branch switch possible. Use a separate worktree only when you need the isolation and the user agrees.

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
2. author and committer are both `Abu Shadab <abu@ai2.at>` (workspace `AGENTS.md`);
3. the commit diff and paths match the packet and the assigned scope;
4. no unrelated user change, secret, or generated runtime artifact was committed; and
5. no tracked edit that belongs to the workitem is left uncommitted.

For a `blocked` packet (`Commit: none — uncommitted edits listed in Gaps / risks`), skip these checks. Instead confirm that the listed paths match the dirty worktree, and keep those edits for the engineer's resumed round.

A correction uses a new commit. Do not amend, replace, rebase, or otherwise rewrite a commit that has gone to review.

## Finalize Each Slice

After the slice gate passes:

1. Verify the temporary slice branch is clean and contains the exact commit that the slice gate accepted. Required implementation review must accept that commit, and every required adversarial challenge must be closed under `Slice Gate`. Earlier test or runtime results may support acceptance under `Review and Validation Rules`; keep their actual execution source and checked reuse explanation in the workitem.
2. Switch to `ben/<workitem-id>`.
3. Run `git merge --squash --no-commit work/<workitem-id>`.
4. Inspect the staged names, the complete staged diff, and `git diff --cached --check`.
5. Create one commit with `Abu Shadab <abu@ai2.at>` as author and committer.
6. Compare the final commit tree with the temporary branch using `test "$(git rev-parse HEAD^{tree})" = "$(git rev-parse work/<workitem-id>^{tree})"`.
7. Keep the source Implementation Engineer commit and the final squash commit for the summary. When test or runtime evidence will transfer, also check `Authorized Squash Rebinding` in the closure guide.
8. Delete the squash-only branch with `git branch -D work/<workitem-id>`.

A tree mismatch is an implementation change, not cleanup. Stop and return to the Implementation Engineer.

Only this squash may rebind accepted evidence to the final commit by exact tree equality. Ordinary reuse across later commits follows `Review and Validation Rules` and keeps the actual execution source. Do not use tree equality to transfer evidence through a rebase, cherry-pick, rewritten commit, or unrelated commit.

Never create an empty commit. If a slice produces no tracked difference, note that briefly and remove the temporary branch. Do not invent extra fields to record who did what.

## Identities

Use these fixed identities:

- Implementation Engineer commits and the final slice commit: `Abu Shadab <abu@ai2.at>` (workspace `AGENTS.md`), with no `Signed-off-by` trailer

Supply the identity to each commit, or use repository-local configuration that is already correct.

The final Abu-authored commit may carry workitem, slice, and AC trailers when they help.

## Lane Workitems

A lane workitem comes from a Iris lane handoff and runs beside other lanes. These rules apply only to lane workitems. The rest of this guide still applies, inside the lane's worktree. Also follow `{{path:guidance:ben}}/lanes-shared-rules.md`.

### Binding

At launch and at every resume, record in `{{path:workitems_root}}/<workitem-id>/lane-binding.md`:

- the lane id;
- the workitem and Task ids;
- the reviewed spec path and the workspace commit that holds that version;
- the integration commit you start from;
- the workitem root and the lane runtime; and
- your session label (see `Single Session Owner`).

On every resume, check these again against the handoff and the worktree. Stop on a mismatch.

### Single Session Owner

One session owns a lane workitem for its whole life. This is separate from the MCP's per-operation locks.

- Claude Code does not give you a session id. Name your session with a unique label: the lane id plus the launch timestamp, for example `lane-F-20261020T181500Z`.
- At launch, create `{{path:workitems_root}}/<workitem-id>/session.lock` containing that label, with a no-clobber write (`set -o noclobber`).
- If it already exists and names another session, refuse the launch or resume and report it. Do not remove it. The label you wrote this session, recorded in `lane-binding.md`, is how you recognize your own lock after a context compaction.
- Remove it when your session ends. Only the user removes a lock left by a session that died.

### Worktree

- The workitem root is `/home/abu/project-attestara/worktrees/<workitem-id>`. It is pre-approved, so it needs no separate user agreement.
- Create it from the bound integration commit: `git -C {{path:repo_root}} worktree add -b ben/<workitem-id> /home/abu/project-attestara/worktrees/<workitem-id> <integration-commit>`.
- Your session starts in `{{path:agent_root:ben}}`, where its config lives. The workitem root, not the working directory, decides where work happens: give it to every specialist and use it for every path and Git command (`git -C <root>`).
- Specialists do not use Serena in a lane workitem. They use Read, `rg` and `find` through Bash, and `git -C <Workitem root>`.
- The workitem root replaces `REPO_ROOT`. Run every Git command there. Never switch branches in the shared checkout for a lane.
- The branch model, slice branch, and squash flow above run inside it, unchanged.
- Add `Workitem root: <path>` to every specialist launch and assignment.
- When Iris releases the lane at a newer integration commit, merge `integration` into `ben/<workitem-id>` and update the binding. Merging `integration` into `dev` stays with the owner.

### Runtime

- Run every check with the explicit-target contract, as `contrib/testing/test-evidence-flow.sh` does: `PROBO_E2E_EXPLICIT_TARGET=1` plus the lane's own database, binary, fixture root, mail, storage, and listeners.
- Never touch `probod`, `probod_test`, or port 8080.
- The lane runtime in the binding wins over `/home/abu/project-attestara/workspace/RUNTIME.md`. Name it in every assignment that runs anything.

## Remote Operations

Do not fetch, pull, merge, or rebase only because a base moved. Syncing needs user direction or repository policy.

Push or create a PR only when the user explicitly asks and required closure has passed. An explicit PR request includes permission to push the user-facing branch when needed. It does not include permission to merge or delete it.

Merge only when explicitly asked, and use the strategy the user chose or the repository requires. Delete user-facing or remote branches only after the merge and with explicit authorization.

Report the PR URL, the final user-facing commit, and the validation state.

### Remote-Operation Checklist

Before any push, pull request, or other GitHub action, read `/home/abu/project-attestara/AGENTS.md` completely. It governs every remote action. Then confirm each item:

1. The user explicitly asked for this push, PR, merge, or other remote mutation. A local commit never authorizes one.
2. `git config --local user.name` is `Abu Shadab` and `git config --local user.email` is `abu@ai2.at`. Set them repository-locally when they differ. Add no `Signed-off-by` trailer unless the user asks.
3. `git remote -v` shows the exact push URL `git@github-ai2:KI-Quadrat/<repo>.git`. Stop if the destination is anything else, including `git@github.com:KI-Quadrat/...`, an HTTPS KI remote, a personal fork, or `upstream`.
4. Use only `ghki <command>` for GitHub CLI work. Before a GitHub API mutation, `ghki api user --jq .login` must print exactly `abushadab26`. Never run bare `gh`, `/usr/bin/gh`, or `GH_CONFIG_DIR`. If `ghki` is missing, expired, or refuses to run, stop and ask the user.
5. Never print or commit tokens, private keys, kubeconfig files, or database dumps.
