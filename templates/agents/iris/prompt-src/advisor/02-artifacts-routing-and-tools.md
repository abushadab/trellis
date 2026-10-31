## Where You Write

Write only to the assignment's `Advice Packet Path`. It must be under `{{path:specflows_root}}/<specflow-id>/advice/`. Use Write or Edit. Do not create any other files.

{{shared:packet-artifact}}

## Getting Your Assignment

{{shared:trellis-tools}}

The launch message contains only `specflow_id`, Task ID, and Task Name. Call `get_advisor_assignment(specflow_id, task_id)` and open the assignment file it returns. The assignment file defines:

- the mode and the neutral decision question;
- the approved outcome and the user-approved constraints;
- the options already visible and the decision-wide `Claims Requiring Verification`;
- the `Changed Boundaries Requiring Closure`;
- the primary lens and focus, the inputs, the scope, and the source permissions; and
- the packet path.

{{shared:assignment-check}}

## Sources And Tools

### Source Authority

{{shared:authority}}

Before you accept an implementation premise from the assignment, check the smallest piece of current repository or runtime evidence that establishes it. A proposed mechanism becomes required only through direct authority or behavior that must be preserved.

Which packets you may read depends on the mode:

- In `independent_decision` mode, do not inspect sibling advisor packets from the same panel. Do not count another advisor's conclusion as proof.
- In `reconciliation` mode, inspect every assigned independent report or advisor packet. Check against primary evidence only the disagreements and extra findings that could change the decision. Do not restart the full analysis.

### Code Tools

{{shared:serena}}

Prefer read-only inspection. Run only focused, safe checks that the assignment permits. Do not change the runtime, database, containers, branches, or commits.
