# Spec Source References

Write a `Source References` registry. Cite it wherever an important claim depends on current behavior, a public contract, a data or trust constraint, a migration, a prior decision, or an important contradiction.

- Use sequential IDs `[S1]`, `[S2]`, and so on. There is no quota or minimum. Include only sources that support an important claim in this artifact.
- Start with the strongest direct product authority, then current implementation or decision evidence. The assignment is routing information already. Cite it only when an assigned boundary that matters is not shown by a stronger source.
- Citing the assignment shows routing and assigned scope only, not product authority.
- Define each ID once, as one coherent source or one tightly linked evidence bundle. Do not reuse an ID for unrelated evidence.
- In a single revision, keep IDs that are still used where practical, add the decisive new evidence, and remove unused sources.
- In a living-master refresh, rebuild the registry around the current direction and roadmap state. Drop superseded round assignments and reviews. Link completed rows to their accepted spec or verification instead of keeping a revision ledger.
- Prefer direct assigned or repository sources over summaries.
{{if:design_authority}}
- For design-authority work, register a `Design reference` source: the design authority path, the pinned version, and the screens and states it covers, by route or screen id. Register the design authority's product rules and recorded rulings that you use as product authority, by rule number, row, or ruling ID. Cite both at the criteria they govern.
{{/if}}
- Put an ID at the nearest important claim, section, or table row. Do not cite every obvious sentence or write prose crowded with source references.
