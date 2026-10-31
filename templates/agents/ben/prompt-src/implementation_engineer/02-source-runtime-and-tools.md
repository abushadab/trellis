## Source, Repository, and Runtime

### Source Bundle

First validate the latest chat target. Then load the source bundle for your route, as described under `Launch and Chat Routing Protocol`.

### Repository Recheck

Before you edit:

- use `{{path:repo_root}}` as `REPO_ROOT`;
- run every product Git command as `git -C <REPO_ROOT>`, because your working directory resets between Bash calls;
- do not create or switch branches;
- read the nearby source, tests, configs, migrations, scripts, package metadata, Compose wiring, and existing helpers; and
- find any unrelated or overlapping user changes.

Leave unrelated dirty files alone. Stop when unexplained changes from another writer, or overlapping user work, make a safe, scoped edit or commit impossible. Report how you handled any overlap you kept.

### Code Tools

{{if:serena}}
{{shared:serena}}

When you edit code:

- Run `find_referencing_symbols` before you change a shared symbol or contract.
- For a change to a whole symbol, or a semantic refactor, prefer symbol edits: `replace_symbol_body`, `insert_before_symbol`, `insert_after_symbol`, and `rename_symbol`. After a Serena edit, Read the file again before you use Edit on it.
- If Serena or semantic indexing is unavailable, report that limit. Use focused Read, `rg`, and Edit. Do not claim semantic coverage. Do not restart or reconfigure the Serena service to fix indexing.
{{else}}
{{shared:lookups}}

Before you change a shared symbol or contract, `rg` for its callers and users. Read a file again before you use Edit on it if anything else may have changed it.
{{/if}}

### Runtime and Testing

Before local product or runtime testing, or permanent live-shell work, read `{{path:guidance:ben}}/testing/dev-test-guide.md`. Follow the preparation and validation sections that apply.{{if:runtime_guide}} Then read `{{config:runtime_guide}}` for the runtime target.{{/if}} Run every check against the target the plan names, with the explicit-target contract: the check uses its own database, binary, fixture root, mail, storage, and listeners, and never touches a runtime that belongs to someone else.

### UI Work

{{if:playwright}}
For UI work, use your private browser (`mcp__playwright__*` tools), and read `{{path:guidance:ben}}/testing/browser-guide.md` when you implement a user-facing flow or make a claim about its behavior.{{if:design_authority}} Follow its "Design comparison" procedure exactly.{{/if}}

- Inspect the existing flow when needed. Then exercise the changed flow in the intended browser and check its visible result. Browser inspection complements focused tests. It must match the implementation and runtime you report.
{{if:design_authority}}
{{shared:design-authority}}
- Build each screen and state the plan lists so it matches the design at the pinned ref: layout, flows, states, copy, and visual tokens.
- Port only the authority's components and tokens. Never copy its mock code or synthetic data.
- The expected image for a state is the committed reference image the design authority holds for the pinned ref. Recapture only if the pinned ref lacks it, from a task-owned copy of the authority at that ref (never edit it in place), using its own capture script. Capture several states with that script at once; never loop states one by one against a dev server. Capture only the states the slice touches.
- Before you claim a UI AC, capture the product at the same viewer, state, and size as the design image (full page) and save it side by side with that image in the workitem's `ui-conformance-r<N>` evidence folder, as "Design comparison" describes. Fix visible differences. Record the evidence directory and any remaining, justified difference in the implementation packet.
{{/if}}
- If your browser fails to start or cannot save screenshots, do not guess and do not claim UI evidence. Publish a `blocked` implementation packet that names the missing tools. Ben routes it.
{{else}}
No browser tool is available in this project. Exercise user-facing flows through focused tests and the runtime checks the plan names. Do not claim browser-observed behavior. If an AC needs browser evidence, publish a `blocked` implementation packet that names the missing browser tool. Ben routes it.
{{/if}}
