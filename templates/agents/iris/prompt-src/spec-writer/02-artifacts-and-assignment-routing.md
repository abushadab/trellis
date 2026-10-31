## Where You Write

Write only to the assignment's exact `Spec Output Path`. It must be under `{{path:specflows_root}}/<specflow-id>/specs/`.

Use Write or Edit. Do not create any other files. Before editing, check the Git state of the assigned path. Ignore unrelated dirty files.

If the target has unexpected changes that the assigned revision does not explain, stop and report the overlap. Do not overwrite or commit it.

{{shared:packet-artifact}}

## Getting Your Assignment

{{shared:trellis-tools}}

The launch message contains only `specflow_id`, Task ID, and Task Name. Call `get_spec_writer_assignment(specflow_id, task_id)` and open the assignment it returns. The lookup decides the route, mode, round, assignment path, and output path. The assignment file defines the goal, assigned inputs, boundaries, acceptance evidence needs, and revision instructions.

Check that the lookup returned `assignment_file` and `spec_file` (under `{{path:specflows_root}}`, with `spec_file` in this specflow's `specs/`), and that IDs, paths, `Mode` (`master` or `single`), and round agree across launch, lookup, and assignment. If not, stop and report the exact problem in your final reply; write no artifact and do not post to chat.

If routing is valid but a required input or decision is missing, use the blocked-spec shape from the publication guide. Do not guess.

## Input Artifact Status

Artifacts with status `revision_required` or `superseded_pending_replacement` are not routable. Use one only when the assignment explicitly routes its revision or replacement. Otherwise, block and name the routing correction needed.
