# Design Conformance Review Lens

## Primary Question

Would implementing the spec as written produce the approved lab screens, in the approved states, with the adopted lab rules, so that a side-by-side comparison with the lab can accept the result?

## Authority

Your prompt states the design lab's authority. Read the lab only at the pinned commit the spec cites (`git -C <lab> show <commit>:<path>`), and never edit it.

## Emphasize

- a `Design reference` source with the lab path, pinned commit, and every screen and state in scope, by route;
- one screen-state acceptance criterion per lab screen and state the slice delivers, with side-by-side screenshot evidence at the fixed viewport;
- every lab rule the spec relies on is cited (`plans/product-rules.md` rule, `plans/evidence-flow-states.md` row, decision-sheet ruling) and matches the lab text at that commit;
- states the intent names but the spec silently drops, and states or copy the spec invents that the lab does not show;
- lab rules the intent lists as open are left open rather than decided inside the spec;
- redesigned screens are specified to use the lab's components (`src/components`) and design tokens (`src/index.css`) ported from the pinned commit, not the restyled `@probo/ui` v2 kit (old screens keep the kit only until replaced), and a kit rule must not force a different layout or interaction; and
- no requirement to port the lab's mock data, QA query switches, lab-only strings, or hard-coded figures as product behaviour; screens are rebuilt on real data.

## Calibration

A finding needs a concrete divergence from the pinned lab screen, state, or rule, or a missing reference that would let Ben accept a screen that does not match. Do not flag lab-defined layout, copy, or tokens as over-prescription. Do not demand pixel-exact parity where the lab uses synthetic data; compare structure, states, copy, and tokens. Leave component and data-loading mechanisms to Ben. Raise backend, authorization, or scope issues only when they make a lab state impossible or unsafe.
