The design authority is `{{config:design_authority}}`. It is the UI spec, and it is read-only. Never edit it.

- The screens and states the spec names, at the spec's pinned ref, decide layout, flows, states, copy, and visual tokens. For how a screen looks, they override older project UI guidance.
- Redesigned screens use the authority's components and design tokens, ported into the product from the pinned ref. Never port mock data, QA query switches, or text that exists only in the authority; rebuild each screen on real data.
- Accept a UI slice by side-by-side comparison with the authority at the same state, not by "functionality present".
