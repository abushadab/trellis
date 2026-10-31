# Adversarial Challenge Failure and Routing

Read this guide on your first red check, ambiguous or unsafe probe result, runtime mismatch, or unavailable required input.

## Diagnose Without Weakening

First decide which it is:

- a proven defect in the product or a permanent test;
- an invalid probe, or one that cannot tell the claim from the defect;
- a problem with the temporary task-owned runtime or fixtures;
- a missing dependency, permission, environment, or safety condition; or
- a cause that is still unclear.

Use focused logs, source reads, before/after state, and one bounded control rerun when useful. Do not weaken the probe or expected result (see `Expected Results`), skip a required branch, or change valuable state to get a result.

## `confirmed_defect`

Publish when you have a reproducible counterexample showing the hypothesized defect, or another directly related defect, in tracked implementation or a false-pass permanent test. Then:

- state the exact claim and counterexample;
- name the tracked implementation or permanent-test boundary that needs correcting;
- keep the safe decisive evidence; and
- name the review, test, and runtime evidence it affects.

Do not repair tracked files.

## `inconclusive`

Publish when the probe ran or partly ran but cannot tell correct behavior from the hypothesis, or when the cause is still unclear after bounded diagnosis.

State the smallest reproducible experiment, what you observed, the competing explanations, and the next fact to find out.

## `blocked`

Publish when safe execution or cleanup needs authority, a dependency, an environment, external input, or a change outside the review's allowed boundary, and it is not available.

State the exact missing condition, any retained task-owned resources, and their cleanup owner. Do not switch to a broader, more destructive, or off-target runtime.

## No-Edit Correction

You may fix task-local probe mechanics, temporary scripts, disposable fixtures, quoting, paths, timeouts, or cleanup. The fix must stay inside the same challenge block and touch no tracked file. Record the correction and rerun only the affected probes.
