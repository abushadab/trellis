A ready spec makes its real size and what it touches visible in plain language, without a required matrix.

- A `single` normally uses one short `Impact` line: the changed behavior and flows, the services and databases crossed, and whether migrations, roles, processes, or stored or in-memory state (and its lifecycle) change. Expand a category only if it is non-empty, hides breadth, or affects safety, authority, order, or acceptance. Name several implementation slices only if the work truly has them.
- A `master` gives the same information at roadmap depth for each immediate and next slice, with the observable acceptance boundary and what stays out.

No row or paragraph should exist just to say `none`; one sentence may say that no migration, role, process, or runtime state is added. Compactness must not hide a surface that cannot be justified. Such a surface is removed or deferred.

### Size Trigger

A `single` with more than about 6–8 acceptance criteria, or one that crosses more than 2–3 services or stores, needs a decomposition decision. The thresholds are starting points, not hard limits. The spec either records in `Impact` a reason that holds up for staying one single, or narrows its scope, or proposes a master that owns the cross-spec invariants plus small singles.

Splitting is not required. Each proposed single must be a complete behavior whose own public path works end to end. A piece that nothing calls until a later slice cannot be reviewed end to end.

### Caller Inputs And Shared Mechanisms

- Each new or changed caller-visible input (query key, header, path segment, or body field) is listed, with how it must not collide with names that existing requests already pass through. Stating this is not caller-input policing. If authority does not settle the name or the collision rule, it stays an open decision.
- For each changed shared mechanism the spec relies on (for example a token hook, identity record, parser, or spawn path), `Preserve:` names the existing main flows that pass through it, including unchanged lifecycle operations.

### Evidence A New Surface Is Needed Now

Every proposed database or store, migration, API or read path, role or grant boundary, process, or persistent or in-memory runtime state needs **necessity evidence**:

- the current-slice behavior that needs it;
- the current producer;
- the current consumer;
- the current acceptance criterion; and
- the concrete correctness or safety failure if it waits.

Only proposed categories need entries. Every field that applies must be covered; an inapplicable field may be stated when that keeps the trace clear. A surface without this evidence is premature future infrastructure and is removed or deferred.

The one exception is a `user-approved foundation exception`: direct product authority explicitly requires that exact broader surface, even though the usual producer and consumer evidence is missing, and the user approved it after its size and tradeoff were visible. Keep the label as written. The spec cites that exact authority, keeps the surface to the stated boundary, and does not pretend ordinary necessity evidence exists. Calling the work a prerequisite, foundation, connection point, changed boundary, or later-use contract does not create that authority. The exception covers only that exact recorded surface, not adjacent behavior.

A capability the owner has ruled in scope counts as direct product authority for current-slice behavior: a recorded ruling{{if:product_doc}} in `{{config:product_doc}}`{{/if}}{{if:design_authority}}, or an approved design-authority screen, state, or product rule that the intent names{{/if}}. Its producer and consumer may be the approved screen and the user action it shows, so it needs no separate workflow proof. Ideas the intent does not name, or lists as open, still need the usual necessity evidence.

### Broad Work

Work is **broad** when it:

- creates a horizontal platform substrate;
- noticeably expands product behavior, trust, data, permissions, safety posture, or architecture;
- inspects infrastructure or the control plane on every ordinary request (for example physical container, cgroup, network, or service inspection); or
- involves release, upgrade, predecessor-drain, or compatibility orchestration.

The last two count as broad by default, even when they reuse existing code and add no durable surface. For them, the spec also shows why simpler behavior cannot safely complete the direct current outcome: necessity evidence, and a comparison with bounded downtime, offline, restart, or deferral options where those could keep the approved guarantees.

For any broad work, the spec shows the narrower MVP option and its tradeoff. Phases, components, headings, or internal splits do not make broad work narrow.

The first two kinds carry one more gate. If the narrow option cannot meet required behavior or safety, so the broader boundary is required, the spec is ready only when the evidence traces a direct user decision for that broader boundary, made after its scope and tradeoff were visible. Agent recommendations are not that decision. If the narrow option does meet the need, the narrow spec is the right one.

A master-roadmap theme may stay broad as a directional map. It must not be routed as one Ben-ready `single` when its real boundary spans several product behaviors, systems, or independently verifiable slices.

Having no new service, database, migration, role, process, runtime state, or public option does not prove the work is narrow. Count the important-by-default changes from the smallest-option rules when you assess behavior and affected flows.

### Current Slice And Later Goal

The MVP slice and the later full-feature goal stay separate. The later goal belongs in roadmap or dependency context. It does not become current acceptance or implementation scope without concrete present need and authority.

A narrow scope may defer surfaces, lifecycle paths, or coverage it does not ship. Everything it ships must still be complete, with no throwaway behavior, and keep the essential guarantees for security and identity, tenancy and sessions, data and permissions, migrations, and destructive actions. {{if:pre_production}}Speculative production rollout, compatibility, retention, high availability, or extra process isolation is not required.{{/if}}
