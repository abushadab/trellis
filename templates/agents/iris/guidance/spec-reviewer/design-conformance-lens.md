# Design Conformance Review Lens

## Primary Question

Would implementing the spec as written produce the approved design-authority screens, in the approved states, with the adopted rules, so that a side-by-side comparison with the design authority can accept the result?

## Authority

Your prompt states the design authority's role. Read it only at the pinned version the spec cites, and never edit it.

## Emphasize

- a `Design reference` source with the design authority path, pinned version, and every screen and state in scope, by route or screen id;
- one screen-state acceptance criterion per screen and state the slice delivers, with side-by-side screenshot evidence at a fixed viewport;
- every design-authority rule the spec relies on is cited (rule, row, or ruling ID) and matches the design authority's text at that version;
- states the intent names but the spec silently drops, and states or copy the spec invents that the design authority does not show;
- rules the intent lists as open are left open rather than decided inside the spec;
- redesigned screens are specified to use the components and design tokens the intent names, taken from the pinned version, and a project UI-kit rule must not force a different layout or interaction; and
- no requirement to port mock data, QA switches, prototype-only strings, or hard-coded figures as product behaviour; screens are rebuilt on real data.

## Calibration

A finding needs a concrete divergence from the pinned screen, state, or rule, or a missing reference that would let Ben accept a screen that does not match. Do not flag design-authority-defined layout, copy, or tokens as over-prescription. Do not demand pixel-exact parity where the design authority uses synthetic data; compare structure, states, copy, and tokens. Leave component and data-loading mechanisms to Ben. Raise backend, authorization, or scope issues only when they make a defined state impossible or unsafe.
