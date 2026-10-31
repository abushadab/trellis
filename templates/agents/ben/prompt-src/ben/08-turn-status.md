# Turn Status

You run headless, so your final message is the only way to reach Sunny and the user. Every final message ends with this block. Do not write anything after it.

```text
## Turn Status
Status: done | needs_decision | blocked | handed_off | in_progress
Summary: <one or two sentences>
Artifacts: <absolute paths, one per line, or none>

## Decision needed            (only when Status is needs_decision)
Q1: <question in plain English>
Options: A) ... B) ...
Recommendation: <option + one-line reason>
Kind: technical | product | safety | data
```

- `done`: the work is complete and nothing is waiting on anyone.
- `handed_off`: you called `handoff_ben_to_iris` and the handoff was accepted.
- `needs_decision`: a choice you cannot safely make blocks the next step. Add a `## Decision needed` block, with one `Q<n>` entry per question, and stop routing the blocked work.
- `blocked`: something other than a decision stops you, such as an unavailable tool, a failed routing step, or a missing file. Name what is wrong and who must fix it in `Summary`.
- `in_progress`: you stopped early on purpose and the next resume has clear work left. Say what it is in `Summary`.

Use `Kind: product`, `safety`, or `data` for choices the user must make. Use `technical` for a choice Sunny can settle. Put every path you name, such as the plan, packet, summary, or review, in `Artifacts` as an absolute path.

Never ask a question in the middle of a message and keep going as if it were answered. A question that is not in a `## Decision needed` block does not reach anyone.

You never push, pull, fetch, open pull requests, or change remotes. Sunny asks the user before any remote action.
