The design authority at `{{config:design_authority}}` is read-only. It is the UI and UX authority, and its product rules are product authority for behavior.

- An approved screen and state at the version the intent pins is direct authority for UI and behavior. So are the design authority's product rules and the owner rulings recorded there. Read it only at the pinned version (for a Git repository, with `git -C <path> show <commit>:<path>`).
- For how a screen looks, they override the project's own UI-kit rules and any earlier intent or spec that conflicts.
- A mock or prototype implementation shows the intended behavior. Port only the components and tokens the intent names. Never port mock data, QA switches, or prototype-only strings; rebuild each screen on real data.
- Uncommitted changes, ideas the intent does not name or lists as open, and rows without a ruling are not authority.
