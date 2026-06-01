from __future__ import annotations

from typing import Any


STAGE_ARTIFACTS = {
    "orchestrator": "orchestration_request",
    "context-ledger": "context_packet",
    "task-designer": "task_design",
    "task-distributor": "execution_plan",
    "worker": "worker_handoff_results",
    "review-distributor": "review_plan",
    "review": "review_handoff_results",
    "feedbackgate": "judgment_envelope",
}

NEXT_OWNER = {
    "orchestrator": "context-ledger",
    "context-ledger": "task-designer",
    "task-designer": "task-distributor",
    "task-distributor": "worker",
    "worker": "review-distributor",
    "review-distributor": "review",
    "review": "feedbackgate",
}

DIRECT_WORKFLOW_OWNER = "direct-workflow"

SEQUENTIAL_THINKING_REQUIRED_STAGES = {
    "orchestrator",
    "task-designer",
    "task-distributor",
    "review-distributor",
}

STAGE_GUIDANCE = {
    "orchestrator": {
        "activation_ref": "$orchestrator",
        "contract_ref": "skills/orchestrator/contract.json",
        "source_docs": ["00-canonical-map.md", "09-runtime-orchestration-steps.md"],
        "required_input_artifacts": ["user_goal", "latest_user_message", "feedback_carryover", "task_design_reentry_decision"],
        "required_external_mcp_tools": ["MCP_DOCKER.sequentialthinking"],
        "required_sections": ["sequential_thinking_ref_or_waiver", "scope", "success_criteria", "risk_flags"],
    },
    "context-ledger": {
        "activation_ref": "$context-ledger",
        "contract_ref": "skills/context-ledger/contract.json",
        "source_docs": ["02-context-planning.md"],
        "required_input_artifacts": ["orchestration_request", "latest_context_packet"],
    },
    "task-designer": {
        "activation_ref": "$task-designer",
        "contract_ref": "skills/task-designer/contract.json",
        "source_docs": ["02-context-planning.md"],
        "required_input_artifacts": ["orchestration_request", "context_packet"],
        "required_external_mcp_tools": ["MCP_DOCKER.sequentialthinking"],
        "required_sections": [
            "problem_definition",
            "assumptions",
            "options",
            "comparison_criteria",
            "selected_option_id",
            "selection_rationale",
            "selected_option_risks",
            "distribution_boundaries",
            "artifact_profile",
            "sequential_thinking_ref_or_waiver",
        ],
        "expected_output_artifact": "task_design",
        "must_not_do": ["select concrete agents", "create worker lanes", "set fanout allocation"],
    },
    "task-distributor": {
        "activation_ref": "$task-distributor",
        "contract_ref": "skills/task-distributor/contract.json",
        "source_docs": ["02-context-planning.md", "06-agent-roster-models.md"],
        "required_input_artifacts": ["task_design", "selected_task_design_ref", "context_packet", "fanout_budget"],
        "required_external_mcp_tools": ["MCP_DOCKER.sequentialthinking"],
        "required_sections": [
            "selected_task_design_ref",
            "task_distribution_criteria_ref",
            "artifact_profile",
            "sequential_thinking_ref_or_waiver",
            "worker_lanes",
            "dependencies",
            "fanout_budget",
        ],
        "expected_output_artifact": "execution_plan",
        "must_not_do": ["redefine task design", "change selected option", "spawn workers"],
    },
    "worker": {
        "activation_ref": "$worker",
        "contract_ref": "skills/worker/contract.json",
        "source_docs": ["03-worker-materialization.md", "06-agent-roster-models.md"],
        "required_input_artifacts": ["execution_plan", "task_distribution_criteria_ref", "context_packet", "fanout_budget"],
    },
    "review-distributor": {
        "activation_ref": "$review-distributor",
        "contract_ref": "skills/review-distributor/contract.json",
        "source_docs": ["04-review-flow.md", "06-agent-roster-models.md"],
        "required_input_artifacts": ["worker_handoff_results", "active_passes", "context_packet", "fanout_budget"],
        "required_external_mcp_tools": ["MCP_DOCKER.sequentialthinking"],
        "required_sections": [
            "worker_handoff_results_ref",
            "review_distribution_criteria_ref",
            "artifact_profile",
            "sequential_thinking_ref_or_waiver",
            "review_lanes",
            "coverage_contract",
        ],
        "expected_output_artifact": "review_plan",
        "must_not_do": ["spawn reviewers", "skip review coverage criteria"],
    },
    "review": {
        "activation_ref": "$review",
        "contract_ref": "skills/review/contract.json",
        "source_docs": ["04-review-flow.md", "06-agent-roster-models.md"],
        "required_input_artifacts": ["review_plan", "review_distribution_criteria_ref", "worker_handoff_results", "active_passes", "fanout_budget"],
    },
    "feedbackgate": {
        "activation_ref": "$feedbackgate",
        "contract_ref": "skills/feedbackgate/contract.json",
        "source_docs": ["05-feedback-lifecycle.md", "08-quality-evals.md"],
        "required_input_artifacts": [
            "worker_handoff_results",
            "review_handoff_results",
            "review_waivers",
            "stage_passes",
            "active_passes",
        ],
    },
    DIRECT_WORKFLOW_OWNER: {
        "activation_ref": None,
        "contract_ref": None,
        "source_docs": ["00-canonical-map.md", "09-runtime-orchestration-steps.md"],
        "required_input_artifacts": ["orchestration_request", "express_direct_handoff"],
        "required_external_mcp_tools": [],
        "required_sections": ["workflow_mode", "complexity_classification", "direct_workflow_scope"],
    },
}

