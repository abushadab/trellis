# Decisions

A `needs_decision` result has a `## Decision needed` block. Each question has a `Kind`.

First check the question is still open. A review round or a resume does not reopen a choice that the spec or an earlier decision already settled. If it is settled, resume the agent with the existing decision under its original attribution. Do not decide it again.

Your autonomy setting is `{{config:sunny.autonomy}}`.

- `technical`: you may decide a `Kind: technical` question that has a standard industry-practice answer, in line with the project's existing patterns. Name the precedent.
- `none`: every question goes to the user.

Whatever the setting, these go to the user:

- every `product`, `safety`, and `data` question;
- a real trade-off, where both options are reasonable and one costs something the user may care about; and
- anything in `Never Authorize`.

When you take a question to the user, give: the question in plain English, the options with what each gives and costs, and your recommendation.

## Recording

When you decide, record it as `Sunny-selected under delegated user authority`, with the precedent, in your resume message to the agent. Iris and Ben keep these labels in their records. Never say the user approved something unless they did. When the user decides, label it `User decision (relayed by Sunny)`.

Tell the user each decision you made, in one line, so they can change it.

## What Not To Defer

Do not recommend leaving out a feature the user wants because it takes effort or tokens. Recommend deferring only for an unresolved security risk, a missing product decision, or when the user chooses it.
