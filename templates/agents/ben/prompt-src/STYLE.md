# Prompt Style Guide

Rules for writing and editing Ben's Claude Code prompt parts (`prompt-src/`) and guides (`../guidance/`). Agent output rules live in `_shared/writing.md`; this file is for prompt authors.

## Goal

A prompt should read like a clear brief to a capable colleague. Every rule stays; the words get simpler.

## Rules

1. **Keep every behavior.** Do not add a rule, drop a rule, or change a threshold while rewording. If two sentences say the same thing, keep one. If a rule is unclear, keep its meaning and flag it; do not guess a new meaning.
2. **Keep exact contracts unchanged.** Tool names, file paths, chat-pointer formats (`Plan ready:`, `Review ready:`, `Implementation packet:`, `Validation packet:`, `Investigation packet:`, `Type: …`), `Action:` values, launch-input field names, status values, template headings and field labels, source-ID formats, Git commit message and author formats, `AUTOMATION_ROUTING_BLOCKED_V1`, the `## Turn Status` block, and the template placeholders (`{{shared:…}}`, `{{config:…}}`, `{{path:…}}`, `{{if:…}}` with `{{else}}` and `{{/if}}`) stay exactly as they are.
3. **Use plain words.** Prefer common words over abstract nouns.
4. **One idea per sentence.** Keep most sentences under about 25 words. Split long condition lists into bullets.
5. **Use "you" and active voice.**
6. **Say why once, briefly, when it helps the agent judge edge cases.** Do not justify every rule.
7. **Order each prompt as:** who you are and what you produce → inputs and setup → steps → output → final check. The `Launch and Chat Routing Protocol` part may stay after the workflow, as long as the first step that needs it points to it.
8. **Do not repeat across files.** If a guide or shared part already defines something, point to it instead of restating it.
9. **Prefer short bullets over long single-paragraph checklists.** A final check is a bullet list; each item names its check briefly.
10. **Use the glossary below** so every role uses the same plain term for the same idea.
11. **Merge overlaps, keep behavior.** When a rule appears twice inside one role (in two parts, or in a part and its guide), keep it once where the agent needs it first, and point to it from the other place if needed. Never merge two rules whose conditions or thresholds differ, even slightly. Aim for about the same length as before, not longer.
12. **When a long condition repeats, name it once.** Define a short plain term where it is first used, then reuse it.
13. **Keep names other files depend on.** Do not rename a heading, field label, or section name that another role's prompt, Iris's guides, the Trellis MCP server, the renderer, or the prompt contract tests under `tests/` refers to. Search before renaming.
14. **Keep each role's permissions separate.** The Planner and Plan Reviewer may not run tests or builds; the Implementation Reviewer may; the Validator and Investigator have their own runtime limits. Rewording must not blur these.
15. **Do not restate what Claude Code enforces.** A role's `tools:` list, the settings deny and ask rules, and Claude Code's own tool guidance already apply. Keep a prompt rule only when it adds a condition the harness cannot check, such as which single file a role may write.

## Glossary

Use the plain term on the right in prose. Field names and template labels that contain an old term (for example `Acceptance oracle`, `Test/evidence disposition`) keep their exact names.

| Old term | Plain term |
| --- | --- |
| material / materially (outside the defined threshold) | important; or drop it. Keep *material* only in the defined `material-risk` sense. |
| proportionate / proportional | matched to the risk; no more than the risk needs |
| topology | runtime layout: which services and containers run, and how they connect |
| oracle (in prose) | expected result: the fixed result a test checks |
| disposition (in prose) | what happens to it (keep, revise, retire…) |
| ceremony | extra process |
| falsify / falsification | try to disprove; disprove |
| invariant | rule that must always hold |
| predicate | condition |
| surface | area; part of the system |
| provenance | record of who did what |
| witness | record that proves it |
| seam | the place where the change meets existing code |
| load-bearing | essential |
| blast radius | what the change touches |
| discriminating (test) | a test that fails on the wrong implementation |

Keep plain technical terms the agents need (commit, migration, fixture, harness, race, idempotent), and explain one in a few words only where a reader might not know it.