STAGE_PACKET_TEMPLATES = {
    "orchestrator": {
        "stage_name": "orchestrator",
        "context_packet_version": "<int: next packet version>",
        "consumed_context_revision": "<int: read.context_revision>",
        "stage_execution_mode": "main_agent_role_pass",
        "stage_pass_ref": "stage_pass:orchestrator:<append.id>",
        "sequential_thinking_ref": "<ref or use sequential_thinking_waiver>",
        "architecture_required": True,
        "orchestration_request": {
            "run_id": "<run_id>",
            "loop_id": "<loop id>",
            "architecture_required": True,
            "scope": {
                "goal": "<user goal>",
                "in_scope": ["<in scope item>"],
                "out_of_scope": ["<out of scope item>"],
            },
            "success_criteria": ["<criterion>"],
            "risk_flags": ["<risk>"],
            "feedback_carryover": ["<feedback item>"],
            "task_design_reentry_decision": "<decision or null>",
            "sequential_thinking_ref": "<same ref or use sequential_thinking_waiver>",
            "stage_pass_ref": "stage_pass:orchestrator:<append.id>",
            "context_delta": {"approved_facts": ["<fact>"]},
            "new_artifact_refs": ["<artifact ref>"],
            "new_evidence_refs": ["stage_pass:orchestrator:<append.id>"],
            "next_owner": "context-ledger",
        },
        "context_delta": {"approved_facts": ["<fact>"]},
        "new_artifact_refs": ["<artifact ref>"],
        "new_evidence_refs": [
            "stage_pass:orchestrator:<append.id>",
            "<sequential_thinking_ref or waiver evidence>",
        ],
        "next_owner": "context-ledger",
    },
    "orchestrator_express_direct": {
        "stage_name": "orchestrator",
        "context_packet_version": "<int: next packet version>",
        "consumed_context_revision": "<int: read.context_revision>",
        "stage_execution_mode": "main_agent_role_pass",
        "stage_pass_ref": "stage_pass:orchestrator:<append.id>",
        "sequential_thinking_ref": "<ref or use sequential_thinking_waiver>",
        "architecture_required": False,
        "workflow_mode": "express-direct",
        "orchestration_request": {
            "run_id": "<run_id>",
            "loop_id": "<loop id>",
            "architecture_required": False,
            "workflow_mode": "express-direct",
            "complexity_classification": "simple",
            "direct_workflow_scope": {
                "allowed_actions": ["normal direct workflow implementation and validation"],
                "excluded_actions": ["specialist fanout", "architecture completion claims"],
            },
            "express_direct_reason": "<why the full architecture loop is unnecessary>",
            "sequential_thinking_ref": "<same ref or use sequential_thinking_waiver>",
            "stage_pass_ref": "stage_pass:orchestrator:<append.id>",
            "context_delta": {"approved_facts": ["<fact>"]},
            "new_artifact_refs": ["<artifact ref>"],
            "new_evidence_refs": ["stage_pass:orchestrator:<append.id>"],
            "next_owner": DIRECT_WORKFLOW_OWNER,
        },
        "context_delta": {"approved_facts": ["<fact>"]},
        "new_artifact_refs": ["<artifact ref>"],
        "new_evidence_refs": [
            "stage_pass:orchestrator:<append.id>",
            "<sequential_thinking_ref or waiver evidence>",
        ],
        "next_owner": DIRECT_WORKFLOW_OWNER,
    },
    "context-ledger": {
        "stage_name": "context-ledger",
        "context_packet_version": "<int: next packet version>",
        "consumed_context_revision": "<int: read.context_revision>",
        "stage_execution_mode": "main_agent_role_pass",
        "stage_pass_ref": "stage_pass:context-ledger:<append.id>",
        "context_packet": {
            "context_packet_version": "<same int>",
            "source_stage": "context-ledger",
            "consumed_context_revision": "<int: read.context_revision>",
            "stage_pass_ref": "stage_pass:context-ledger:<append.id>",
            "approved_facts": ["<fact>"],
            "constraints": ["<constraint>"],
            "artifact_refs": ["<artifact ref>"],
            "evidence_refs": ["<evidence ref>"],
            "role_pass_readiness": {"task-designer": True},
            "context_delta": {"new_facts": ["<fact>"]},
            "next_owner": "task-designer",
        },
        "context_delta": {"new_facts": ["<fact>"]},
        "new_artifact_refs": ["context_packet:<run_id>:rev<N>"],
        "new_evidence_refs": ["stage_pass:context-ledger:<append.id>"],
        "next_owner": "task-designer",
    },
    "task-designer": {
        "stage_name": "task-designer",
        "context_packet_version": "<int: next packet version>",
        "consumed_context_revision": "<int: read.context_revision>",
        "stage_execution_mode": "main_agent_role_pass",
        "stage_pass_ref": "stage_pass:task-designer:<append.id>",
        "task_design": {
            "problem_definition": "<problem>",
            "assumptions": ["<assumption>"],
            "options": [
                {
                    "id": "option-a",
                    "title": "<option title>",
                    "summary": "<option summary>",
                    "fit_assessment": "<fit assessment>",
                    "tradeoffs": ["<tradeoff>"],
                },
                {
                    "id": "option-b",
                    "title": "<option title>",
                    "summary": "<option summary>",
                    "fit_assessment": "<fit assessment>",
                    "tradeoffs": ["<tradeoff>"],
                },
                {
                    "id": "option-c",
                    "title": "<option title>",
                    "summary": "<option summary>",
                    "fit_assessment": "<fit assessment>",
                    "tradeoffs": ["<tradeoff>"],
                },
            ],
            "comparison_criteria": ["<criterion>"],
            "selected_option_id": "option-b",
            "selection_rationale": "<rationale>",
            "selected_option_risks": ["<risk>"],
            "distribution_boundaries": ["<boundary for task-distributor>"],
            "artifact_profile": {
                "version": 1,
                "source_stage": "task-designer",
                "reuse_policy": "<reuse policy>",
                "invalidated_by": ["<invalidation condition>"],
            },
            "sequential_thinking_ref": "<ref or use sequential_thinking_waiver>",
        },
        "context_delta": {"new_facts": ["<design fact>"]},
        "new_artifact_refs": ["task_design.md"],
        "new_evidence_refs": [
            "stage_pass:task-designer:<append.id>",
            "validate_task_design:true",
        ],
        "next_owner": "task-distributor",
    },
}

