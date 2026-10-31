# Single Spec Template

A single is a compact task contract, not a checklist of sections. Start here and add a heading only for distinct important content that would otherwise be unclear.

```md
# <Slice Title>

## Status

- Status: `ready_for_ben` / `ready`
- Mode: `single`

## Source References

- [S1] Product authority: `...`
{{if:design_authority}}
- [S2] Design reference: `<design authority path>@<pinned version>`, screens and states `...`
- [S3] Current evidence: `...`
- [S4] Assignment-only boundary: `...`
{{else}}
- [S2] Current evidence: `...`
- [S3] Assignment-only boundary: `...`
{{/if}}

## Intent

<Two to four sentences: changed outcome, why now, and nearest important boundary.>

## Decisions

<Only fixed choices needed by this slice. Omit when none.>

## Boundaries

- In: <changed behavior and affected flows>
- Preserve: <one reference to essential existing behavior>
- Out: <nearest tempting adjacent behavior>
- Impact: <services/databases and whether migrations, roles/processes, or state change>

## Acceptance

All criteria are blocking unless the ID cell is marked `(non-blocking)`.

| ID | Observable result | Best practical evidence |
| --- | --- | --- |
| AC-1 | When/if `<trigger>`, `<result>` | `<focused evidence>` |
{{if:design_authority}}| AC-2 | Screen `<design screen>` in state `<design state>` matches the design authority at the pinned version: layout, states, copy, and visual tokens | Product screenshot beside the design authority's reference image for that state at the pinned version, same width, full page, same state and viewer |{{/if}}

## Open Questions

<Only unresolved decisions safe to review. Omit when none.>
```

Include the assignment-only row only when it adds a boundary that no stronger source shows.

Status, source traceability, intent, boundaries and impact, and acceptance are required content. You may merge headings when they stay easy to find.

{{if:design_authority}}
For design-authority work, these are also required:

- the design reference row; and
- one screen-state criterion for each design-authority screen and state the slice delivers (several states of one screen may share a row when they share evidence).

Omit the design reference row and the screen-state criteria for slices with no UI.
{{/if}}

Use `When`/`If ... must ...` wording or Given/When/Then only when it makes the criterion clearer. The writing guide says what counts as one criterion.

Keep evidence beside its criterion. Add a separate section for context, data and trust, edge cases, validation, or risks only when it holds distinct important content that nothing else states.
