# Implementation Engineer Publication

When the assigned implementation and engineer-owned validation are complete or blocked, write one concise implementation packet for the current round. The packet reports the implementation and its evidence.

## Result Pointer

Append this only after the packet passes `Final Check`:

```md
Implementation packet: `{{path:workitems_root}}/<workitem-id>/implementations/<slug>-implementation-r<N>.md`
Status: `complete` / `blocked`
Summary: <one sentence>
```

## Output Format

Write one immutable packet under `{{path:workitems_root}}/<workitem-id>/implementations/`. Name it `<slug>-implementation-r<N>.md`, where `<slug>` is the lowercased Task ID, followed by `-<nickname>` when your launch input has a `Nickname:` line, and `<N>` is the round. Create a new packet for each correction round.

```md
Implementation packet:

Workitem ID: <workitem-id>
Task: <Task ID> — <Task Name>
Round: <N>
Commit: <exact commit; the unchanged reviewed commit for an evidence-only round; `none — uncommitted edits listed in Gaps / risks` when blocked after tracked edits; or `No commit required` only when blocked before tracked edits>
Branch / base: <active branch and relevant base>
Source: <ready plan or focused repair and authoritative spec/source>

Work completed:
- <concise outcome and decisive changed paths>

Planned-assertion corrections:
<Omit when none. For each correction, name the planned expectation, corrected expectation, higher-priority source, and affected checks.>

Seams touched:
- <seam kind>: <one side, path and symbol> <-> <other side, path and symbol>

Evidence:
- <requirement or risk>: <repository path, focused command/test ID, or runtime result>: <result>

Runtime evidence:
<Omit when none. Repeat this block for each tightly related runtime claim set.>
- Claim:
- Command or entrypoint and result:
- Tested source, image, and configuration identity:
- Fixtures and mutation boundary:
- Cleanup:
- Freshness assumptions and limits:

Correction impact:
<Omit in round 1. Name the prior implementation packet and the result that triggered this round. Then name affected evidence to rerun, and accepted evidence that stays fresh, with the reason.>

Gaps / risks:
<Omit when empty. Otherwise name the exact missing, failed, stale, contradictory, unclear, or unsupported item and next owner. A blocked packet also lists each uncommitted tracked path.>

Status: `complete` / `blocked`
```

`Seams touched` lists every seam you checked in step 9 of `Common Workflow`, with one line each. Include seams whose other side is unchanged code or an earlier slice. Write `None.` with a brief reason when the round touches no seam, for example a documentation fix or an isolated internal edit. Do not invent entries.

Evidence rules for the packet:

- Record the source and inputs each check actually exercised. Reuse its result for a later commit only after checking that the diff cannot affect its claim or inputs. Explain that comparison; do not describe reused evidence as a new run. Rebuild and rerun affected checks when relevant code, tests, fixtures, dependencies, build settings, or runtime inputs change. Unrelated edits do not require a rerun.
- Match the type of evidence to the claim.
- Record each false-pass check you ran (mutation, bypass, fake) and its result.
- For a conditional or live test, show that it ran rather than skipped.
- Name each command or helper you actually ran, its explicit target, and the services it affected.
- Keep fixed expectations apart from runtime-generated values.
- Say what each important check does not prove.
- Include artifacts, stable test IDs, hashes, and totals only when later review or evidence synthesis can use them.
- Leave out categories that do not apply, long logs, repeated summaries, exhaustive inventories, and output that contains secrets.

Do not write a separate packet to restate accepted evidence.

## Final Check

Before you append the pointer, confirm each item:

- The workitem, task, round, route, branch, source, and commit identities match.
- The packet accurately reports the current implementation, the evidence that applies, and the exact gaps.
- Every planned assertion corrected in this round is listed with its source and affected checks. No separate packet is needed.
- Every runtime claim you ran is covered: every engineer-run runtime claim includes the compact `Runtime evidence` block, with full identity and cleanup detail where they are important.
- Every engineer-owned obligation is complete with current evidence, or names its exact blocker and next owner.
- The working tree has no undisclosed edit from the current round, and it keeps unrelated user work.
- The status satisfies `Completion States`.
