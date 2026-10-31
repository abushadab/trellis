# General Review Lens

`general` is the default single-reviewer pass. Use it for slices with no lab screen. For lab-defined screens, it does not replace `design_conformance`.

## Primary Question

Is the spec clear enough for Ben to implement without inventing product behavior, safe in the places it touches, and the smallest slice that fully meets the approved outcome?

## Emphasize

Product:

- behavior stated clearly enough that Ben need not invent decisions, with actors, observable states, results, and errors where they matter;
- observable acceptance criteria that tell the intended behavior from other behavior;
- preservation of known current behavior across the changed surface; and
- lab-defined layout, states, copy, and tokens that the spec references by lab screen and state are approved observable contract, not over-prescription. Flag a UI requirement that has no lab screen behind it, or that contradicts the pinned lab screen.

Risk, only where the spec touches it:

- security and identity, tenancy, data, permissions, migrations, and destructive actions; and
- a demonstrated failure timeline, not just a serious-sounding topic.

MVP and scope:

- the narrower option tested, with no premature surfaces that lack necessity evidence;
- the MVP slice kept separate from the later full-feature goal; and
- validation sized to what the change touches, not cumulative recertification. Side-by-side lab and product screenshots for lab screen and state acceptance criteria are the required UI evidence, not a costly journey to challenge.

## Calibration

Prioritize the few highest-impact findings over exhaustive coverage of all three areas.
