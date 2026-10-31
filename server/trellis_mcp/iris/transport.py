from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .. import settings
from ..chat_io import atomic_write_text
from ..handoffs.transport import append_handoff_chat
from ..messages import validate_author, validate_message
from ..workflow_common import (
    WorkflowStore,
    abs_ref,
    chat_header_markdown,
    listing,
    parse_chat_messages,
    select_messages,
    validate_read_args,
    validate_task_id,
)

SPEC_REVIEW_LENSES = frozenset({"general", "product", "risk", "overengineering", "design_conformance"})
ADVISOR_LENSES = frozenset(
    {
        "security_authority",
        "runtime_implementability",
        "proportionality",
        "cross_lens_reconciliation",
    }
)
ASSIGNMENT_AUTHOR = "Assignment Record"
SPECFLOW_DIRS = ("assignments", "scout", "research", "advice", "specs", "reviews", "handoffs")

store = WorkflowStore("Iris specflow", "specflow_id", lambda: settings.get().paths.specflows_root)


def _validate_specflow_id(specflow_id: str) -> None:
    store.validate_id(specflow_id)


def _specflow_dir(specflow_id: str) -> Path:
    return store.dir(specflow_id)


def _validate_required_fields(fields: dict[str, str]) -> None:
    for value in fields.values():
        validate_message(value)


def _validate_optional_fields(fields: dict[str, str]) -> None:
    for value in fields.values():
        if value.strip():
            validate_message(value)


def _allowed_review_lenses() -> frozenset[str]:
    if settings.get().design_authority:
        return SPEC_REVIEW_LENSES
    return SPEC_REVIEW_LENSES - {"design_conformance"}


