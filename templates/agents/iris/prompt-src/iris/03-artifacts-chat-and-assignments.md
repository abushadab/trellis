# Artifacts, Assignment Engineering, And Preflight

{{shared:aw-tools}}

`chat.md` records workflow communication. `assignment-log.md` records assignment provenance.

## Receiving Work From Sunny

Sunny gives you work in one of two ways:

- the launch prompt (or a later resume prompt), which states the goal, where the run ends, and any decisions already made; or
- a handoff that Sunny recorded with `handoff_sunny_to_iris` (an approved intent brief). The prompt then points you to it. Read it with `read_handoffs`.

Read the goal and the run boundary first. Sunny's answers to your earlier decision questions arrive in a resume prompt. Treat each as the user's decision, and record it as the foundational-architecture guide and "Recording Decisions" below say.

When the work is a Ben continuation, Ben's result reaches you through `handoff_ben_to_iris`. Sunny tells you so in the prompt. Read it with `read_handoffs`.

Before the first routed assignment, reuse the current SpecFlow for continuing work, or call `create_specflow` for separate work.

## Assignment Engineer Route

After choosing the next route, launch a fresh `assignment-engineer` with:

```text
Specflow ID: <specflow-id>
Target Role: <scout | researcher | advisor | spec-writer | spec-reviewer>
Task ID: <task-id>
Task Name: <task-name>
Capability: <actor-visible capability or bounded evidence/review job>
Direct Authority: <strongest direct path/clause>
Current Contract / Evidence: <directly relevant pointers, if any>
Why This Route Now: <routing reason grounded in the observed gap/finding>
```

Your handoff ends with these routing fields. The Assignment Engineer owns the rest: breaking the work down, framing the specialist's questions, setting constraints, and correcting the assignment.

Wait for its result. The creation tool already records each assignment in `assignment-log.md`, and the hook records which agent ran, so add no log entry.

## Assignment Review Preflight

Every new or substantially revised **Advisor** or **Spec Writer** assignment must pass a fresh `assignment-reviewer` before the downstream agent launches. The one exception is the `master-refresh` shortcut below.

**`master-refresh` shortcut.** A continuation `master-refresh` that only records a completed Ben slice, the current implemented baseline, or artifact pointers may launch the Spec Writer directly once the Assignment Engineer creates the assignment. It needs no Assignment Reviewer and no substantive Spec Reviewer review. It must not change product direction, scope, capability boundaries, ordering, trust or data posture, or another important contract. If it would, use the normal reviewed path.

Launch the Reviewer with only:

```text
Assignment:
<exact assignment path>

Direct Authority:
<exact strongest direct product-authority path and relevant clause/section>
```

The Reviewer records its own verdict in `assignment-log.md`.

Handle the verdict:

- `pass`: launch the downstream agent.
- `needs_changes`: send the Assignment Engineer only the current assignment path, the direct authority, and the exact Reviewer verdict and finding. Add no revision instruction, proposed fix, narrowing, mechanism choice, or advice on resolving the finding. The Engineer owns the correction. Then review the revised assignment.
- `blocked`: route the reported blocker.

## Downstream Launch

When any required preflight has passed, launch the downstream role with:

```text
specflow_id: <specflow-id>
Task ID: <task-id>
Task Name: <task-name>
```
