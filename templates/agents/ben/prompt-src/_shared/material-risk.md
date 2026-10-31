A risk is *material* for this workflow when it can affect any of these:

- persistent data outside the slice's intended target (disposable fixtures that the current task created and owns do not count);
- persistent volumes other than the verified disposable local development database;
- external or shared infrastructure;
- unrelated services;
- public contracts; or
- auth or permission state.

Ordinary scoped local development runtime work is not material by itself: build, recreate, restart, config edit, local database reset, recreate, or schema replacement, migration, and current-task fixtures.

A fixture used across runs, tasks, or agents counts as persistent state only when the active task marks it non-disposable or it belongs outside the verified local development target.

"Material" and "materially" in this prompt mean this threshold.
