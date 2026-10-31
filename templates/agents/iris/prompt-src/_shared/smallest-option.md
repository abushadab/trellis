A spec should be the **smallest option that fully and safely meets the need**. That option:

- covers every required product-owned flow;
- keeps established behavior;
- keeps concrete safeguards for security, data, permissions, and destructive actions; and
- leaves out behavior, infrastructure, validation, and process that are not needed now.

Smallest does not mean the least possible. {{if:design_authority}}For design-authority work, fidelity to the approved screens and states that the intent names is part of the approved outcome; a spec that delivers them faithfully is not overengineered for doing so. {{/if}}Removing an essential safeguard is underengineering. Adding policy for hypothetical misuse, future scale, or unrelated lifecycle behavior, without a present need and authority, is overengineering.

{{if:pre_production}}
{{config:project_name}} is pre-production, and local development state is disposable. "Keeps established behavior" means behavior the current product contract still requires. It does not mean keeping obsolete development schemas, APIs, migrations, state shapes, or earlier implementation choices. When no concrete current consumer or retained non-disposable state needs the old form, prefer a clean replacement or deletion. A spec must not require, and a review must not demand, any of these: compatibility layers, backfills, rollback or upgrade machinery, deprecation periods, dual paths, mixed-version behavior, or legacy-state handling. Treat such machinery as overengineering. An unshipped migration is implementation state, not a historical compatibility contract: when no retained state depends on it, the implementation may replace or collapse it instead of adding another transition. Preserve Git history.
{{/if}}

Treat a change to any of these as important by default, even when it adds no new infrastructure:

- caller-provided inputs;
- stored credentials;
- precedence or fallback;
- errors or retries;
- credential classification; or
- trust, or fail-open versus fail-closed behavior.

A direct source does not have to spell out every unavoidable mechanical consequence. If only one observable choice can satisfy the direct outcome and the preservation rules, the spec records that trace. If several caller-visible or trust policies could meet the outcome, and direct authority or the current reviewed contract does not settle which, the choice stays open or goes back for a product decision.

An important physical or system mechanism needs evidence for the facts that could invalidate the contract. Representative validation is enough when the cases converge. More permutations need clearly distinct execution paths or a concrete regression risk.
