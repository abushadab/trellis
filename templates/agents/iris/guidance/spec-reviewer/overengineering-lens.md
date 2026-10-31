# MVP Scope And Overengineering Review Lens

## Primary Question

Is this the smallest complete, safe current slice, with the smallest evidence that can settle it? Or has unrelated scope, mechanism, or validation been made blocking?

## Emphasize

- find the direct or current-reviewed product outcomes before you split anything. Split distinct, independently valuable outcomes, not CRUD operations or test branches inside one grouped resource lifecycle;
- challenge new infrastructure, state, processes, roles, compatibility machinery, hot-path gates, or later-goal work that lacks necessity evidence;
- separate evidence-backed safety mechanisms from speculative hardening;
- reject cumulative predecessor recertification when accepted evidence still stands and no changed boundary or concrete risk that the evidence is stale requires it;
- challenge exact-build or browser journeys, fault matrices, topology proof, broad scans, and other costly validation when a narrower proof tells the cases apart (side-by-side lab and product screenshots for the screen-state acceptance criteria are the required UI evidence, not a costly journey to challenge); and
- compare broad requirements with simpler complete classes, such as reuse, defer, bounded downtime or an offline transition, restart or recreate, or validation focused on what the change touches, when these fit the approved guarantees.

## Before Pass

Do the Counterfactual Before Pass from your prompt. Examples of simpler contract classes to test against: reusing existing authority, stating the property and leaving the mechanism open, aggregate rather than per-family bounds, deferring or omitting optional behavior, a bounded operator-mediated transition, or focused evidence on what the change touches.

## Calibration

Do not fragment one coherent resource lifecycle. Do not require a hypothetical alternative to be complete before you reject unsupported breadth. Do not redesign security or runtime architecture just to make the slice smaller; challenge its necessity and its blocking effect instead.
