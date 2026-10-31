---
name: update
description: Re-render Trellis agent folders after a plugin update or a config edit, then run the health check. Never touches runtime state.
disable-model-invocation: true
---

# /trellis:update

Re-render the Trellis agent folders for this project. Run it after the plugin is updated or after
`.trellis/config.yml` is edited. The plugin lives at `${CLAUDE_PLUGIN_ROOT}`.

1. Find the project directory with `git rev-parse --show-toplevel`. If `.trellis/config.yml` is missing
   there, stop and tell the user to run `/trellis:init`.
2. Preview what would change (writes nothing; exit 1 means some output is stale):

   ```bash
   uvx --from "${CLAUDE_PLUGIN_ROOT}/server" trellis render --project "$PWD" --plugin-root "${CLAUDE_PLUGIN_ROOT}" --check
   ```

   If nothing is stale, say so and still run the health check in step 4.
3. Render:

   ```bash
   uvx --from "${CLAUDE_PLUGIN_ROOT}/server" trellis render --project "$PWD" --plugin-root "${CLAUDE_PLUGIN_ROOT}"
   ```

   Exit 2 is a render error. Show the message and help fix the config. Do not hand-edit rendered files:
   they are overwritten on the next render. `settings.local.json` files are never touched.
4. Check:

   ```bash
   uvx --from "${CLAUDE_PLUGIN_ROOT}/server" trellis doctor --project "$PWD"
   ```

5. Report the result in a few lines. A running Sunny session keeps the old prompts until it is restarted
   (`cd .trellis/agents/sunny && claude`). Iris and Ben pick up the new files the next time Sunny starts or
   resumes them.

Never read, edit or delete anything under `.trellis/state/`. Never push.
