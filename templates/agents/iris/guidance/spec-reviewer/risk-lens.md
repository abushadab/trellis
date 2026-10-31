# Risk Review Lens

## Primary Question

Could implementing the spec as written break an approved security, authority, data, destructive-action, migration, preservation, or lifecycle guarantee on a realistic current-slice failure path?

## Emphasize

- caller identity, authorization that checks what the request actually does (not only that the caller is signed in), canonical state ownership, credential and secret custody, aliases, and leftover authority;
- destructive actions, migrations, data loss or corruption, effects across projects or principals, replay and duplication, concurrency and supersession, and timeout and lost-response boundaries;
- finality and no-late-effect claims, only when the finality check's trigger applies;
- preservation of accepted trust, data, and runtime guarantees where the change touches them; and
- whether evidence proves a concrete failure, not just a serious-sounding topic.

## Calibration

Prefer a demonstrated failure timeline over generic hardening. Do not demand new stores, tokens, isolation layers, topology inspection, exhaustive fault matrices, or stronger availability just because they could reduce uncertainty. Name the violated guarantee or the missing authority or evidence.
