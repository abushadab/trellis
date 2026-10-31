# General Review Lens

`general` is the default single-reviewer pass.{{if:design_authority}} Use it for slices with no design-authority screen. For screens the design authority defines, it does not replace `design_conformance`.{{/if}}

## Primary Question

Is the spec clear enough for Ben to implement without inventing product behavior, safe in the places it touches, and the smallest slice that fully meets the approved outcome?

## Emphasize

Product:

- behavior stated clearly enough that Ben need not invent decisions, with actors, observable states, results, and errors where they matter;
- observable acceptance criteria that tell the intended behavior from other behavior;
- preservation of known current behavior across the changed surface{{if:design_authority}}; and{{else}}.{{/if}}
{{if:design_authority}}
- layout, states, copy, and tokens that the spec references by design-authority screen and state are approved observable contract, not over-prescription. Flag a UI requirement that has no design-authority screen behind it, or that contradicts the pinned screen.
{{/if}}

Risk, only where the spec touches it:

- security and identity, tenancy, data, permissions, migrations, and destructive actions; and
- a demonstrated failure timeline, not just a serious-sounding topic.

MVP and scope:

- the narrower option tested, with no premature surfaces that lack necessity evidence;
- the MVP slice kept separate from the later full-feature goal; and
- validation sized to what the change touches, not cumulative recertification.{{if:design_authority}} Side-by-side design-authority and product screenshots for screen-state acceptance criteria are the required UI evidence, not a costly journey to challenge.{{/if}}

## Calibration

Prioritize the few highest-impact findings over exhaustive coverage of all three areas.
