# Validation and Runtime Contract

## Expected-Result Hierarchy

The approved source and explicit user or Iris decisions set the expected behavior. For behavior they leave unchanged, use reviewed repository contracts. The plan supplies the remaining implementation and test details; it cannot override required preservation. Observed output alone never sets the expected result.

Let the engineer correct a mistaken planned assertion when the source clearly settles it, or a reviewed repository contract settles behavior the source leaves unchanged. Require a short explanation and evidence in the implementation packet. Route a conflict only when the expected behavior, scope, authority, or safety remains unresolved.

## Local Runtime Authority

The local development runtime and task-owned local fixtures have standing authority for rebuilds, recreates, destructive resets, and creating or deleting volumes. Do not extend that authority to production, external or shared systems, or valuable data that does not belong to the task.

Before you approve a development deployment or migration that may change existing data in a database that the active task has not marked disposable, require a backup of that database first. Keep dumps outside every Git repository, and never commit them.

For runtime targets, read {{if:runtime_guide}}`{{config:runtime_guide}}` and {{/if}}`{{path:guidance:ben}}/testing/dev-test-guide.md`.

## Review and Validation Rules

- Before you route on a result packet, check the cause it demonstrates. Its status label alone is not authority.
- Review the exact submitted commit. Keep each test or runtime result tied to the source and inputs it actually exercised.
- Reuse an earlier result when the later diff cannot affect its claim or inputs. Record what changed and why the result still applies. Relevant inputs include code, tests, fixtures, dependencies, build settings, runtime configuration, and services.
- Rebuild or rerun only what a relevant change invalidates. An unrelated edit or a new commit ID alone does not invalidate evidence. If applicability is unclear, inspect the changed inputs or run the affected check.
