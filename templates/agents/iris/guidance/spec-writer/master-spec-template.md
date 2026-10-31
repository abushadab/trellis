# Master Spec Template

A master is a shallow living roadmap for genuinely multi-slice work. It is not a larger single or a checklist of sections.

```md
# <Direction Title>

## Status

- Status: `ready`
- Mode: `master`

## Source References

- [S1] Product authority: `...`
{{if:design_authority}}
- [S2] Design reference (design-authority work): `<design authority path>@<pinned version>`, screens and states `...`
- [S3] Current evidence: `...`
{{else}}
- [S2] Current evidence: `...`
{{/if}}

## Direction

<Approved direction, why now, and any parent product or ownership decision.>

## Current Baseline

<Only present-state facts needed to understand or order the remaining slices.>

## Boundaries

- In: <parent outcome and affected flows>
- Preserve: <essential current behavior>
- Out: <nearest adjacent or later full-feature work>
- Impact: <systems/databases and migrations, roles/processes, or state>
- Complete when: <observable parent outcome>

## Roadmap

| ID | Slice and outcome | Boundary | Impact | Depends on | Status / spec |
| --- | --- | --- | --- | --- | --- |
| R1 | <one independently verifiable outcome> | <in / deferred> | <systems and important surfaces> | - | planned / `...` |

## Risks And Open Decisions

<Only issues that affect routing, order, authority, or safe completion. Omit when none.>
```

Keep roadmap IDs stable once something refers to them. A row names and bounds a slice. It does not design it. Keep completed rows to one line with their accepted spec or verification link. Add another section only for distinct important content that the compact shape cannot state once.
