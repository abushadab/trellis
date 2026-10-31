from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from . import transport

RequiredText = Annotated[str, Field(min_length=1)]
SpecflowId = Annotated[
    RequiredText,
    Field(
        pattern=r"^[a-z0-9][a-z0-9-]{1,120}$",
        description="Stable lowercase ID for the Iris specflow; reuse it across the full flow.",
    ),
]
TaskId = Annotated[
    RequiredText,
    Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$",
        description="Stable logical task ID; keep it unchanged across revision rounds.",
    ),
]
Title = Annotated[RequiredText, Field(description="Short human-readable title.")]
ScopeBody = Annotated[
    RequiredText,
    Field(description="Initial outcome, boundaries, and context for the specflow."),
]
TaskName = Annotated[
    RequiredText,
    Field(description="Short task name; keep it unchanged across revision rounds."),
]
Source = Annotated[
    RequiredText,
    Field(description="Authoritative request, decision, or artifact that triggered the assignment."),
]
Inputs = Annotated[
    RequiredText,
    Field(description="Direct artifact pointers or evidence the assignee must inspect."),
]
Lens = Annotated[
    RequiredText,
    Field(description="One bounded perspective for this scout assignment."),
]
ReviewLens = Annotated[
    Literal["general", "product", "risk", "overengineering", "design_conformance"],
    Field(
        description=(
            "Spec review lens. Use general for the default single reviewer; product, risk, or "
            "overengineering only for a deliberate additional specialized review; "
            "design_conformance only when the project config sets design_authority, for a slice "
            "whose screens are defined by that design authority."
        )
    ),
]
AdvisorMode = Annotated[
    Literal["independent_decision", "reconciliation"],
    Field(description="Run a blind complete decision review or reconcile assigned independent reports."),
]
AdvisorPrimaryLens = Annotated[
    Literal[
        "security_authority",
        "runtime_implementability",
        "proportionality",
        "cross_lens_reconciliation",
    ],
    Field(
        description=(
            "Primary investigative emphasis; it does not limit the advisor's complete cross-lens recommendation. "
            "Use cross_lens_reconciliation only with reconciliation mode."
        )
    ),
]
Goal = Annotated[
    RequiredText,
    Field(description="The single result this assignment must produce."),
]
Scope = Annotated[
    RequiredText,
    Field(description="The behavior, evidence, or artifact boundary included in this assignment."),
]
NonGoals = Annotated[
    str,
    Field(description="Work explicitly excluded from the assignment; leave empty when none."),
]
SourcePermissions = Annotated[
    str,
    Field(description="Explicit source-access limits or allowances; leave empty when unspecified."),
]
ResearchQuestions = Annotated[
    RequiredText,
    Field(
        description=(
            "At most three tightly coupled evidence questions supporting the named routing decision; "
            "exclude specification, acceptance-matrix, test-plan, and implementation checklists "
            "unless one is itself the bounded evidence decision."
        ),
    ),
]
RoutingDecision = Annotated[
    RequiredText,
    Field(description="The one route, scope, safety, or specification decision these answers must support."),
]
StoppingCondition = Annotated[
    RequiredText,
    Field(description="The evidence threshold at which the Researcher must stop and return control to Iris."),
]
SpecMode = Annotated[
    Literal["master", "single"],
    Field(description="Write either the master roadmap spec or one Ben-ready single spec."),
]
Acceptance = Annotated[
    str,
    Field(description="Acceptance requirements the resulting spec must preserve or include."),
]
Validation = Annotated[
    str,
    Field(description="Validation expectations the resulting spec must cover."),
]
ReviewTarget = Annotated[
    RequiredText,
    Field(description="Absolute path to the spec artifact being reviewed."),
]
ReviewFocus = Annotated[
    RequiredText,
    Field(description="Concrete issues to emphasize within the assigned review lens."),
]
DecisionQuestion = Annotated[
    RequiredText,
    Field(
        description="Neutral unresolved decision question; do not embed Iris's preferred answer as settled."
    ),
]
ApprovedOutcome = Annotated[
    RequiredText,
    Field(description="User-approved outcome or guarantee the final recommendation must satisfy."),
]
UserApprovedConstraints = Annotated[
    RequiredText,
    Field(description="Explicit user-approved scope, product, safety, and operational constraints."),
]
OptionsVisible = Annotated[
    RequiredText,
    Field(
        description="Realistic options or prior recommendations to compare without declaring one authoritative."
    ),
]
ClaimsRequiringVerification = Annotated[
    RequiredText,
    Field(
        description="Decision-wide claims and uncertainties every advisor must verify against primary evidence."
    ),
]
ChangedBoundariesRequiringClosure = Annotated[
    RequiredText,
    Field(
        description=(
            "Compact common inventory of every changed material remote or authority boundary requiring closure, "
            "including caller and target, authentication and credential custody, semantic authorization/state, "
            "remote failure fencing, residual authority, stage, and verified/open status."
        )
    ),
]
AdvisorFocus = Annotated[
    RequiredText,
    Field(
        description=(
            "Claims, failure modes, and tradeoffs to investigate most deeply. The primary lens guides depth "
            "but does not limit the complete recommendation."
        )
    ),
]
AssignmentRound = Annotated[
    int,
    Field(ge=1, description="Assignment round; start at 1 and increment revisions."),
]
LookupRound = Annotated[
    int,
    Field(ge=0, description="Assignment round to read; use 0 for the latest round."),
]
HandoffSingleSpecPath = Annotated[
    RequiredText,
    Field(description="Absolute path to the reviewed single spec being handed to Ben."),
]
MasterSpecPath = Annotated[
    str,
    Field(description="Absolute path to the related master spec; leave empty when not needed."),
]
SupportingFiles = Annotated[
    str,
    Field(description="Optional Markdown list or text containing direct supporting artifact paths."),
]
ReadyForBenStatus = Annotated[
    Literal["ready_for_ben"],
    Field(description="Fixed status for a reviewed single spec authorized for Ben."),
]
ChatAuthor = Annotated[
    RequiredText,
    Field(description="Human-readable author label recorded with the chat message."),
]
ChatMessage = Annotated[
    RequiredText,
    Field(description="Concise routing message, artifact pointer, status, or summary."),
]
AssignmentLogAuthor = Annotated[
    RequiredText,
    Field(
        description=(
            "Assignment-provenance actor label, normally Assignment Engineer, "
            "Assignment Reviewer, or Iris. This label does not imply product authority."
        )
    ),
]
AssignmentLogMessage = Annotated[
    RequiredText,
    Field(
        description=(
            "Concise assignment provenance only: assignment path/revision, agent session or nickname, "
            "review verdict and one-line finding summary, or downstream routing. Do not copy product/spec content."
        )
    ),
]
RecentCount = Annotated[
    int,
    Field(ge=1, description="Number of most recent messages to read when no range is supplied."),
]
RangeStart = Annotated[
    Annotated[int, Field(ge=1)] | None,
    Field(description="One-based inclusive first message index; provide together with end."),
]
RangeEnd = Annotated[
    Annotated[int, Field(ge=1)] | None,
    Field(description="One-based inclusive last message index; provide together with start."),
]


