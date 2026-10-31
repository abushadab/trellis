# Test Credibility

Use this guide for every created, substantially changed, or directly superseded unit, integration, migration, permission, concurrency, regression, fixture, support-helper, live-shell, and runtime-evidence area in the submitted implementation.

Apply only the checks that fit the changed risk. Do not ask for a broad test matrix or extra artifact just because a category exists below.

## Expected Results and Claim Fidelity

- Use the approved source and explicit user or Iris decisions first. For behavior the source leaves unchanged, use reviewed repository contracts. The plan or repair supplies remaining details and cannot override required preservation.
- Check each `Planned-assertion corrections` entry against that order. Compare the old and new expectations with the cited source and affected checks. A justified correction is not a defect merely because it differs from the plan. Reject a correction based only on observed output or one that accepts outcomes the higher-priority contract forbids. If the diff changes a planned assertion that the packet does not list, inspect and classify it under these same rules.
- Runtime output supplies only dynamic values such as generated IDs, keys, and timestamps. Observed success does not define the expected behavior.
- Assertions are exact enough to reject plausible wrong outcomes, conditions, argument mappings, actors, parents, types, versions, roles, or state transitions.
- Where required, the test asserts the returned results and the relevant before/after state, denial, non-mutation, or cleanup effects.

## False-Pass Resistance

- A required failure cannot turn into a warning, skip, accepted alternative, swallowed pipeline failure, fallback success, loose matcher, or success counter.
- Conditional tests demonstrably run in the recorded run.
- When useful, check that the evidence for a new or substantially changed high-risk assertion includes a focused mutation, bypass probe, temporary fake, or deterministic counterexample showing that it fails on wrong behavior.
- Mocks, substitute services, and direct database checks do not bypass the boundary the test claims to prove.

## Coverage and Setup

- The submitted artifact matches the plan's `Test/evidence disposition`. A permanent regression protects a surviving current or supported historical contract. Temporary or workitem proof is not promoted to tracked source without authority.
- Directly superseded tests and helpers are kept, revised or converged, or retired for a source-backed reason, not kept only so the history stays green.
- A new or substantially changed permanent live test matches the plan's `Harness choice` and `Support choice`.
- The happy, negative, denial, non-mutation, preservation, concurrency, retry, replay, failure, and deletion cases that the changed behavior needs are present.
- Test setup creates prerequisites. It does not pre-seed the product behavior or state credited to the implementation.
- Fixtures represent valid and invalid states that the real workflow can reach.
- The change does not add unnecessary per-slice wrappers or duplicate preflight, Docker lifecycle, cleanup, artifact parsing, checksum, or reporting machinery.
- When practical, prefer durable proof in this order:
  1. behavioral tests, or permanent tests of a rule that must always hold;
  2. symbol or call-site checks, or AST/context allowlists;
  3. forbidden-reference checks scoped to production code;
  4. occurrence counts; and
  5. exact line/column inventories, only when no simpler structural proof establishes the boundary.

## Runtime and Source Freshness

Read `/home/abu/project-attestara/claude-workspace/testing/dev-test-guide.md` when you review permanent live-shell work or runtime preparation.

- The test targets the intended `local Probo development runtime` stack, project, database, service, role, proxy, pool, startup, Compose, or built entry point.
- Runtime preparation covers every changed image input, bundled library, migration, configuration, environment, generated output, Compose file, and affected service.
- When freshness matters, the recorded image and container identity is useful and consistent.
- Each result identifies the source and inputs used for that check. For reused evidence, inspect the later diff and confirm it cannot affect the claim or its code, tests, fixtures, dependencies, build settings, or runtime inputs. Require affected rebuilds and reruns when those inputs change. Unrelated edits or a new commit ID alone do not require re-execution.

## Live Shell Tests

For a new or substantially revised permanent shell test, confirm that it:

- has the durable execution trigger or home the plan requires;
- still runs after the temporary `work/<workitem-id>` branch is squashed and deleted, with no hard-coded equality to that branch;
- honors explicit runtime targeting (`PROBO_E2E_EXPLICIT_TARGET=1` plus its own database, binary, mail, storage, and listeners), as `contrib/testing/test-evidence-flow.sh` does;
- uses durable source and runtime identity, or protected-target checks, where freshness or safety needs them;
- deliberately captures expected non-zero commands; and
- keeps sensitive values out of printed output that a review may quote.
