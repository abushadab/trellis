- **Wrong implementation:** each AC test names a plausible wrong implementation it must fail on, such as a wrong condition, wrong target, or skipped effect. A test that would also pass on it does not prove the AC.
- **Expected results** come from the source spec or an approved decision, never from implementation output.
- **Negative tests:** where a planned denial could have another cause, a planned control shows that the denial comes from the intended boundary. Do not prescribe where the control runs.
- **Runtime target:** each runtime check names its target: the local development runtime{{if:runtime_guide}} described in `{{config:runtime_guide}}`{{/if}}, or a task-owned disposable target. Each check follows the project's testing guide: `{{path:guidance:ben}}/testing/dev-test-guide.md`.
- **Permanent tests:** use `permanent_regression` only for one of these, when it can realistically regress again:
  - a currently supported behavior;
  - a rule that must always hold for safety;
  - a supported migration, upgrade, recovery, or historical-input path; or
  - a reusable regression boundary.

  The entry names that surviving contract and a durable trigger. Proof that only establishes this implementation at this commit is a `temporary_probe` or `workitem_evidence`, even when it is useful now.
- **Engineer ownership:** the Implementation Engineer owns the planned permanent regressions, revisions to affected tests and helpers, convergence or retirement, fixtures, support helpers, runtime preparation, and first execution. No other role gets these.
- **Stop conditions** may halt work for unclear expected behavior, an architecture or authority change, unsafe stateful work or mutation, product ambiguity, drift in protected state, or a correction outside scope. Inside scope, they must let the Implementation Engineer diagnose and fix a source-proven defect in product code, tests, fixtures, commands, or runtime setup. No separate authoring role is needed.
- **Clean install:** plan a clean dependency install or an uncached dependency layer only when dependency inputs, package-manager configuration, toolchain, base image, or install commands changed, or dependency installation is an assigned risk. Reusing the dependency layer still runs compilation, code generation, workspace-package builds, and application image layers for changed source.
- **Runtime class:** a runtime-affecting slice uses `recreate`, `rebuild`, or, only when isolation is unsafe, `full-stack`.
- **Proof budget:** prove each AC once, with one focused test, plus the slice's integration checks. Never split a slice, or open a new one, just to re-prove behavior that already works. Name any slow end-to-end proof you add distinctly (for example with a `Slow` suffix), so the project's normal test run can leave it out. If the plan's slice count passes about twice the spec's ACs, publish a `blocked` plan that names the decision Ben must make.
- **Deferral** is valid only when the current task cannot safely do the check (for example, a dependency or environment is missing), or a reviewed later integration boundary owns it. A deferral names the command or scenario, the owner, the reason, and the evidence target. Do not defer safe proof for the current slice just because a later slice exists.