def _extract_assignment_field(assignment_md: str, field: str) -> str:
    match = re.search(rf"^\*\*{re.escape(field)}:\*\*\s*(.+?)\s*$", assignment_md, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip().strip("`")


def _latest_assignment_round(assignment_dir: Path, filename_re: re.Pattern[str], kind: str) -> int:
    rounds: list[int] = []
    for path in assignment_dir.iterdir() if assignment_dir.exists() else []:
        if path.is_symlink():
            raise ValueError(f"Iris {kind} assignment file must not be a symlink")
        match = filename_re.fullmatch(path.name)
        if match:
            rounds.append(int(match.group(1)))
    if not rounds:
        raise FileNotFoundError(f"No Iris {kind} assignment found for task: {assignment_dir.name}")
    return max(rounds)


_OUTPUT_FIELDS = {
    "scout_packet_file": "Scout Packet Path",
    "research_packet_file": "Research Packet Path",
    "advice_packet_file": "Advice Packet Path",
    "spec_file": "Spec Output Path",
    "review_file": "Review Packet Path",
}


async def _get_iris_assignment(
    *,
    specflow_id: str,
    task_id: str,
    kind: str,
    filename_re: re.Pattern[str],
    filename_template: str,
    output_field: str,
    round: int,
) -> dict[str, Any]:
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if round < 0:
            raise ValueError("round must be >= 0; use 0 for latest")

        specflow_dir = _specflow_dir(specflow_id)
        store.require_files(specflow_dir)
        assignment_dir = store.child_dir(specflow_dir, "assignments", task_id)
        if not assignment_dir.exists() or not assignment_dir.is_dir():
            raise FileNotFoundError(f"Iris assignment task does not exist: {task_id}")

        selected_round = round or _latest_assignment_round(assignment_dir, filename_re, kind)
        assignment_path = assignment_dir / filename_template.format(round=selected_round)
        assignment_md = store.read_required(assignment_path)

        file_specflow_id = _extract_assignment_field(
            assignment_md, "Specflow ID"
        ) or _extract_assignment_field(assignment_md, "Workitem ID")
        file_task_id = _extract_assignment_field(assignment_md, "Task ID")
        if file_specflow_id != specflow_id:
            raise ValueError(f"Iris {kind} assignment Specflow ID mismatch: {file_specflow_id!r}")
        if file_task_id != task_id:
            raise ValueError(f"Iris {kind} assignment Task ID mismatch: {file_task_id!r}")

        return {
            "ok": True,
            "specflow_id": specflow_id,
            "task_id": task_id,
            "task_name": _extract_assignment_field(assignment_md, "Task Name"),
            "round": selected_round,
            "assignment_file": str(assignment_path),
            output_field: _abs_output(
                specflow_dir, _extract_assignment_field(assignment_md, _OUTPUT_FIELDS[output_field])
            ),
            "assignment_markdown": assignment_md,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _abs_output(specflow_dir: Path, value: str) -> str:
    """Absolute form of an output path stored in an assignment (legacy ones were state-relative)."""
    if not value:
        return ""
    return str(abs_ref(value, specflow_dir.parent.parent))


def _assignment_log_markdown(*, specflow_id: str) -> str:
    return f"""# Assignment Log

**Specflow ID:** {specflow_id}

This log records assignment creation and assignment-review provenance only. It does not create product authority or replace the specflow chat.

---
"""


def _scout_assignment_markdown(
    *,
    specflow_id: str,
    task_id: str,
    task_name: str,
    source: str,
    lens: str,
    goal: str,
    scope: str,
    non_goals: str,
    source_permissions: str,
    round: int,
    packet_rel: str,
) -> str:
    return f"""# Scout Assignment

**Specflow ID:** {specflow_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Source:** {source}
**Lens:** {lens}
**Round:** {round}
**Scout Packet Path:** `{packet_rel}`

## Goal

{goal.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Source Permissions

{source_permissions.strip() or "None specified."}
"""


def _research_assignment_markdown(
    *,
    specflow_id: str,
    task_id: str,
    task_name: str,
    source: str,
    inputs: str,
    routing_decision: str,
    research_questions: str,
    stopping_condition: str,
    scope: str,
    non_goals: str,
    source_permissions: str,
    round: int,
    packet_rel: str,
) -> str:
    return f"""# Research Assignment

**Specflow ID:** {specflow_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Source:** {source}
**Round:** {round}
**Research Packet Path:** `{packet_rel}`

## Inputs

{inputs.strip() or "None specified."}

## Routing Decision

{routing_decision.strip()}

## Research Questions

{research_questions.strip()}

## Stopping Condition

{stopping_condition.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Source Permissions

{source_permissions.strip() or "None specified."}
"""


def _advisor_assignment_markdown(
    *,
    specflow_id: str,
    task_id: str,
    task_name: str,
    mode: str,
    decision_question: str,
    approved_outcome: str,
    user_approved_constraints: str,
    options_visible: str,
    claims_requiring_verification: str,
    changed_boundaries_requiring_closure: str,
    primary_lens: str,
    focus: str,
    inputs: str,
    source: str,
    scope: str,
    non_goals: str,
    source_permissions: str,
    round: int,
    packet_rel: str,
) -> str:
    return f"""# Advisor Assignment

**Specflow ID:** {specflow_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Mode:** {mode}
**Primary Lens:** {primary_lens}
**Source:** {source}
**Round:** {round}
**Advice Packet Path:** `{packet_rel}`

## Decision Question

{decision_question.strip()}

## Approved Outcome

{approved_outcome.strip()}

## User-Approved Constraints

{user_approved_constraints.strip()}

## Options Currently Visible

{options_visible.strip()}

## Claims Requiring Verification

{claims_requiring_verification.strip()}

## Changed Boundaries Requiring Closure

{changed_boundaries_requiring_closure.strip()}

## Primary-Lens Focus

{focus.strip()}

## Inputs

{inputs.strip() or "None specified."}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Source Permissions

{source_permissions.strip() or "None specified."}
"""


def _spec_writer_assignment_markdown(
    *,
    specflow_id: str,
    task_id: str,
    task_name: str,
    mode: str,
    source: str,
    inputs: str,
    goal: str,
    scope: str,
    non_goals: str,
    acceptance: str,
    validation: str,
    round: int,
    spec_rel: str,
) -> str:
    return f"""# Spec Writer Assignment

**Specflow ID:** {specflow_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Mode:** {mode}
**Source:** {source}
**Round:** {round}
**Spec Output Path:** `{spec_rel}`

## Inputs

{inputs.strip() or "None specified."}

## Goal

{goal.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Acceptance

{acceptance.strip() or "None specified."}

## Validation

{validation.strip() or "None specified."}
"""


def _spec_reviewer_assignment_markdown(
    *,
    specflow_id: str,
    task_id: str,
    task_name: str,
    target: str,
    lens: str,
    focus: str,
    inputs: str,
    source: str,
    round: int,
    review_rel: str,
) -> str:
    return f"""# Spec Reviewer Assignment

**Specflow ID:** {specflow_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Target:** {target}
**Lens:** {lens}
**Source:** {source}
**Round:** {round}
**Review Packet Path:** `{review_rel}`

## Focus

{focus.strip()}

## Inputs

{inputs.strip() or "None specified."}
"""


def _spec_output_path(
    *,
    specflow_id: str,
    task_id: str,
    mode: str,
    round: int,
    assignment_dir: Path,
) -> str:
    specs_dir = _specflow_dir(specflow_id) / "specs"
    if round == 1:
        return str(specs_dir / f"{task_id}-{mode}-spec.md")

    previous_assignment = assignment_dir / f"spec-writer-assignment-r{round - 1}.md"
    previous_md = store.read_required(previous_assignment)
    if _extract_assignment_field(previous_md, "Specflow ID") != specflow_id:
        raise ValueError("Previous Iris spec-writer assignment Specflow ID mismatch")
    if _extract_assignment_field(previous_md, "Task ID") != task_id:
        raise ValueError("Previous Iris spec-writer assignment Task ID mismatch")
    if _extract_assignment_field(previous_md, "Mode") != mode:
        raise ValueError("Iris spec mode cannot change between revision rounds")

    stored = _extract_assignment_field(previous_md, "Spec Output Path")
    spec_path = abs_ref(stored, specs_dir.parent.parent.parent) if stored else None
    if spec_path is None or spec_path.parent != specs_dir or ".." in Path(stored).parts:
        raise ValueError("Previous Iris Spec Output Path is invalid")
    return str(spec_path)


def _append_log_unlocked(chat_path: Path, author: str, message: str) -> None:
    store.append_chat(chat_path, author, message)


def _ensure_assignment_log_unlocked(specflow_dir: Path, specflow_id: str) -> Path:
    path = store.file(specflow_dir, "assignment-log.md")
    if not path.exists():
        atomic_write_text(path, _assignment_log_markdown(specflow_id=specflow_id))
    elif not path.is_file():
        raise ValueError("Iris specflow assignment-log.md path is not a file")
    return path


def _write_assignment(
    *,
    specflow_id: str,
    task_id: str,
    filename: str,
    kind: str,
    round: int,
    markdown_for,
    pointer_head: str,
    prepare=None,
) -> tuple[Path, Path]:
    """Write one assignment file and record its pointer in the assignment log.

    ``markdown_for(assignment_dir)`` returns the file text. ``prepare`` may run
    extra checks or directory setup under the lock, with the specflow dir.
    """
    specflow_dir = _specflow_dir(specflow_id)
    with store.lock(specflow_id):
        store.require_files(specflow_dir)
        if prepare is not None:
            prepare(specflow_dir)
        assignment_dir = store.child_dir(specflow_dir, "assignments", task_id)
        assignment_dir.mkdir(parents=True, exist_ok=True)
        assignment_path = assignment_dir / filename
        if assignment_path.exists() and assignment_path.is_symlink():
            raise ValueError(f"Iris {kind} assignment file must not be a symlink")
        if assignment_path.exists():
            raise FileExistsError(f"Iris {kind} assignment already exists: {task_id} round {round}")
        atomic_write_text(assignment_path, markdown_for(assignment_dir))
        chat_message = f"{pointer_head}\nAssignment: `{assignment_path}`"
        _append_log_unlocked(
            _ensure_assignment_log_unlocked(specflow_dir, specflow_id), ASSIGNMENT_AUTHOR, chat_message
        )
    return assignment_path, specflow_dir


def _assignment_result(
    specflow_id: str, task_id: str, assignment_path: Path, specflow_dir: Path, **outputs: str
) -> dict[str, Any]:
    return {
        "ok": True,
        "specflow_id": specflow_id,
        "task_id": task_id,
        "assignment_file": str(assignment_path),
        **outputs,
        "chat_file": str(specflow_dir / "chat.md"),
        "assignment_log_file": str(specflow_dir / "assignment-log.md"),
    }


async def create_iris_specflow(
    specflow_id: str,
    title: str,
    scope_body: str,
) -> dict[str, Any]:
    """Create an Iris specflow directory with chat.md and artifact folders."""
    try:
        _validate_specflow_id(specflow_id)
        _validate_required_fields({"title": title, "scope_body": scope_body})
        current = settings.get()
        specflow_dir = store.create(
            specflow_id,
            {
                "chat.md": chat_header_markdown(
                    id_label="Specflow ID",
                    id_value=specflow_id,
                    title=title.strip(),
                    scope_body=scope_body,
                    project_name=current.project_name,
                    project_root=current.project_dir,
                ),
                "assignment-log.md": _assignment_log_markdown(specflow_id=specflow_id),
            },
            subdirs=SPECFLOW_DIRS,
        )
        return {
            "ok": True,
            "specflow_id": specflow_id,
            "specflow_dir": str(specflow_dir),
            **listing(specflow_dir),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_iris_scout_assignment(
    specflow_id: str,
    task_id: str,
    task_name: str,
    source: str,
    lens: str,
    goal: str,
    scope: str,
    non_goals: str = "",
    source_permissions: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write a scout assignment file and record its pointer in the assignment log."""
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "source": source,
                "lens": lens,
                "goal": goal,
                "scope": scope,
            }
        )
        _validate_optional_fields(
            {
                "non_goals": non_goals,
                "source_permissions": source_permissions,
            }
        )
        packet_path = _specflow_dir(specflow_id) / "scout" / f"{task_id}-scout-r{round}.md"
        path, specflow_dir = _write_assignment(
            specflow_id=specflow_id,
            task_id=task_id,
            filename=f"scout-assignment-r{round}.md",
            kind="scout",
            round=round,
            markdown_for=lambda _dir: _scout_assignment_markdown(
                specflow_id=specflow_id,
                task_id=task_id,
                task_name=task_name.strip(),
                source=source.strip(),
                lens=lens.strip(),
                goal=goal,
                scope=scope,
                non_goals=non_goals,
                source_permissions=source_permissions,
                round=round,
                packet_rel=str(packet_path),
            ),
            pointer_head=(
                f"Type: scout_assignment\nTask ID: {task_id}\nTask Name: {task_name.strip()}\nAction: scout"
            ),
        )
        return _assignment_result(
            specflow_id, task_id, path, specflow_dir, scout_packet_file=str(packet_path)
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_iris_research_assignment(
    specflow_id: str,
    task_id: str,
    task_name: str,
    source: str,
    inputs: str,
    routing_decision: str,
    research_questions: str,
    stopping_condition: str,
    scope: str,
    non_goals: str = "",
    source_permissions: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write a research assignment file and record its pointer in the assignment log."""
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "source": source,
                "inputs": inputs,
                "routing_decision": routing_decision,
                "research_questions": research_questions,
                "stopping_condition": stopping_condition,
                "scope": scope,
            }
        )
        _validate_optional_fields(
            {
                "non_goals": non_goals,
                "source_permissions": source_permissions,
            }
        )
        packet_path = _specflow_dir(specflow_id) / "research" / f"{task_id}-research-r{round}.md"
        path, specflow_dir = _write_assignment(
            specflow_id=specflow_id,
            task_id=task_id,
            filename=f"research-assignment-r{round}.md",
            kind="research",
            round=round,
            markdown_for=lambda _dir: _research_assignment_markdown(
                specflow_id=specflow_id,
                task_id=task_id,
                task_name=task_name.strip(),
                source=source.strip(),
                inputs=inputs,
                routing_decision=routing_decision,
                research_questions=research_questions,
                stopping_condition=stopping_condition,
                scope=scope,
                non_goals=non_goals,
                source_permissions=source_permissions,
                round=round,
                packet_rel=str(packet_path),
            ),
            pointer_head=(
                f"Type: research_assignment\nTask ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\nAction: research"
            ),
        )
        return _assignment_result(
            specflow_id, task_id, path, specflow_dir, research_packet_file=str(packet_path)
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_iris_advisor_assignment(
    specflow_id: str,
    task_id: str,
    task_name: str,
    mode: str,
    decision_question: str,
    approved_outcome: str,
    user_approved_constraints: str,
    options_visible: str,
    claims_requiring_verification: str,
    changed_boundaries_requiring_closure: str,
    primary_lens: str,
    focus: str,
    inputs: str,
    source: str,
    scope: str,
    non_goals: str = "",
    source_permissions: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write an advisor assignment file and record its pointer in the assignment log."""
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if mode not in {"independent_decision", "reconciliation"}:
            raise ValueError("mode must be 'independent_decision' or 'reconciliation'")
        if primary_lens not in ADVISOR_LENSES:
            raise ValueError("primary_lens is not a supported advisor lens")
        if mode == "reconciliation" and primary_lens != "cross_lens_reconciliation":
            raise ValueError("reconciliation mode requires primary_lens='cross_lens_reconciliation'")
        if mode == "independent_decision" and primary_lens == "cross_lens_reconciliation":
            raise ValueError("independent_decision mode requires a non-reconciliation primary lens")
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "mode": mode,
                "decision_question": decision_question,
                "approved_outcome": approved_outcome,
                "user_approved_constraints": user_approved_constraints,
                "options_visible": options_visible,
                "claims_requiring_verification": claims_requiring_verification,
                "changed_boundaries_requiring_closure": changed_boundaries_requiring_closure,
                "primary_lens": primary_lens,
                "focus": focus,
                "inputs": inputs,
                "source": source,
                "scope": scope,
            }
        )
        _validate_optional_fields(
            {
                "non_goals": non_goals,
                "source_permissions": source_permissions,
            }
        )
        packet_path = _specflow_dir(specflow_id) / "advice" / f"{task_id}-advice-r{round}.md"

        def prepare(specflow_dir: Path) -> None:
            store.child_dir(specflow_dir, "advice").mkdir(exist_ok=True)

        action = "reconcile_advice" if mode == "reconciliation" else "advise_decision"
        path, specflow_dir = _write_assignment(
            specflow_id=specflow_id,
            task_id=task_id,
            filename=f"advisor-assignment-r{round}.md",
            kind="advisor",
            round=round,
            prepare=prepare,
            markdown_for=lambda _dir: _advisor_assignment_markdown(
                specflow_id=specflow_id,
                task_id=task_id,
                task_name=task_name.strip(),
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
                source=source.strip(),
                scope=scope,
                non_goals=non_goals,
                source_permissions=source_permissions,
                round=round,
                packet_rel=str(packet_path),
            ),
            pointer_head=(
                f"Type: advisor_assignment\nTask ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\nAction: {action}\n"
                f"Mode: `{mode}`\nPrimary Lens: `{primary_lens}`"
            ),
        )
        return _assignment_result(
            specflow_id, task_id, path, specflow_dir, advice_packet_file=str(packet_path)
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_iris_spec_writer_assignment(
    specflow_id: str,
    task_id: str,
    task_name: str,
    mode: str,
    source: str,
    inputs: str,
    goal: str,
    scope: str,
    non_goals: str = "",
    acceptance: str = "",
    validation: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write a spec-writer assignment file and record its pointer in the assignment log."""
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if mode not in {"master", "single"}:
            raise ValueError("mode must be 'master' or 'single'")
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "source": source,
                "inputs": inputs,
                "goal": goal,
                "scope": scope,
            }
        )
        _validate_optional_fields(
            {
                "non_goals": non_goals,
                "acceptance": acceptance,
                "validation": validation,
            }
        )
        spec_holder: dict[str, str] = {}

        def markdown_for(assignment_dir: Path) -> str:
            spec_holder["path"] = _spec_output_path(
                specflow_id=specflow_id,
                task_id=task_id,
                mode=mode,
                round=round,
                assignment_dir=assignment_dir,
            )
            return _spec_writer_assignment_markdown(
                specflow_id=specflow_id,
                task_id=task_id,
                task_name=task_name.strip(),
                mode=mode,
                source=source.strip(),
                inputs=inputs,
                goal=goal,
                scope=scope,
                non_goals=non_goals,
                acceptance=acceptance,
                validation=validation,
                round=round,
                spec_rel=spec_holder["path"],
            )

        path, specflow_dir = _write_assignment(
            specflow_id=specflow_id,
            task_id=task_id,
            filename=f"spec-writer-assignment-r{round}.md",
            kind="spec-writer",
            round=round,
            markdown_for=markdown_for,
            pointer_head=(
                f"Type: spec_writer_assignment\nTask ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\nAction: write_spec\nMode: `{mode}`"
            ),
        )
        return _assignment_result(specflow_id, task_id, path, specflow_dir, spec_file=spec_holder["path"])
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_iris_spec_reviewer_assignment(
    specflow_id: str,
    task_id: str,
    task_name: str,
    target: str,
    lens: str,
    focus: str,
    inputs: str,
    source: str,
    round: int = 1,
) -> dict[str, Any]:
    """Write a spec-reviewer assignment file and record its pointer in the assignment log."""
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "target": target,
                "lens": lens,
                "focus": focus,
                "inputs": inputs,
                "source": source,
            }
        )
        allowed = _allowed_review_lenses()
        if lens.strip() not in allowed:
            hint = ""
            if lens.strip() == "design_conformance":
                hint = " (design_conformance needs `design_authority` in the project config)"
            raise ValueError("lens must be one of: " + ", ".join(sorted(allowed)) + hint)
        review_path = _specflow_dir(specflow_id) / "reviews" / f"{task_id}-spec-review-r{round}.md"
        path, specflow_dir = _write_assignment(
            specflow_id=specflow_id,
            task_id=task_id,
            filename=f"spec-reviewer-assignment-r{round}.md",
            kind="spec-reviewer",
            round=round,
            markdown_for=lambda _dir: _spec_reviewer_assignment_markdown(
                specflow_id=specflow_id,
                task_id=task_id,
                task_name=task_name.strip(),
                target=target.strip(),
                lens=lens.strip(),
                focus=focus,
                inputs=inputs,
                source=source.strip(),
                round=round,
                review_rel=str(review_path),
            ),
            pointer_head=(
                f"Type: spec_reviewer_assignment\nTask ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\nAction: review_spec"
            ),
        )
        return _assignment_result(specflow_id, task_id, path, specflow_dir, review_file=str(review_path))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _getter(kind: str, prefix: str, output_field: str):
    filename_re = re.compile(rf"{prefix}-assignment-r([0-9]+)\.md")

    async def get(specflow_id: str, task_id: str, round: int = 0) -> dict[str, Any]:
        return await _get_iris_assignment(
            specflow_id=specflow_id,
            task_id=task_id,
            kind=kind,
            filename_re=filename_re,
            filename_template=f"{prefix}-assignment-r{{round}}.md",
            output_field=output_field,
            round=round,
        )

    get.__doc__ = f"Look up an Iris {kind} assignment by task id; round 0 returns the latest round."
    get.__name__ = f"get_iris_{kind.replace('-', '_')}_assignment"
    return get


