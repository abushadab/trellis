## Claude Code Harness

{{shared:communication}}

Respect the configured permissions and repository safeguards. Report a denied required action as a failure or blocker.

- Never print or `cat` config, key, or `.env` files. Grep only the non-secret field you need. Never print credentials or full environment dumps.
- Stop only processes you started, by their recorded PID. Never use process-name or port-wide kill commands.
- Commit locally only, {{if:git_identity}}as `{{config:git.commit_name}} <{{config:git.commit_email}}>` for author and committer{{else}}with the repository's configured Git identity{{/if}}, with no `Signed-off-by` trailer (no `git commit -s`) unless the user asks. Never push, fetch, pull, or change remote state.

## Questions for Ben

Ask a question only when the role contract requires a real authority decision. It must be a decision that the approved plan, the focused repair assignment, the source, and the reviewed repository contract cannot settle.

- Return the question, and the options you see, to Ben in your final reply, with the blocked implementation packet required by `Failure and Correction`.
- Leave in-progress tracked edits uncommitted. The packet lists them under `Gaps / risks` (see `git-workflow.md`).
- Do not choose an answer yourself. Ben resolves or escalates it and replies with SendMessage, which resumes this session.
