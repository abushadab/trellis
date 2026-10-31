## Lessons from confirmed implementation reviews

Apply a lesson only when your work touches that boundary; lessons do not widen scope. More are in `boundary-checks.md` (see `Conditional boundary checks`).

- **Complete a correction across all paths.** Trace the rule through every return, variant, and replay or recovery path that applies. Run the same counterexample on each path before you call it fixed.
- **Make cleanup observable.**
  - Before you create anything, list the exact containers, storage, networks, and paths this run owns.
  - Count volumes the image declares, using the existing fixture contract.
  - Create fixtures inside setup that really runs, so a skipped suite creates none.
  - Attempt all owned cleanup. Then check absence separately. Container absence alone does not prove storage cleanup. A failed query is uncertainty and must fail validation.
  - Force an assertion or inspection failure. Check that gates, checked-out clients, and pending operations settle before teardown. Keep the failure visible.
  - Never prune resources when you cannot prove you own them.
