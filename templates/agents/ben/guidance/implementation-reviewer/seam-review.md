# Seam Review

A seam is a place where two parts meet. Defects hide there, because each side can look correct on its own.

## Find the seams

List every seam the change creates or touches. Include seams whose other side is unchanged code or code from an earlier slice. Read `{{path:guidance:ben}}/seam-kinds.md` completely; it defines the seven kinds used below.

Start from the packet's `Seams touched` list. Check it against the actual diff and its callers, and add any seam it missed. The author's list alone can miss seams. A missed seam is not a defect by itself; review it like the others.

## Read both sides

For each seam, read the code on both sides in the current source. Read the unchanged side too. A diff of one side is not enough.

## Ask the questions for that kind

Ask these two for every changed safeguard or durable step:

- What must eventually complete or release resources?
- What existing valid flow could this safeguard disrupt?

Then ask the questions for the seam's kind.

**Process or service boundary:**
- Are success, definite refusal, transient error, and unknown outcome handled differently?
- Is a lost response checked against the actual effect before anything is repeated or compensated?

**Durable state:**
- For each phase, what resumes it?
- What ends it when the outcome is definite?
- What does it release?
- What happens if the next step fails after this one committed?
- Are writes that must agree done atomically?

**Shared hold:**
- Who holds it, and for how long?
- Who is blocked meanwhile?
- Can it be held indefinitely, or across a whole request?
- Holding is fine while effects are still uncertain, and some holds legitimately outlive an operation. A hold is a defect only when it violates its progress or release contract. An example is a hold that blocks unrelated work with no path to release.

**Changed shared mechanism:**
- Which existing flows pass through it? Include unchanged lifecycle operations.
- Does each one still work?
- Name one positive check for each flow.

**Caller input:**
- Is it read by one authority everywhere, from validation through dispatch?
- Can it collide with names that existing requests already pass through?
- Does every entry point that should handle it actually handle it?

**Inherited state:**
- What in the copied state can run before the checks?
- Is it neutralized or rejected before then?

**Test expected result:**
- Would the assertion still pass if the boundary were broken?
- Where a denial could have another cause, do the controls distinguish the boundary from the competing causes? The control does not have to be on the same target.
- Does the asserted failure come from this boundary and not from another cause?

## Failing closed is not automatically correct

Cautious behavior is not proof that it was intended. A refusal or hold is a defect when either is true:

- it violates the progress or release contract that applies to it, from the approved behavior or what the outcome requires (for example, a definite refusal that never ends); or
- it breaks an existing valid flow.

Some holds legitimately outlive an operation, and holding while effects are still uncertain is fine. Missing written intent alone is not a defect either.

## Stay in scope

- Review only seams the change creates or touches.
- Report a seam defect only when you can name a concrete trigger. The trigger must cross the seam and cause wrong, stuck, or broken behavior.
- Propose the narrowest fix. Do not propose a new architecture.

## Record coverage

In the packet's `Seams checked` field, give one line for each seam: its kind, the two sides you read (path:line), the questions you asked in one short phrase, and the result.

A seam you do not list counts as not reviewed.

## Integrated seam review

The target is under `Integrated Seam Review Target` in `Launch and Chat Routing Protocol`. Each slice review saw only its own change; this review looks at where the slices meet each other and existing code.

**Scope:** the full `<base commit>..<final commit>` diff, limited to these seams:

- every `Seams touched` entry in the workitem's complete implementation packets, under its `implementations/` directory;
- seams that list missed, found by checking it against the full diff and its callers yourself; and
- cross-slice seams that no single slice owned, such as code from one slice that meets code from another.

**Read:** the source spec, each slice plan, those packets, and the full diff. When a plan has a `Durable steps` section, use it as the expected state machine for durable-state seams.

**Do:** the seam pass in this guide for each seam in scope, then the disprove pass and `Adversarial Challenge Decision`. Read both sides yourself. Do not rely on earlier slice reviews' conclusions.

**Stay bounded:** this is a targeted seam review, not a full re-review. Do not repeat the per-slice correctness and test-credibility passes outside these seams.

**Publish** one of the usual results with the usual publication guide. Name the file `integrated-seam-implementation-review-r<N>.md`. In `Review target`, put the base and final commits under `Submitted commit`, and the `implementations/` directory under `Target implementation packet`.
