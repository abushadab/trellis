# Spec Writing And Review Routing

## Choose The Spec Route

Use a direct `single` by default for one coherent actor-visible capability or outcome.

Use a `master` only when the requested feature has several capability boundaries that can close independently, a required dependency order, or later decisions that need not block the first child. Importance, uncertainty, file count, component count, risk, or possible future growth do not justify a master on their own.

Do not split CRUD, error, or test branches inside one coherent resource lifecycle just because they can be tested separately. Do split independent capability outcomes when one can close safely without the other and they differ in state, authority, lifecycle, dependency, or acceptance boundary.

**Size trigger.** When a `single` is likely to have more than about 6–8 acceptance criteria, or to cross more than 2–3 services or stores, decide before routing whether to split it into a master plus small, complete singles. Splitting is not required. Each single must be a complete behavior whose own public path works end to end. The master owns the invariants that cross its singles. The Spec Writer and Spec Reviewer apply the same trigger to the written spec. The thresholds are starting points, not hard limits.

You select the route. The Assignment Engineer turns it into the Spec Writer assignment, and may return `blocked` if the route cannot be framed without inventing scope.

## Review Set

Use one Spec Reviewer with lens `general` by default. Add a `product`, `risk`, or `overengineering` reviewer only when a product or risk judgment different enough to change the outcome, or real pressure on scope, would improve confidence. These four and `design_conformance` are the only lenses; no other lens name is valid.

Use `design_conformance` for every spec that delivers or changes a lab-defined screen. It checks that the spec carries the pinned lab commit, every lab screen and state in scope, and the adopted lab rules, without drift. `general` does not replace it for lab-defined screens; use `general` for slices with no lab screen.

- For a UI-only slice, `design_conformance` may be the single required reviewer, in place of `general`.
- When the slice also changes behavior or a trust boundary, add a `general` reviewer. Use `product` or `risk` instead when that is the specific judgment you need.

Use `overengineering` when any of these holds. Do not add it to every spec by habit.

- The spec is broad in scope.
- It adds new durable or operational surfaces.
- It spans several independent capability flows.
- Earlier review or revision has accumulated scope.

Do not request checks the Spec Reviewer already runs. Its Counterfactual Before Pass (the smallest-option check) applies to the `general` and `overengineering` lenses, not to `design_conformance`.

A `master-refresh` that only records a completed Ben slice is not a substantive review event; it follows the shortcut in your prompt's "Assignment Review Preflight" section.

A spec moves forward only after every review the route requires has passed and findings that matter are resolved.
