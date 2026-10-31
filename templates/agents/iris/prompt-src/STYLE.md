# Prompt Style Guide

Rules for writing and editing Iris's Claude Code prompt parts (`prompt-src/`) and guides (`../guidance/`). The agent output rules live in `_shared/writing.md`; this file is for prompt authors.

## Goal

A prompt should read like a clear brief to a capable colleague. Every rule stays; the words get simpler.

## Rules

1. **Keep every behavior.** Do not add a rule, drop a rule, or change a threshold while rewording. If two sentences say the same thing, keep one. If a rule is unclear, keep its meaning and flag it; do not guess a new meaning.
2. **Keep exact contracts unchanged.** Tool names, file paths, field names, status values, verdict strings, source-ID prefixes, chat-pointer formats, lens and mode names, and `{{shared:…}}` placeholders stay exactly as they are.
3. **Use plain words.** Prefer common words over abstract nouns. Write "check whether X is needed now" rather than "establish need-now evidence for X".
4. **One idea per sentence.** Keep most sentences under about 25 words. Split long lists of conditions into bullets.
5. **Use "you" and active voice.** "Write the packet to…" rather than "The packet must be written to…".
6. **Say why once, briefly, when it helps the agent judge edge cases.** Do not justify every rule.
7. **Order each prompt as:** who you are and what you produce → inputs and setup → steps → output → final check.
8. **Do not repeat across files.** If a guide already defines something, the prompt points to it instead of restating it.
9. **Prefer short bullets over long single-paragraph checklists.** A final check is a bullet list.
10. **Use the glossary below** so every role uses the same plain term for the same idea.
11. **Merge overlaps, keep behavior.** When a rule appears twice inside one role (in two parts, or in a part and its guide), keep it once in the place where the agent needs it first, and point to it from the other place if needed. A final checklist may still name each check briefly. Aim for about the same length as before, not longer. Never merge two rules whose conditions or thresholds differ, even slightly.
12. **When a long condition repeats, name it once.** Define a short plain term (for example **route-changing**) where it is first used, then reuse the term.
13. **Keep names other files depend on.** Do not rename a packet or template heading, field label, or section name that another role's prompt, Iris's guides, the `aw` tools, or Ben's prompts refer to. Spec template headings and field labels (`Status`, `Source References`, `Intent`, `Decisions`, `Boundaries`, `Preserve:`, `Acceptance`, `Open Questions`, and the master template's equivalents) stay unchanged because Ben reads specs. Search before renaming any heading.

14. **Do not restate what Claude Code enforces.** A role's `tools:` list, the settings deny and ask rules, and Claude Code's own tool guidance already apply. Keep a prompt rule only when it adds a condition the harness cannot check, such as which single file a role may write.

## Glossary

Use the plain term on the right. Do not use the old term on the left in prompts or templates.

| Old term | Plain term |
| --- | --- |
| need-now evidence / need-now trace | evidence it is needed now: the current behavior that needs it, who produces and uses it, the acceptance check, and what breaks if it waits |
| parity destination / future parity | the later full-feature goal |
| load-bearing (behavior, guarantee) | essential; existing behavior that other behavior depends on |
| seam / changed seam | the place where the change meets existing code; the changed boundary |
| blocking gap | blocker: a missing fact or decision without which the spec cannot be stated or tested |
| surviving witness / surviving authority | a record that still proves the outcome after the failure |
| narrowest complete (safe) solution / option | the smallest option that fully and safely meets the need |
| materially broad | broad work (keep the existing triggers that define it) |
| material | important enough to change the decision (or simply drop the word when it adds nothing) |
| terrain | the relevant code and systems |
| lane (meaning a routing lane) | route / task (e.g. "Researcher task"). A parallel-work lane (lane id, lane table, lane handoff, integrator) is an Attestara term: keep it, and see `guidance/theo/lanes.md`. |
| specifiability | whether the spec can be written |
| closure-feasibility rows | finality checks |
| blast radius | what the change touches |
| ceremony | extra process |
| Audit Facts (packet heading) | What Was Checked |

Keep plain technical terms the agents need (caller, credential, migration, idempotent, race), and explain one in a few words only where a reader might not know it.
