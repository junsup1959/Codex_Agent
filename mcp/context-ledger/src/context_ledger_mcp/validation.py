from __future__ import annotations

from typing import Any


STAGE_ARTIFACTS = {
    "orchestrator": "orchestration_request",
    "context-ledger": "context_packet",
    "task-planner": "execution_plan",
    "worker": "worker_handoff_results",
    "review-distributor": "review_plan",
    "review": "review_handoff_results",
    "feedbackgate": "judgment_envelope",
}

NEXT_OWNER = {
    "orchestrator": "context-ledger",
    "context-ledger": "task-planner",
    "task-planner": "worker",
    "worker": "review-distributor",
    "review-distributor": "review",
    "review": "feedbackgate",
}

PREVIOUS_STAGE = {
    "context-ledger": "orchestrator",
    "task-planner": "context-ledger",
    "worker": "task-planner",
    "review-distributor": "worker",
    "review": "review-distributor",
    "feedbackgate": "review",
}

REQUIRED_TOOL_SEQUENCE = {
    "orchestrator": (
        "initialize_run",
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "context-ledger": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "set_role_pass_readiness",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "task-planner": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "worker": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "review-distributor": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "review": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "feedbackgate": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
}

BARRIER_FIELDS = (
    "stage_name",
    "context_packet_version",
    "consumed_context_revision",
    "context_delta",
    "new_artifact_refs",
    "new_evidence_refs",
    "stage_pass_ref",
)


def validate_stage_packet(
    stage_name: str,
    packet: dict[str, Any],
    *,
    current_revision: int | None = None,
    completed_stages: list[str] | None = None,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append({"code": code, "path": path, "message": message})

    stage_packet = packet.get("stage_packet", packet)
    if not isinstance(stage_packet, dict):
        error("packet.shape", "$", "packet must be an object")
        stage_packet = {}

    if stage_name not in STAGE_ARTIFACTS:
        error("stage.unknown", "stage_name", f"unknown stage: {stage_name}")

    required_previous = PREVIOUS_STAGE.get(stage_name)
    if required_previous and completed_stages is not None and required_previous not in completed_stages:
        error(
            "stage.previous_missing",
            "stage_passes",
            f"{stage_name} requires completed previous stage {required_previous}",
        )

    if stage_packet.get("stage_name") != stage_name:
        error("stage.name", "stage_name", f"stage_name must be {stage_name}")

    for field in BARRIER_FIELDS:
        if field not in stage_packet:
            error("barrier.missing", field, f"missing barrier field: {field}")

    if not isinstance(stage_packet.get("context_packet_version"), int):
        error("barrier.context_packet_version", "context_packet_version", "must be an integer")
    if not isinstance(stage_packet.get("consumed_context_revision"), int):
        error("barrier.consumed_context_revision", "consumed_context_revision", "must be an integer")
    if not isinstance(stage_packet.get("context_delta"), dict):
        error("barrier.context_delta", "context_delta", "must be an object")
    if not isinstance(stage_packet.get("new_artifact_refs"), list):
        error("barrier.new_artifact_refs", "new_artifact_refs", "must be a list")
    if not isinstance(stage_packet.get("new_evidence_refs"), list):
        error("barrier.new_evidence_refs", "new_evidence_refs", "must be a list")
    if not stage_packet.get("stage_pass_ref"):
        error("barrier.stage_pass_ref", "stage_pass_ref", "must be non-empty")

    if current_revision is not None and stage_packet.get("consumed_context_revision") != current_revision:
        error(
            "barrier.stale_revision",
            "consumed_context_revision",
            f"must match current revision {current_revision}",
        )

    artifact_name = STAGE_ARTIFACTS.get(stage_name)
    if artifact_name and artifact_name not in stage_packet and stage_packet.get("artifact_type") != artifact_name:
        error("artifact.missing", artifact_name, f"missing expected artifact: {artifact_name}")

    expected_next = _expected_next_owner(stage_name, stage_packet)
    actual_next = stage_packet.get("next_owner", expected_next)
    if actual_next != expected_next:
        error("handoff.next_owner", "next_owner", f"expected {expected_next}, got {actual_next}")

    if stage_name in {"worker", "review"}:
        _validate_materialization(stage_name, stage_packet, error)

    return {
        "valid": not errors,
        "stage_name": stage_name,
        "expected_artifact": artifact_name,
        "expected_next_owner": expected_next,
        "errors": errors,
    }


def validate_tool_sequence(stage_name: str, observed_tools: list[str]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    required = list(REQUIRED_TOOL_SEQUENCE.get(stage_name, ()))
    if not required:
        errors.append({"code": "sequence.unknown_stage", "path": "stage_name", "message": f"unknown stage: {stage_name}"})
        return {"valid": False, "stage_name": stage_name, "required_order": required, "observed_tools": observed_tools, "errors": errors}

    cursor = 0
    for tool_name in observed_tools:
        if cursor < len(required) and tool_name == required[cursor]:
            cursor += 1

    if cursor != len(required):
        missing = required[cursor:]
        errors.append({
            "code": "sequence.incomplete_or_out_of_order",
            "path": "tool_call_events",
            "message": f"missing or out-of-order required tools: {', '.join(missing)}",
        })

    return {
        "valid": not errors,
        "stage_name": stage_name,
        "required_order": required,
        "observed_tools": observed_tools,
        "errors": errors,
    }


def _expected_next_owner(stage_name: str, packet: dict[str, Any]) -> str:
    if stage_name == "feedbackgate":
        judgment = packet.get("judgment_envelope", packet)
        if isinstance(judgment, dict) and judgment.get("feedback_required") is True:
            return "orchestrator"
        return "final"
    return NEXT_OWNER.get(stage_name, "unknown")


def _validate_materialization(stage_name: str, packet: dict[str, Any], error) -> None:
    active_passes = packet.get("active_passes")
    if active_passes is not None and not isinstance(active_passes, list):
        error("active_passes.shape", "active_passes", "must be a list")

    handoff_name = "worker_handoff_results" if stage_name == "worker" else "review_handoff_results"
    handoffs = packet.get(handoff_name)
    if not isinstance(handoffs, list):
        error("handoff.shape", handoff_name, "must be a list")
        return

    for index, item in enumerate(handoffs):
        path = f"{handoff_name}[{index}]"
        if not isinstance(item, dict):
            error("handoff.item_shape", path, "must be an object")
            continue
        if not item.get("lane_id"):
            error("handoff.lane_id", f"{path}.lane_id", "lane_id is required")
        if item.get("status") not in {
            "returned",
            "timed_out",
            "failed",
            "superseded",
            "schema_invalid",
            "no_wait_handle",
            "thread_limit_reached",
        }:
            error("handoff.status", f"{path}.status", "invalid or missing lane status")
            continue
        if item.get("status") == "returned":
            if not item.get("spawn_receipt_ref"):
                error("handoff.spawn_receipt_ref", f"{path}.spawn_receipt_ref", "spawn receipt evidence is required")
            if not (item.get("agent_id") or item.get("submission_id")):
                error("handoff.agent_id", f"{path}.agent_id", "agent_id or submission_id is required")
            if not item.get("wait_agent_evidence"):
                error("handoff.wait_agent_evidence", f"{path}.wait_agent_evidence", "wait_agent evidence is required")
