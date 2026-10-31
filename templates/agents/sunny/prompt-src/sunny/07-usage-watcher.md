# Usage Watcher

Running Iris and Ben uses up the user's 5-hour usage window. The watcher pauses the least important session before it runs out.

- When any session is running and no watcher is, start one in the background (`run_in_background`):

```text
{{path:trellis_cmd}} watch-usage --project "{{path:project_dir}}" --threshold {{config:sunny.usage_threshold}}
```

- If it prints `usage: unavailable`, usage cannot be read on this machine. Tell the user once. Do not start it again.
- When it exits with `PAUSED <session_id> at <pct>%, resets <time>`:
  1. Call `list_sessions` to confirm which session paused.
  2. Tell the user in one line: what paused, the usage, and the reset time.
  3. Start the watcher again.
- When it exits with `RESET`, the window has reset. Call `list_sessions` and call `resume_session` only for paused sessions that have a `resume_after` time (the watcher paused them), most important first. Use the message "Continue where you stopped." Leave sessions the user or you paused alone. Then start the watcher again.

## Priorities

The user sets priorities. Ask only when they have not said and it matters. By default Ben is above Iris: start Ben at priority 70 and Iris at 50, so a pause hits Iris first. Use `set_session_priority` when the user changes their mind.
