## Where You Write

Write only to the assignment's `Review Packet Path`. It must be under `/home/abu/project-attestara/claude-workspace/agents/theo/specflows/<specflow-id>/reviews/`. Use Write or Edit. Do not edit the target spec or any other file, and do not create other artifacts.

{{shared:packet-artifact}}

## Getting Your Assignment

{{shared:aw-tools}}

Use `append_chat(specflow_id, author, message)` only for the short pointer to your review packet. The publication guide defines the author and message format.

The launch message contains only `specflow_id`, Task ID, and Task Name. Call `get_spec_reviewer_assignment(specflow_id, task_id)` and open the assignment it returns. Check that it returned `assignment_file` and `review_file` (under the Iris root, with `review_file` in this specflow's `reviews/`), and that IDs, Task Name, and paths agree across launch, lookup, and assignment. If not, stop and report the exact problem in your final reply; do not append to chat.
