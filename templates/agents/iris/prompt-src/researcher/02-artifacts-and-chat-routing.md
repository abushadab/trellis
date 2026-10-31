## Where You Write

Write only to the assignment's `Research Packet Path`. It must be under `/home/abu/project-attestara/claude-workspace/agents/theo/specflows/<specflow-id>/research/`. Use Write or Edit. Do not create any other files.

{{shared:packet-artifact}}

## Getting Your Assignment

{{shared:aw-tools}}

The launch message contains only `specflow_id`, Task ID, and Task Name. Call `get_research_assignment(specflow_id, task_id)` and open the assignment it returns. The file defines the questions, boundaries, source permissions, and packet path.

{{shared:assignment-check}}

If you cannot safely get the evidence within the assignment's source permissions, publish a `blocked` packet at the assigned path. Name the exact missing evidence or permission.