async def create_specflow(
    specflow_id: SpecflowId,
    title: Title,
    scope_body: ScopeBody,
) -> dict[str, Any]:
    """Create one Iris specflow with its chat and artifact folders."""
    return await transport.create_iris_specflow(specflow_id, title, scope_body)


async def create_scout_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    task_name: TaskName,
    source: Source,
    lens: Lens,
    goal: Goal,
    scope: Scope,
    non_goals: NonGoals = "",
    source_permissions: SourcePermissions = "",
    round: AssignmentRound = 1,
) -> dict[str, Any]:
    """Create one bounded scout assignment and record its pointer in the assignment log."""
    return await transport.create_iris_scout_assignment(
        specflow_id=specflow_id,
        task_id=task_id,
        task_name=task_name,
        source=source,
        lens=lens,
        goal=goal,
        scope=scope,
        non_goals=non_goals,
        source_permissions=source_permissions,
        round=round,
    )


async def create_research_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    task_name: TaskName,
    source: Source,
    inputs: Inputs,
    routing_decision: RoutingDecision,
    research_questions: ResearchQuestions,
    stopping_condition: StoppingCondition,
    scope: Scope,
    non_goals: NonGoals = "",
    source_permissions: SourcePermissions = "",
    round: AssignmentRound = 1,
) -> dict[str, Any]:
    """Create one bounded research assignment and record its pointer in the assignment log."""
    return await transport.create_iris_research_assignment(
        specflow_id=specflow_id,
        task_id=task_id,
        task_name=task_name,
        source=source,
        inputs=inputs,
        routing_decision=routing_decision,
        research_questions=research_questions,
        stopping_condition=stopping_condition,
        scope=scope,
        non_goals=non_goals,
        source_permissions=source_permissions,
        round=round,
    )


