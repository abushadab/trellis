# Routing Stop

Each failing step below gets at most three attempts in total: the first try and up to two retries.

- **Malformed or unrecognized arguments:** fix the arguments and try again.
- **Blocking subagent-routing failure:** base each recovery attempt on what the error says. Before each one, check what the last attempt already did, such as a created assignment or a started engineer. Continue from there; do not create it again.

If the third attempt still fails, do not repeat the operation. Stop and end your turn with this block as the start of your final message, followed by the `Turn Status` block with `Status: blocked`:

```text
AUTOMATION_ROUTING_BLOCKED_V1
<one-sentence description of the routing issue>
```

Keep the report short. Sunny reads it and decides how to recover.
