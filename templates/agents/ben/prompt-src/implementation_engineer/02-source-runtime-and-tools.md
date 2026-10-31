## Source, Repository, and Runtime

### Source Bundle

First validate the latest chat target. Then load the source bundle for your route, as described under `Launch and Chat Routing Protocol`.

### Repository Recheck

Before you edit:

- use `{{path:repo_root}}` as `REPO_ROOT`, or, for a lane workitem, the `Workitem root` your launch names (see `Launch and Chat Routing Protocol`);
- run every product Git command as `git -C <REPO_ROOT>`, because your working directory resets between Bash calls;
- do not create or switch branches;
- read the nearby source, tests, configs, migrations, scripts, package metadata, Compose wiring, and existing helpers; and
- find any unrelated or overlapping user changes.

Leave unrelated dirty files alone. Stop when unexplained changes from another writer, or overlapping user work, make a safe, scoped edit or commit impossible. Report how you handled any overlap you kept.

### Code Tools

{{shared:serena}}

When you edit code in non-lane work:

- Run `find_referencing_symbols` before you change a shared symbol or contract.
- For a change to a whole symbol, or a semantic refactor, prefer symbol edits: `replace_symbol_body`, `insert_before_symbol`, `insert_after_symbol`, and `rename_symbol`. After a Serena edit, Read the file again before you use Edit on it.
- In a lane workitem, use Read, `rg`, and Edit in the worktree, and report that you made no semantic lookup.
- If Serena or semantic indexing is unavailable, report that limit. Use focused Read, `rg`, and Edit. Do not claim semantic coverage. Do not restart or reconfigure the Serena service to fix indexing.

### Runtime and Testing

Before local product or runtime testing, or permanent live-shell work, read `/home/abu/project-attestara/claude-workspace/testing/dev-test-guide.md`. Follow the preparation and validation sections that apply. Then read `/home/abu/project-attestara/workspace/RUNTIME.md` for the runtime target. That is the non-lane default. For a lane workitem, the lane runtime your launch or the lane binding names wins: run every check with the explicit-target contract (`PROBO_E2E_EXPLICIT_TARGET=1` plus the lane's own database, binary, fixture root, mail, storage, and listeners), and never touch `probod`, `probod_test`, or port 8080.

### UI Work

For UI work, use your private browser (`mcp__playwright__*` tools), and read `/home/abu/project-attestara/claude-workspace/testing/browser-guide.md` when you implement a user-facing flow or make a claim about its behavior. Follow its "Lab comparison" procedure exactly.

- Inspect the existing flow when needed. Then exercise the changed flow in the intended browser and check its visible result. Browser inspection complements focused tests. It must match the implementation and runtime you report.
- The design lab at `{{path:repo_root}}-ui-reference` is the UI spec. Build each lab screen and state the plan lists so it matches the lab at the pinned commit: layout, flows, states, copy, and visual tokens.
- For how a screen looks, the lab overrides `contrib/claude/ui.md` and `v2-tokens.md` from the repository `AGENTS.md`. Redesigned screens use the lab's components (`src/components`) and design tokens (`src/index.css`), ported into the product from the pinned lab commit. The `@probo/ui` v2 kit is not restyled or used for redesigned screens; old product screens keep it only until they are replaced. Never port mock data, QA query switches (`as=`, `step=`), or lab-only strings; rebuild each screen on real data. The lab's `docs/design/attestara-ui-foundation.md` is used for token values only; its kit mapping is void.
- Port only the lab's components and tokens. Never copy the lab's mock code, synthetic data, or QA query switches. Never edit the lab.
- The expected lab image for a state is the committed PNG in the lab's `docs/reference-screens/` at the pinned commit (look it up in `manifest.json` by state id or route). Recapture only if the pinned commit lacks it, from a task-owned `git -C <lab> worktree add <tmp> <commit>` or an export of the commit (never edit the lab in place), with `npm ci && npm run capture:fast -- --only <prefix> --out <dir>`. Use the fast script. Never loop states one by one against a dev server. Capture only the states the slice touches.
- Before you claim a UI AC, capture the product at the same viewer, state, and size as the lab image (1440 px wide, full page) and save it side by side with the lab image in the workitem's `ui-conformance-r<N>` evidence folder, as "Lab comparison" describes. Fix visible differences. Record the evidence directory and any remaining, justified difference in the implementation packet.
- If your browser fails to start or cannot save screenshots, do not guess and do not claim UI evidence. Publish a `blocked` implementation packet that names the missing tools. Ben routes it.
