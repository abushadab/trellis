# Implementation Review

## Files to Read

Read:

- the target implementation packet;
- its ready detailed plan or focused repair assignment;
- the authoritative source spec, brief, and explicit user or Iris decisions the packet names;
- the submitted commit and every changed file;
- for a correction, the prior implementation and the review, validation, or investigation result that triggered it; and
- only the prior-slice, preservation, runtime, or accepted-evidence artifacts that the active contract or the reachable changed behavior needs.

## Pass A — Implementation Correctness

Confirm that:

- every required active behavior is implemented, and no future-slice behavior or extra process machinery was added without authority;
- the source's public API, SDK, MCP, environment, persistence, deletion, and deployment contracts are preserved;
- input, authority, data identity, permission, transaction, concurrency, replay, migration, cleanup, and failure paths are correct when touched;
- shared callers, imports, registration, config, generated outputs, and existing branches still work;
- the actual configured runtime path is represented, not only a parser, mock, direct database shortcut, or unbuilt source path;
- implementation choices the source leaves open follow current repository contracts, and are matched to the approved company self-hosted product; and
- every disclosed changed file belongs to the authorized slice or correction.

These are findings: missing required behavior, an unauthorized behavior change, unsafe runtime or data handling, and a reachable regression.

## Pass B — Test and Evidence Credibility

Apply `Test Credibility` to the areas listed at its top. It covers runtime freshness, recorded identity, and cleanup. Also confirm that:

- every required permanent test is in the Implementation Engineer deliverable, not deferred to another authoring role;
- cleanup is bounded and does not hide a primary failure; and
- the validation obligations, test entry points, fixed expected results, and runtime and fixture boundaries are enough to reproduce the result.

These are findings when they undermine confidence in the changed behavior: a missing required test, a test that passes on wrong behavior, a stale runtime, a source/image mismatch, and unsafe cleanup.