async def create_advisor_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    task_name: TaskName,
    mode: AdvisorMode,
    decision_question: DecisionQuestion,
    approved_outcome: ApprovedOutcome,
    user_approved_constraints: UserApprovedConstraints,
    options_visible: OptionsVisible,
    claims_requiring_verification: ClaimsRequiringVerification,
    changed_boundaries_requiring_closure: ChangedBoundariesRequiringClosure,
    primary_lens: AdvisorPrimaryLens,
    focus: AdvisorFocus,
    inputs: Inputs,
    source: Source,
    scope: Scope,
    non_goals: NonGoals = "",
    source_permissions: SourcePermissions = "",
    round: AssignmentRound = 1,
) -> dict[str, Any]:
    """Create one blind decision or reconciliation advisor assignment and record its pointer."""
    return await transport.create_iris_advisor_assignment(
        specflow_id=specflow_id,
        task_id=task_id,
        task_name=task_name,
        mode=mode,
        decision_question=decision_question,
        approved_outcome=approved_outcome,
        user_approved_constraints=user_approved_constraints,
        options_visible=options_visible,
        claims_requiring_verification=claims_requiring_verification,
        changed_boundaries_requiring_closure=changed_boundaries_requiring_closure,
        primary_lens=primary_lens,
        focus=focus,
        inputs=inputs,
        source=source,
        scope=scope,
        non_goals=non_goals,
        source_permissions=source_permissions,
        round=round,
    )


async def create_spec_writer_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    task_name: TaskName,
    mode: SpecMode,
    source: Source,
    inputs: Inputs,
    goal: Goal,
    scope: Scope,
    non_goals: NonGoals = "",
    acceptance: Acceptance = "",
    validation: Validation = "",
    round: AssignmentRound = 1,
) -> dict[str, Any]:
    """Create a master or single spec-writer assignment and record its pointer in the assignment log."""
    return await transport.create_iris_spec_writer_assignment(
        specflow_id=specflow_id,
        task_id=task_id,
        task_name=task_name,
        mode=mode,
        source=source,
        inputs=inputs,
        goal=goal,
        scope=scope,
        non_goals=non_goals,
        acceptance=acceptance,
        validation=validation,
        round=round,
    )


async def create_spec_reviewer_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    task_name: TaskName,
    target: ReviewTarget,
    lens: ReviewLens,
    focus: ReviewFocus,
    inputs: Inputs,
    source: Source,
    round: AssignmentRound = 1,
) -> dict[str, Any]:
    """Create one bounded spec-review assignment and record its pointer in the assignment log."""
    return await transport.create_iris_spec_reviewer_assignment(
        specflow_id=specflow_id,
        task_id=task_id,
        task_name=task_name,
        target=target,
        lens=lens,
        focus=focus,
        inputs=inputs,
        source=source,
        round=round,
    )


