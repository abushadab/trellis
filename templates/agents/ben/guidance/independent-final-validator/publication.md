# Independent Final Validator Publication

Read this guide after the run, diagnosis, and cleanup attempt are done.

## Result Pointer

Append only after the validation packet passes `Final Check`:

```md
Validation packet: `{{path:workitems_root}}/<workitem-id>/validations/<slug>-adversarial-validation-r<N>.md`
Status: `not_broken` / `confirmed_defect` / `inconclusive` / `blocked`
Summary: <one sentence result and next route when status is not `not_broken`>
```

## Output Format

Write one immutable packet under `{{path:workitems_root}}/<workitem-id>/validations/`.

`<slug>` is the challenge review file name without `-implementation-review-r<N>.md`, followed by `-<nickname>` when your launch input has a `Nickname:` line. `<N>` is the launch's `Validation Round`. Never overwrite a packet; if the file exists, stop and name it in your final reply.

```md
Validation packet:

Workitem ID:
Task: <Task ID> — <Task Name>
Validation round:
Challenge review:
Implementation packet:
Reviewed commit:
Branch:

## Challenge results

### <Challenge ID> — <short claim>
- Claim:
- Failure hypothesis:
- Fixed expected-result source:
- Probe rationale: (how the probe tells the claim apart from the named defect)
- Runtime preparation and tested source/build identity: (starting HEAD and dirty-state result)
- Fixtures, mutations, controls, and protected targets:
- Invocation and concise result: (exact commands)
- Decisive before/after evidence:
- Cleanup: (including repository status after the run)
- Result: not_broken | confirmed_defect | inconclusive | blocked
- Limits:

## Overall result
- Status: not_broken | confirmed_defect | inconclusive | blocked
- Next route:
```

Pick the overall status in this order:

1. `confirmed_defect`, if any challenge proves a defect.
2. Otherwise `blocked`, if any challenge could not run safely, or any cleanup or protected-target blocker remains.
3. Otherwise `inconclusive`, if any challenge is still undecided.
4. Otherwise `not_broken`.

## Routing

`Next route`: for any status but `not_broken`, name the owner and the smallest next step from `Failure and Routing`.

## Final Check

Before you publish, confirm:

- the workitem, task, round, `challenge_required` review, implementation packet, branch, and reviewed commit all match;
- every assigned challenge has one result, with complete decisive evidence or the exact blocker, from a probe that tests its hypothesis (not a rerun of the engineer's tests) against source-backed expected results;
- every `You must` item under `Runtime and Temporary-File Authority` holds, including repository status after the run;
- no tracked product, test, config, SQL, migration, infrastructure, prompt, or unrelated workspace file changed; and
- the overall status meets its meaning: `confirmed_defect` proves a tracked correction is needed, `inconclusive` does not imply acceptance, `blocked` names the missing safe condition, and `not_broken` is limited to the assigned challenges.
