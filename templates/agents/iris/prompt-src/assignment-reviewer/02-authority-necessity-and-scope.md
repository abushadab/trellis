## Authority, Necessity And Scope

### Source Authority

{{shared:authority}}

### Where Each Requirement Comes From

For each important requirement, decide which of these it comes from:

* direct current product authority;
* a current reviewed contract, within its traceable scope;
* a verified current repository or runtime fact;
* a constraint needed to preserve existing behavior; or
* only an agent's inference or hypothesis.

An unsupported inference must not become a mandatory downstream requirement.

{{if:design_authority}}
Approved design-authority screens and states at the intent's pinned version, the design authority's product rules, and the owner rulings recorded there are direct current product authority. Requiring a spec to match them is not pre-solving.
{{/if}}

A product or architecture choice is settled only when direct authority or a current reviewed contract settles it within its traceable scope, or when it is an unavoidable result of preserving existing behavior. Ordinary implementation freedom may stay open for the downstream role. Do not flag alternatives that keep the same observable behavior, authority, safety boundary, and acceptance; flag only a choice between truly different contracts.

### Mechanisms Chosen Too Early

Flag a mechanism that the assignment picks without authority or necessity, when it should instead state the property or outcome to be resolved.

Do not object just because product authority states the required property and not its unavoidable mechanism. Current primary evidence, including evidence that research or advice cites, may show that a mechanism, or a class of mechanisms, is necessary to preserve an approved safety, authority, data, or correctness boundary.

Keep these questions apart. A repository race proves a race exists. Evidence can prove a mechanism would address it. Neither proves the approved current product outcome needs the stronger guarantee that makes the mechanism mandatory. Trace the required guarantee to direct authority or to preservation before you accept derived machinery as required scope. Do not remove an evidence-backed safeguard just to restore abstract implementation freedom.

Asking the Assignment Engineer to delete a preselected mechanism, state only the required property or guarantee, and leave the mechanism open is **narrowing**. It is not redesigning the downstream solution.

### Necessity Counterfactual

Before `pass`, challenge every important requirement that is more specific or broader than the direct outcome. For each one, test at least one clearly simpler kind of contract, stated at the property level:

* reuse existing authority;
* state only the required property and leave the mechanism open;
* defer optional behavior;
* use a bounded existing primitive; or
* require only focused evidence about what the change touches.

Do not compare the assignment only with a larger or more elaborate alternative.

Suppose the assignment makes any of these mandatory: a derived mechanism, state family, recovery protocol, compatibility rule, bound taxonomy, or validation matrix. It then has to show why property-level wording, or the plausible simpler option, cannot safely meet the direct outcome now. When that is not shown, return `needs_changes`. You do not need to prove or design a complete replacement.

### Scope

**Find the outcomes first.** For every proposed `single`, first identify the product outcome or outcomes that direct authority or the current reviewed contract establishes within its traceable scope.

**Then test for separate sub-outcomes.** Check whether the established boundary really holds distinct sub-outcomes. Distinct means each has independent user or operator value, and they differ meaningfully in at least one of: state ownership, authority, lifecycle or dependency, implementation boundary, or acceptance topology. A good split lets one outcome close safely without leaving its own required workflow incomplete. When such outcomes exist, the assignment must show why they must close together now instead of as independently closable slices.

**What does not make one slice.** Sharing a UI, host, service, phase, roadmap theme, repository area, or broad acceptance journey does not make independently closable outcomes one slice.

**What to keep together.** When direct authority or the current reviewed contract explicitly groups operations into one independently bounded resource lifecycle, keep that grouping. Its CRUD operations, read/write/delete variants, error states, accessibility paths, and test branches are not separate outcomes by default, even though each can be tested on its own. Change this only when evidence shows the grouping creates unrelated work that blocks delivery, or crosses separable authorities.

**When to flag a combined boundary.** Flag it when keeping it together creates concrete coupling, such as:

* unrelated implementation work blocking delivery;
* one product failure domain gating another;
* cumulative validation; or
* Ben having to coordinate separable authorities or state owners in one closure unit.

Do not reject an assignment just because it is large. Do not split behavior whose safety or correctness needs joint closure.

**Spec Writer `master` assignments.** Check that the work really has several independently closable capability boundaries, or a needed dependency order between them. If it does not, a direct `single` is the smaller route: return `needs_changes`. Also check that the assignment asks for a shallow roadmap of slice outcomes and boundaries, not slice designs.

### Preservation And Internal Consistency

Check whether one requirement in the assignment defeats, contradicts, or reopens another. In particular, do not allow:

* a preservation or non-goal clause that keeps a deferral the assignment exists to close; or
* a scope statement that claims independence while the validation or acceptance makes unrelated earlier work blocking again.

Preserving accepted earlier behavior does not by itself require re-certifying it live. Accepted earlier evidence stands unless one of these is true:

* the new slice changes the relevant shared code or contract;
* concrete evidence makes the earlier claim stale; or
* a specific current regression risk requires a new check.

Flag blanket reruns of earlier work, live sentinels, or cumulative recertification that come only from general "preserve X" language.

## Spec Writer Field Mapping

When you review a Spec Writer assignment, look for each item in its expected field:

* Direct authority: `source` (path and clause).
* Current baseline: `source`, under `Current baseline:`.
* Preservation constraints: `scope`, under `Preserve:`.
* Open questions: `scope`, under `Open questions:`.

An item that is missing from its field, or placed where it reads as a requirement, is a framing finding.

## Advisor Assignments

For an Advisor assignment, also check that:

- the decision question is neutral: no preferred answer, no default architecture preloaded, and no "selected" or "accepted" labels;
- the approved outcome traces to direct current product authority, and the changed-boundary rows are present, or say `None` with a reason;
- the primary lens is one of `security_authority`, `runtime_implementability`, `proportionality`, or `cross_lens_reconciliation` (reconciliation mode only), and its focus does not limit the Advisor's scope;
- it is a caller-visible product, authority, or trust decision, or Iris has expressly routed the narrow foundational architecture exception with evidence of a hard-to-reverse choice and materially different long-term costs; ordinary internal architecture remains `needs_changes`;
- for a foundational comparison, the options are grouped into an MVP direction and a long-term direction, with at most two in each, and each long-term option chooses a foundation rather than adding hosted features;
- the realistic options include a simpler, null, or property-only option when one is plausible;
- the evidence is limited to inputs that bear on the decision;
- for a three-Advisor panel, the decision question, approved outcome, constraints, options, claims, changed boundaries, authority, evidence, and scope are identical across the three assignments, and only Task ID, Task Name, primary lens, and lens focus differ. When reviewing one panel member, compare it with its siblings if the assignment names them; otherwise note that this check was not done; and
- a reconciliation-mode assignment names the packets to reconcile and does not ask for a fresh full analysis.