get_iris_scout_assignment = _getter("scout", "scout", "scout_packet_file")
get_iris_research_assignment = _getter("research", "research", "research_packet_file")
get_iris_advisor_assignment = _getter("advisor", "advisor", "advice_packet_file")
get_iris_spec_writer_assignment = _getter("spec-writer", "spec-writer", "spec_file")
get_iris_spec_reviewer_assignment = _getter("spec-reviewer", "spec-reviewer", "review_file")


async def handoff_iris_to_ben(
    specflow_id: str,
    single_spec_path: str,
    task_id: str,
    task_name: str,
    master_spec_path: str = "",
    supporting_files: str = "",
    status: str = "ready_for_ben",
) -> dict[str, Any]:
    """Append a concise Iris-to-Ben handoff message to an Iris specflow chat."""
    try:
        _validate_specflow_id(specflow_id)
        validate_task_id(task_id)
        if status != "ready_for_ben":
            raise ValueError("status must be 'ready_for_ben'")
        _validate_required_fields(
            {
                "single_spec_path": single_spec_path,
                "task_name": task_name,
            }
        )
        _validate_optional_fields(
            {
                "master_spec_path": master_spec_path,
                "supporting_files": supporting_files,
            }
        )

        specflow_dir = _specflow_dir(specflow_id)
        master_section = f"\nMaster spec: `{master_spec_path.strip()}`" if master_spec_path.strip() else ""
        supporting_section = (
            f"\nSupporting files:\n{supporting_files.strip()}" if supporting_files.strip() else ""
        )
        chat_message = f"""Single spec ready: `{single_spec_path.strip()}`
{master_section}
Status: `{status}`
Suggested Ben task:
- Task ID: {task_id}
- Task Name: {task_name.strip()}
- Source: {single_spec_path.strip()}{supporting_section}"""
        shared_message = f"""Hey Ben, here is the reviewed single spec. Please execute your implementation flow.

Single spec: `{single_spec_path.strip()}`{master_section}
Iris specflow: `{specflow_dir / "chat.md"}`
Suggested Ben task:
- Task ID: {task_id}
- Task Name: {task_name.strip()}{supporting_section}"""
        with store.lock(specflow_id):
            store.require_files(specflow_dir)
            store.append_chat(store.file(specflow_dir, "chat.md"), "Iris", chat_message)
        shared = await append_handoff_chat("Iris", shared_message)
        if not shared.get("ok"):
            raise RuntimeError(f"Failed to append cross-agent handoff: {shared.get('error')}")
        return {
            "ok": True,
            "specflow_id": specflow_id,
            "task_id": task_id,
            "status": status,
            "chat_file": str(specflow_dir / "chat.md"),
            "handoff_chat_file": shared["chat_file"],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def count_iris_chats(specflow_id: str) -> dict[str, Any]:
    """Count timestamped messages in an Iris specflow chat."""
    try:
        specflow_dir = _specflow_dir(specflow_id)
        store.require_files(specflow_dir)
        messages = parse_chat_messages(store.read_required(store.file(specflow_dir, "chat.md")))
        return {
            "ok": True,
            "specflow_id": specflow_id,
            "specflow_dir": str(specflow_dir),
            "count": len(messages),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def read_iris_chats(
    specflow_id: str,
    count: int = 5,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Read recent messages or a 1-based inclusive range from an Iris specflow chat."""
    try:
        validate_read_args(count, start, end)
        specflow_dir = _specflow_dir(specflow_id)
        store.require_files(specflow_dir)
        messages = parse_chat_messages(store.read_required(store.file(specflow_dir, "chat.md")))
        return {
            "ok": True,
            "specflow_id": specflow_id,
            "specflow_dir": str(specflow_dir),
            **select_messages(messages, count, start, end),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def append_iris_chat(specflow_id: str, author: str, message: str) -> dict[str, Any]:
    """Append a timestamped message to an Iris specflow chat."""
    try:
        validate_author(author)
        validate_message(message)
        specflow_dir = _specflow_dir(specflow_id)
        with store.lock(specflow_id):
            store.require_files(specflow_dir)
            store.append_chat(store.file(specflow_dir, "chat.md"), author, message)
        return {"ok": True, "specflow_id": specflow_id, "chat_file": str(specflow_dir / "chat.md")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def read_iris_assignment_log(
    specflow_id: str,
    count: int = 5,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Read recent assignment-log entries or a 1-based inclusive range."""
    try:
        validate_read_args(count, start, end)
        specflow_dir = _specflow_dir(specflow_id)
        store.require_files(specflow_dir)
        log_path = store.file(specflow_dir, "assignment-log.md")
        if log_path.exists():
            messages = parse_chat_messages(store.read_required(log_path))
            exists = True
        else:
            messages = []
            exists = False
        return {
            "ok": True,
            "specflow_id": specflow_id,
            "specflow_dir": str(specflow_dir),
            "assignment_log_file": str(log_path),
            "exists": exists,
            **select_messages(messages, count, start, end),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def append_iris_assignment_log(
    specflow_id: str,
    author: str,
    message: str,
) -> dict[str, Any]:
    """Append one timestamped assignment-engineering or assignment-review provenance entry."""
    try:
        validate_author(author)
        validate_message(message)
        specflow_dir = _specflow_dir(specflow_id)
        with store.lock(specflow_id):
            store.require_files(specflow_dir)
            log_path = _ensure_assignment_log_unlocked(specflow_dir, specflow_id)
            _append_log_unlocked(log_path, author, message)
        return {
            "ok": True,
            "specflow_id": specflow_id,
            "assignment_log_file": str(log_path),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