PREVIOUS_STAGE = {
    "context-ledger": "orchestrator",
    "task-designer": "context-ledger",
    "task-distributor": "task-designer",
    "worker": "task-distributor",
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
    "task-designer": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "validate_task_design",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "task-distributor": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "validate_execution_plan",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "worker": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "validate_stage_completion",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "review-distributor": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "validate_review_plan",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "review": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "validate_stage_completion",
        "write_context_packet",
        "record_mcp_quiescence",
        "validate_tool_sequence",
    ),
    "feedbackgate": (
        "read_context_packet",
        "validate_context_revision",
        "append_stage_pass",
        "validate_stage_packet",
        "validate_stage_completion",
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
    elif stage_name == "orchestrator":
        _validate_sequential_thinking_ref(stage_packet, "sequential_thinking_ref", error)
    elif stage_name == "context-ledger":
        _validate_reentry_cache_if_present(stage_packet, error)
    elif stage_name == "task-designer":
        _extend_errors(validate_task_design(stage_packet), errors)
    elif stage_name == "task-distributor":
        _extend_errors(validate_execution_plan(stage_packet), errors)
    elif stage_name == "review-distributor":
        _extend_errors(validate_review_plan(stage_packet), errors)

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
        "next_stage": build_next_stage_guidance(expected_next),
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


def validate_stage_completion(stage_name: str, packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append({"code": code, "path": path, "message": message})

    stage_packet = packet.get("stage_packet", packet)
    if not isinstance(stage_packet, dict):
        error("packet.shape", "$", "packet must be an object")
        stage_packet = {}

    if stage_name == "worker":
        handoffs = stage_packet.get("worker_handoff_results")
        missing_lanes = stage_packet.get("missing_lane_classifications")
        missing_lanes_valid = _validate_lane_reason_items("missing_lane_classifications", missing_lanes, error)
        if not _non_empty_list(handoffs) and not missing_lanes_valid:
            error(
                "completion.worker_lanes_missing",
                "worker_handoff_results",
                "worker completion requires at least one handoff result or missing-lane classification",
            )
    elif stage_name == "review":
        handoffs = stage_packet.get("review_handoff_results")
        waivers = stage_packet.get("review_waivers")
        waivers_valid = _validate_lane_reason_items("review_waivers", waivers, error)
        if not _non_empty_list(handoffs) and not waivers_valid:
            error(
                "completion.review_lanes_missing",
                "review_handoff_results",
                "review completion requires at least one review result or explicit waiver",
            )
    elif stage_name == "feedbackgate":
        judgment = stage_packet.get("judgment_envelope", {})
        if not isinstance(judgment, dict):
            error("completion.judgment_shape", "judgment_envelope", "judgment_envelope must be an object")
            judgment = {}
        if judgment.get("feedback_required") is True:
            _validate_task_design_reentry_decision(
                judgment.get("task_design_reentry_decision", stage_packet.get("task_design_reentry_decision")),
                error,
            )
        elif judgment.get("feedback_required") is False:
            waivers_valid = _validate_lane_reason_items("review_waivers", stage_packet.get("review_waivers"), error)
            _validate_non_empty_dict(
                "feedback_gate_evidence",
                stage_packet.get("feedback_gate_evidence"),
                "completion.feedback_gate_evidence_missing",
                "final readiness requires feedback gate evidence",
                error,
            )
            review_input_refs = stage_packet.get("review_input_refs")
            review_refs_valid = (
                _validate_non_empty_string_list("review_input_refs", review_input_refs, error)
                if review_input_refs is not None
                else False
            )
            if not (review_refs_valid or waivers_valid):
                error(
                    "completion.review_inputs_missing",
                    "review_input_refs",
                    "final readiness requires reviewer input refs or explicit review waivers",
                )
            if not _validate_non_empty_string_list("stage_passes", stage_packet.get("stage_passes"), error):
                error("completion.stage_passes_missing", "stage_passes", "final readiness requires stage pass evidence")
            if not _validate_non_empty_string_list("active_passes", stage_packet.get("active_passes"), error):
                error("completion.active_passes_missing", "active_passes", "final readiness requires active pass evidence")
    elif stage_name not in STAGE_ARTIFACTS:
        error("stage.unknown", "stage_name", f"unknown stage: {stage_name}")

    return {
        "valid": not errors,
        "stage_name": stage_name,
        "errors": errors,
    }


def validate_task_design(packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append({"code": code, "path": path, "message": message})

    stage_packet = packet.get("stage_packet", packet)
    task_design = stage_packet.get("task_design") if isinstance(stage_packet, dict) else None
    if not isinstance(task_design, dict):
        error("task_design.shape", "task_design", "task_design must be an object")
        task_design = {}

    _require_non_empty_value(task_design, "problem_definition", "task_design.problem_definition", error)
    _require_non_empty_list(task_design, "assumptions", "task_design.assumptions", error)
    _require_non_empty_list(task_design, "comparison_criteria", "task_design.comparison_criteria", error)
    _require_non_empty_value(task_design, "selected_option_id", "task_design.selected_option_id", error)
    _require_non_empty_value(task_design, "selection_rationale", "task_design.selection_rationale", error)
    _require_non_empty_list(task_design, "selected_option_risks", "task_design.selected_option_risks", error)
    _require_non_empty_list(task_design, "distribution_boundaries", "task_design.distribution_boundaries", error)
    _validate_artifact_profile(task_design.get("artifact_profile"), "task_design.artifact_profile", "task-designer", error)
    _validate_sequential_thinking_ref(task_design, "task_design.sequential_thinking_ref", error)

    options = task_design.get("options")
    if not isinstance(options, list) or len(options) < 3:
        error("task_design.options_count", "task_design.options", "task_design requires at least three options")
        options = [] if not isinstance(options, list) else options

    option_ids: set[str] = set()
    for index, option in enumerate(options):
        path = f"task_design.options[{index}]"
        if not isinstance(option, dict):
            error("task_design.option_shape", path, "option must be an object")
            continue
        option_id = option.get("id")
        if not isinstance(option_id, str) or not option_id:
            error("task_design.option_id", f"{path}.id", "option id is required")
        else:
            option_ids.add(option_id)
        _require_non_empty_value(option, "title", f"{path}.title", error)
        _require_non_empty_value(option, "summary", f"{path}.summary", error)
        _require_non_empty_value(option, "fit_assessment", f"{path}.fit_assessment", error)
        _require_non_empty_list(option, "tradeoffs", f"{path}.tradeoffs", error)

    selected_option_id = task_design.get("selected_option_id")
    if isinstance(selected_option_id, str) and option_ids and selected_option_id not in option_ids:
        error(
            "task_design.selected_option_missing",
            "task_design.selected_option_id",
            "selected_option_id must match one option id",
        )

    forbidden = ("execution_plan", "worker_lanes", "agent_selection", "worker_handoff_results")
    for field_name in forbidden:
        if field_name in task_design:
            error(
                "task_design.forbidden_output",
                f"task_design.{field_name}",
                f"task-designer must not emit {field_name}",
            )

    return {"valid": not errors, "artifact": "task_design", "errors": errors}


def validate_execution_plan(packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append({"code": code, "path": path, "message": message})

    stage_packet = packet.get("stage_packet", packet)
    execution_plan = stage_packet.get("execution_plan") if isinstance(stage_packet, dict) else None
    if not isinstance(execution_plan, dict):
        error("execution_plan.shape", "execution_plan", "execution_plan must be an object")
        execution_plan = {}

    _require_non_empty_value(execution_plan, "selected_task_design_ref", "execution_plan.selected_task_design_ref", error)
    criteria_ref = execution_plan.get("task_distribution_criteria_ref")
    if not isinstance(criteria_ref, str) or not criteria_ref:
        error(
            "execution_plan.criteria_ref",
            "execution_plan.task_distribution_criteria_ref",
            "task_distribution_criteria_ref is required",
        )
    elif not criteria_ref.lower().endswith(".md"):
        error(
            "execution_plan.criteria_ref_format",
            "execution_plan.task_distribution_criteria_ref",
            "task_distribution_criteria_ref must point to an MD artifact",
        )

    _require_non_empty_list(execution_plan, "distribution_principles", "execution_plan.distribution_principles", error)
    _require_non_empty_list(execution_plan, "worker_lanes", "execution_plan.worker_lanes", error)
    _require_non_empty_value(execution_plan, "fanout_budget", "execution_plan.fanout_budget", error)
    _validate_artifact_profile(execution_plan.get("artifact_profile"), "execution_plan.artifact_profile", "task-distributor", error)
    _validate_sequential_thinking_ref(execution_plan, "execution_plan.sequential_thinking_ref", error)

    lane_ids: set[str] = set()
    worker_lanes = execution_plan.get("worker_lanes", [])
    if isinstance(worker_lanes, list):
        for index, lane in enumerate(worker_lanes):
            path = f"execution_plan.worker_lanes[{index}]"
            if not isinstance(lane, dict):
                error("execution_plan.lane_shape", path, "worker lane must be an object")
                continue
            lane_id = lane.get("lane_id")
            if not isinstance(lane_id, str) or not lane_id:
                error("execution_plan.lane_id", f"{path}.lane_id", "lane_id is required")
            elif lane_id in lane_ids:
                error("execution_plan.lane_id_duplicate", f"{path}.lane_id", "lane_id must be unique")
            else:
                lane_ids.add(lane_id)
            _require_non_empty_value(lane, "purpose", f"{path}.purpose", error)
            _require_non_empty_value(lane, "specialist_category", f"{path}.specialist_category", error)
            _require_non_empty_list(lane, "input_artifacts", f"{path}.input_artifacts", error)
            _require_non_empty_list(lane, "expected_outputs", f"{path}.expected_outputs", error)
            _require_non_empty_list(lane, "handoff_evidence", f"{path}.handoff_evidence", error)

    dependencies = execution_plan.get("dependencies", [])
    if dependencies is not None and not isinstance(dependencies, list):
        error("execution_plan.dependencies_shape", "execution_plan.dependencies", "dependencies must be a list")
    elif isinstance(dependencies, list):
        for index, dependency in enumerate(dependencies):
            path = f"execution_plan.dependencies[{index}]"
            if not isinstance(dependency, dict):
                error("execution_plan.dependency_shape", path, "dependency must be an object")
                continue
            before = dependency.get("before")
            after = dependency.get("after")
            if before not in lane_ids:
                error("execution_plan.dependency_before", f"{path}.before", "dependency before must match a lane_id")
            if after not in lane_ids:
                error("execution_plan.dependency_after", f"{path}.after", "dependency after must match a lane_id")

    forbidden = ("task_design", "design_decisions", "selected_option_rationale")
    for field_name in forbidden:
        if field_name in execution_plan:
            error(
                "execution_plan.forbidden_output",
                f"execution_plan.{field_name}",
                f"task-distributor must not emit {field_name}",
            )

    return {"valid": not errors, "artifact": "execution_plan", "errors": errors}


def validate_review_plan(packet: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append({"code": code, "path": path, "message": message})

    stage_packet = packet.get("stage_packet", packet)
    review_plan = stage_packet.get("review_plan") if isinstance(stage_packet, dict) else None
    if not isinstance(review_plan, dict):
        error("review_plan.shape", "review_plan", "review_plan must be an object")
        review_plan = {}

    _require_non_empty_value(review_plan, "worker_handoff_results_ref", "review_plan.worker_handoff_results_ref", error)
    criteria_ref = review_plan.get("review_distribution_criteria_ref")
    if not isinstance(criteria_ref, str) or not criteria_ref:
        error(
            "review_plan.criteria_ref",
            "review_plan.review_distribution_criteria_ref",
            "review_distribution_criteria_ref is required",
        )
    elif not criteria_ref.lower().endswith(".md"):
        error(
            "review_plan.criteria_ref_format",
            "review_plan.review_distribution_criteria_ref",
            "review_distribution_criteria_ref must point to an MD artifact",
        )

    _require_non_empty_list(review_plan, "review_principles", "review_plan.review_principles", error)
    _require_non_empty_list(review_plan, "review_lanes", "review_plan.review_lanes", error)
    _require_non_empty_value(review_plan, "coverage_contract", "review_plan.coverage_contract", error)
    _validate_artifact_profile(review_plan.get("artifact_profile"), "review_plan.artifact_profile", "review-distributor", error)
    _validate_sequential_thinking_ref(review_plan, "review_plan.sequential_thinking_ref", error)

    lane_ids: set[str] = set()
    review_lanes = review_plan.get("review_lanes", [])
    if isinstance(review_lanes, list):
        for index, lane in enumerate(review_lanes):
            path = f"review_plan.review_lanes[{index}]"
            if not isinstance(lane, dict):
                error("review_plan.lane_shape", path, "review lane must be an object")
                continue
            lane_id = lane.get("lane_id")
            if not isinstance(lane_id, str) or not lane_id:
                error("review_plan.lane_id", f"{path}.lane_id", "lane_id is required")
            elif lane_id in lane_ids:
                error("review_plan.lane_id_duplicate", f"{path}.lane_id", "lane_id must be unique")
            else:
                lane_ids.add(lane_id)
            _require_non_empty_value(lane, "purpose", f"{path}.purpose", error)
            _require_non_empty_value(lane, "reviewer_category", f"{path}.reviewer_category", error)
            _require_non_empty_list(lane, "input_artifacts", f"{path}.input_artifacts", error)
            _require_non_empty_list(lane, "required_findings", f"{path}.required_findings", error)
            _require_non_empty_list(lane, "handoff_evidence", f"{path}.handoff_evidence", error)

    forbidden = ("execution_plan", "task_design", "worker_handoff_results", "judgment_envelope")
    for field_name in forbidden:
        if field_name in review_plan:
            error(
                "review_plan.forbidden_output",
                f"review_plan.{field_name}",
                f"review-distributor must not emit {field_name}",
            )

    return {"valid": not errors, "artifact": "review_plan", "errors": errors}


def _expected_next_owner(stage_name: str, packet: dict[str, Any]) -> str:
    if stage_name == "orchestrator" and _is_express_direct_handoff(packet):
        return DIRECT_WORKFLOW_OWNER
    if stage_name == "context-ledger":
        decision = packet.get("task_design_reentry_decision")
        context_packet = packet.get("context_packet")
        if decision is None and isinstance(context_packet, dict):
            decision = context_packet.get("task_design_reentry_decision")
        if isinstance(decision, dict) and decision.get("action") in {"reuse_task_design", "skip_to_distribution"}:
            return "task-distributor"
        if isinstance(decision, dict) and decision.get("action") == "revise_task_design":
            return "task-designer"
    if stage_name == "feedbackgate":
        judgment = packet.get("judgment_envelope", packet)
        if isinstance(judgment, dict) and judgment.get("feedback_required") is True:
            return "orchestrator"
        return "final"
    return NEXT_OWNER.get(stage_name, "unknown")


def build_next_stage_guidance(next_owner: str) -> dict[str, Any]:
    if next_owner == DIRECT_WORKFLOW_OWNER:
        guidance = STAGE_GUIDANCE[DIRECT_WORKFLOW_OWNER]
        return {
            "owner": DIRECT_WORKFLOW_OWNER,
            **guidance,
            "required_mcp_tools": [],
            "stage_packet_template": STAGE_PACKET_TEMPLATES["orchestrator_express_direct"],
            "action": (
                "exit the architecture stage chain and resume the normal direct workflow; "
                "do not spawn specialists or claim full architecture completion"
            ),
        }

    if next_owner == "final":
        return {
            "owner": "final",
            "activation_ref": None,
            "contract_ref": None,
            "source_docs": [],
            "required_input_artifacts": ["judgment_envelope", "feedback_gate_evidence"],
            "required_mcp_tools": [],
            "action": "emit final response only after feedbackgate completion evidence is valid",
        }

    guidance = STAGE_GUIDANCE.get(next_owner)
    if guidance is None:
        return {
            "owner": next_owner,
            "activation_ref": None,
            "contract_ref": None,
            "source_docs": [],
            "required_input_artifacts": [],
            "required_mcp_tools": [],
            "action": "block until next_owner is corrected to a known stage",
        }

    activation_ref = guidance["activation_ref"]
    return {
        "owner": next_owner,
        **guidance,
        "required_mcp_tools": list(REQUIRED_TOOL_SEQUENCE.get(next_owner, ())),
        "stage_packet_template": STAGE_PACKET_TEMPLATES.get(next_owner),
        "action": (
            f"activate {activation_ref}; read only its SKILL.md, adjacent contract.json, "
            "and the listed source_docs"
        ),
    }


def _is_express_direct_handoff(packet: dict[str, Any]) -> bool:
    request = packet.get("orchestration_request")
    if not isinstance(request, dict):
        request = {}

    next_owner = packet.get("next_owner", request.get("next_owner"))
    workflow_mode = packet.get("workflow_mode", request.get("workflow_mode"))
    architecture_required = packet.get("architecture_required", request.get("architecture_required"))
    request_architecture_required = request.get("architecture_required", architecture_required)
    complexity = packet.get("complexity_classification", request.get("complexity_classification"))

    return (
        next_owner == DIRECT_WORKFLOW_OWNER
        and workflow_mode == "express-direct"
        and architecture_required is False
        and request_architecture_required is False
        and complexity in {"simple", "direct", "low-risk"}
    )


def _extend_errors(validation: dict[str, Any], errors: list[dict[str, str]]) -> None:
    if validation.get("valid"):
        return
    for item in validation.get("errors", []):
        if isinstance(item, dict):
            errors.append(item)


def _require_non_empty_value(source: dict[str, Any], field_name: str, path: str, error) -> bool:
    value = source.get(field_name)
    if value is None or value == "":
        error(f"{path}.missing", path, f"{field_name} is required")
        return False
    return True


def _require_non_empty_list(source: dict[str, Any], field_name: str, path: str, error) -> bool:
    value = source.get(field_name)
    if not isinstance(value, list) or len(value) == 0:
        error(f"{path}.missing", path, f"{field_name} must be a non-empty list")
        return False
    return True


def _validate_artifact_profile(value: Any, path: str, expected_source_stage: str, error) -> bool:
    if not isinstance(value, dict):
        error(f"{path}.shape", path, "artifact_profile must be an object")
        return False

    valid = True
    if not isinstance(value.get("version"), int):
        error(f"{path}.version", f"{path}.version", "version must be an integer")
        valid = False
    if value.get("source_stage") != expected_source_stage:
        error(
            f"{path}.source_stage",
            f"{path}.source_stage",
            f"source_stage must be {expected_source_stage}",
        )
        valid = False
    if not value.get("reuse_policy"):
        error(f"{path}.reuse_policy", f"{path}.reuse_policy", "reuse_policy is required")
        valid = False
    invalidated_by = value.get("invalidated_by")
    if not isinstance(invalidated_by, list) or not invalidated_by:
        error(f"{path}.invalidated_by", f"{path}.invalidated_by", "invalidated_by must be a non-empty list")
        valid = False
    return valid


def _validate_sequential_thinking_ref(source: dict[str, Any], path: str, error) -> bool:
    value = source.get("sequential_thinking_ref")
    waiver = source.get("sequential_thinking_waiver")
    if value is None or value == "":
        return _validate_sequential_thinking_waiver(waiver, path, error)
    if not isinstance(value, (str, dict)):
        error(f"{path}.shape", path, "sequential_thinking_ref must be a non-empty string or evidence object")
        return False
    if isinstance(value, dict) and not value:
        error(f"{path}.shape", path, "sequential_thinking_ref must be a non-empty string or evidence object")
        return False
    return True


def _validate_sequential_thinking_waiver(value: Any, path: str, error) -> bool:
    waiver_path = path.rsplit(".", 1)[0] + ".sequential_thinking_waiver" if "." in path else "sequential_thinking_waiver"
    if not isinstance(value, dict):
        error(
            f"{path}.missing",
            path,
            "sequential_thinking_ref or sequential_thinking_waiver is required after MCP_DOCKER sequentialthinking attempt",
        )
        return False

    valid = True
    if value.get("status") not in {"tool_unavailable", "tool_error", "timeout"}:
        error(
            f"{waiver_path}.status",
            f"{waiver_path}.status",
            "status must be tool_unavailable, tool_error, or timeout",
        )
        valid = False
    for field_name in ("reason", "fallback_summary"):
        if not value.get(field_name):
            error(
                f"{waiver_path}.{field_name}",
                f"{waiver_path}.{field_name}",
                f"{field_name} is required",
            )
            valid = False
    return valid


def _validate_reentry_cache_if_present(stage_packet: dict[str, Any], error) -> bool:
    context_packet = stage_packet.get("context_packet")
    if not isinstance(context_packet, dict):
        return True

    decision = context_packet.get("task_design_reentry_decision")
    cache = context_packet.get("reentry_cache")
    if decision is None and cache is None:
        return True

    valid = True
    if not isinstance(cache, dict):
        error("reentry_cache.shape", "context_packet.reentry_cache", "reentry_cache must be an object on feedback loops")
        return False

    if not cache.get("task_design_ref"):
        error("reentry_cache.task_design_ref", "context_packet.reentry_cache.task_design_ref", "task_design_ref is required")
        valid = False
    for field_name in ("reusable_artifacts", "invalidated_artifacts"):
        value = cache.get(field_name)
        if not isinstance(value, list):
            error(
                f"reentry_cache.{field_name}",
                f"context_packet.reentry_cache.{field_name}",
                f"{field_name} must be a list",
            )
            valid = False
    if not cache.get("distribution_action"):
        error(
            "reentry_cache.distribution_action",
            "context_packet.reentry_cache.distribution_action",
            "distribution_action is required",
        )
        valid = False
    if not cache.get("review_distribution_action"):
        error(
            "reentry_cache.review_distribution_action",
            "context_packet.reentry_cache.review_distribution_action",
            "review_distribution_action is required",
        )
        valid = False
    return valid


def _non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _validate_non_empty_dict(
    field_name: str,
    value: Any,
    missing_code: str,
    missing_message: str,
    error,
) -> bool:
    if value is None or value == {}:
        error(missing_code, field_name, missing_message)
        return False
    if not isinstance(value, dict):
        error(f"completion.{field_name}.shape", field_name, "must be a non-empty object")
        return False
    return True


def _validate_non_empty_string_list(field_name: str, value: Any, error) -> bool:
    if value is None or value == []:
        return False
    if not isinstance(value, list):
        error(f"completion.{field_name}.shape", field_name, "must be a list")
        return False

    valid = True
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            error(f"completion.{field_name}.item", f"{field_name}[{index}]", "must be a non-empty string")
            valid = False
    return valid


def _validate_lane_reason_items(field_name: str, value: Any, error) -> bool:
    if value is None:
        return False
    if not isinstance(value, list):
        error(f"completion.{field_name}.shape", field_name, "must be a list")
        return False

    valid_items = 0
    for index, item in enumerate(value):
        path = f"{field_name}[{index}]"
        if not isinstance(item, dict):
            error(f"completion.{field_name}.item_shape", path, "must be an object")
            continue
        has_lane_id = bool(item.get("lane_id"))
        has_reason = bool(item.get("reason"))
        if not has_lane_id:
            error(f"completion.{field_name}.lane_id", f"{path}.lane_id", "lane_id is required")
        if not has_reason:
            error(f"completion.{field_name}.reason", f"{path}.reason", "reason is required")
        if has_lane_id and has_reason:
            valid_items += 1

    return valid_items > 0


def _validate_task_design_reentry_decision(value: Any, error) -> bool:
    if not isinstance(value, dict):
        error(
            "completion.task_design_reentry_decision.shape",
            "judgment_envelope.task_design_reentry_decision",
            "feedback loops require task_design_reentry_decision",
        )
        return False

    action = value.get("action")
    allowed_actions = {"revise_task_design", "reuse_task_design", "skip_to_distribution"}
    valid = True
    if action not in allowed_actions:
        error(
            "completion.task_design_reentry_decision.action",
            "judgment_envelope.task_design_reentry_decision.action",
            "action must be revise_task_design, reuse_task_design, or skip_to_distribution",
        )
        valid = False
    if not value.get("reason"):
        error(
            "completion.task_design_reentry_decision.reason",
            "judgment_envelope.task_design_reentry_decision.reason",
            "reason is required",
        )
        valid = False
    if action in {"reuse_task_design", "skip_to_distribution"} and not value.get("task_design_ref"):
        error(
            "completion.task_design_reentry_decision.task_design_ref",
            "judgment_envelope.task_design_reentry_decision.task_design_ref",
            "task_design_ref is required when reusing or skipping task design",
        )
        valid = False
    for field_name in ("reusable_artifacts", "invalidated_artifacts"):
        field_value = value.get(field_name)
        if not isinstance(field_value, list):
            error(
                f"completion.task_design_reentry_decision.{field_name}",
                f"judgment_envelope.task_design_reentry_decision.{field_name}",
                f"{field_name} must be a list",
            )
            valid = False
    allowed_distribution_actions = {"reuse_execution_plan", "revise_execution_plan", "skip_distribution"}
    if value.get("distribution_action") not in allowed_distribution_actions:
        error(
            "completion.task_design_reentry_decision.distribution_action",
            "judgment_envelope.task_design_reentry_decision.distribution_action",
            "distribution_action must be reuse_execution_plan, revise_execution_plan, or skip_distribution",
        )
        valid = False
    allowed_review_actions = {"reuse_review_criteria", "revise_review_plan", "skip_review_distribution"}
    if value.get("review_distribution_action") not in allowed_review_actions:
        error(
            "completion.task_design_reentry_decision.review_distribution_action",
            "judgment_envelope.task_design_reentry_decision.review_distribution_action",
            "review_distribution_action must be reuse_review_criteria, revise_review_plan, or skip_review_distribution",
        )
        valid = False
    return valid


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
            if not item.get("wait_handle"):
                error("handoff.wait_handle", f"{path}.wait_handle", "wait_handle is required")
            if not item.get("wait_agent_evidence"):
                error("handoff.wait_agent_evidence", f"{path}.wait_agent_evidence", "wait_agent evidence is required")