async def get_scout_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    round: LookupRound = 0,
) -> dict[str, Any]:
    """Look up an Iris scout assignment by task id; round 0 returns the latest round."""
    return await transport.get_iris_scout_assignment(specflow_id, task_id, round)


async def get_research_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    round: LookupRound = 0,
) -> dict[str, Any]:
    """Look up an Iris research assignment by task id; round 0 returns the latest round."""
    return await transport.get_iris_research_assignment(specflow_id, task_id, round)


async def get_advisor_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    round: LookupRound = 0,
) -> dict[str, Any]:
    """Look up an Iris advisor assignment by task id; round 0 returns the latest round."""
    return await transport.get_iris_advisor_assignment(specflow_id, task_id, round)


async def get_spec_writer_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    round: LookupRound = 0,
) -> dict[str, Any]:
    """Look up an Iris spec-writer assignment by task id; round 0 returns the latest round."""
    return await transport.get_iris_spec_writer_assignment(specflow_id, task_id, round)


async def get_spec_reviewer_assignment(
    specflow_id: SpecflowId,
    task_id: TaskId,
    round: LookupRound = 0,
) -> dict[str, Any]:
    """Look up an Iris spec-reviewer assignment by task id; round 0 returns the latest round."""
    return await transport.get_iris_spec_reviewer_assignment(specflow_id, task_id, round)


async def handoff_to_ben(
    specflow_id: SpecflowId,
    single_spec_path: HandoffSingleSpecPath,
    task_id: TaskId,
    task_name: TaskName,
    master_spec_path: MasterSpecPath = "",
    supporting_files: SupportingFiles = "",
    status: ReadyForBenStatus = "ready_for_ben",
) -> dict[str, Any]:
    """After review and scope approval, append the ready spec to Iris and shared handoff chats."""
    return await transport.handoff_iris_to_ben(
        specflow_id=specflow_id,
        single_spec_path=single_spec_path,
        task_id=task_id,
        task_name=task_name,
        master_spec_path=master_spec_path,
        supporting_files=supporting_files,
        status=status,
    )


async def count_chats(specflow_id: SpecflowId) -> dict[str, Any]:
    """Count timestamped messages in an Iris specflow chat."""
    return await transport.count_iris_chats(specflow_id)


async def read_chats(
    specflow_id: SpecflowId,
    count: RecentCount = 5,
    start: RangeStart = None,
    end: RangeEnd = None,
) -> dict[str, Any]:
    """Read recent messages or a 1-based inclusive range from an Iris specflow chat."""
    return await transport.read_iris_chats(specflow_id, count, start, end)


async def append_chat(
    specflow_id: SpecflowId,
    author: ChatAuthor,
    message: ChatMessage,
) -> dict[str, Any]:
    """Append a timestamped message to an Iris specflow chat."""
    return await transport.append_iris_chat(specflow_id, author, message)


async def read_assignment_log(
    specflow_id: SpecflowId,
    count: RecentCount = 5,
    start: RangeStart = None,
    end: RangeEnd = None,
) -> dict[str, Any]:
    """Read recent assignment provenance or a 1-based inclusive range from assignment-log.md."""
    return await transport.read_iris_assignment_log(specflow_id, count, start, end)


async def append_assignment_log(
    specflow_id: SpecflowId,
    author: AssignmentLogAuthor,
    message: AssignmentLogMessage,
) -> dict[str, Any]:
    """Append one Assignment Engineer/Reviewer or Iris provenance entry to assignment-log.md."""
    return await transport.append_iris_assignment_log(specflow_id, author, message)


IRIS_TOOL_FUNCTIONS = [
    append_chat,
    count_chats,
    read_chats,
    append_assignment_log,
    read_assignment_log,
    create_specflow,
    create_scout_assignment,
    create_research_assignment,
    create_advisor_assignment,
    create_spec_writer_assignment,
    create_spec_reviewer_assignment,
    get_scout_assignment,
    get_research_assignment,
    get_advisor_assignment,
    get_spec_writer_assignment,
    get_spec_reviewer_assignment,
]
