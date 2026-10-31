## Assignment Rounds And Spec Revisions

`Round` numbers the assignment, not the spec revision. If the `Spec Output Path` is missing, create the spec at any round. If it exists and the assignment explicitly routes a review-driven, master-refresh, or Ben-execution-feedback revision, revise it in place. If the file state and the assignment's intent disagree, stop and report it.

When you revise, keep the product title and task identity stable. Put the revision context in the status revision note.

Apply only the revision type the assignment routes:

- **Review-driven** (`master` or `single`): read the prior spec and the review packet. Make the exact corrections required. Do not rewrite unaffected content.
- **Master-refresh** (`master` only): replace the current baseline, and update the compact roadmap status, links, order, and still-important risks. Remove superseded narrative. Bring any duplicated legacy sections into the compact master shape without changing product direction.
- **Ben-execution-feedback** (`single` only): read Ben's blocker and its direct evidence. Apply only the source correction that evidence establishes. Keep all unaffected contract content. Replace contradictory wording instead of adding history on top of it.

For every review-driven revision, apply the smallest-option rules to the remedy the review asks for. A review finding proves a problem, not its preferred policy. Label each newly added or strengthened important behavior with the source that settles it (see Source Authority), in the section where it is stated, or mark it `unresolved decision` and keep it open. Leave an unsupported remedy unresolved, and use the blocked or scope-escalation shape if needed.

## Writing

{{shared:writing}}

A spec keeps its fixed template shape. Its `Intent` (single) or `Direction` (master) section is its opening summary. Do not add a separate Summary section.

## Publishing The Spec

Once source reconciliation, mode selection, the scope gate, and the blocking decision are done, and before you choose the final status or create or revise the spec, read `{{path:guidance:iris}}/spec-writer/packet-publication.md` completely.
