#!/usr/bin/env python3
"""Validate concrete runtime artifacts emitted by the Codex harness.

`validate-agent-architecture.py` checks static architecture files. This script
checks the actual JSON object returned by a stage before the caller hands it to
the next stage. Non-zero exit means the caller must not continue the handoff.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from validators.constants import (
    ACTIVE_PASSES_REQUIRED_FIELDS,
    AGGREGATION_PACKET_REQUIRED_FIELDS,
    BOUNDED_REWORK_REQUEST_REQUIRED_FIELDS,
    CANONICAL_STAGE_ROLES,
    CONFIDENCE_LEVELS,
    CONTRACT_PROVENANCE_REQUIRED_FIELDS,
    CONTEXT_PACKET_REQUIRED_FIELDS,
    EXECUTION_PLAN_LANE_REQUIRED_FIELDS,
    EXECUTION_PLAN_REQUIRED_FIELDS,
    EXPECTED_AGENT_CATEGORIES,
    FANOUT_BUDGET_REQUIRED_FIELDS,
    FEEDBACK_TARGET_REENTRY,
    HANDOFF_RESULT_REQUIRED_FIELDS,
    JUDGMENT_ALLOWED_DECISIONS,
    JUDGMENT_ALLOWED_LOOP_STAGES,
    JUDGMENT_ENVELOPE_REQUIRED_FIELDS,
    LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS,
    LOGICAL_LANE_REQUIRED_FIELDS,
    LOOP_CARRYOVER_REQUIRED_FIELDS,
    LOOP_CONTROL_REQUIRED_FIELDS,
    MISSING_LANE_CLASSES,
    ORCHESTRATION_REQUEST_REQUIRED_FIELDS,
    PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS,
    PASS_STATUSES,
    PROGRESS_DELTA_REQUIRED_FIELDS,
    REVIEW_COVERAGE_REQUIRED_FIELDS,
    REVIEW_LAUNCH_MANIFEST_REQUIRED_FIELDS,
    REVIEW_LANE_ALLOWED_CATEGORIES,
    REVIEW_LANE_ALLOWED_ROLES,
    REVIEW_WAIVER_REQUIRED_FIELDS,
    RUN_LEDGER_REQUIRED_FIELDS,
    SCHEMA_INVALID_REQUIRED_FIELDS,
    SPAWN_CONTEXT_MODES,
    STAGE_PASS_REQUIRED_FIELDS,
    WORKER_LAUNCH_MANIFEST_REQUIRED_FIELDS,
)

ARTIFACT_KEYS = (
    "orchestration_request",
    "context_packet",
    "execution_plan",
    "launch_manifest",
    "schema_invalid",
    "active_pass",
    "active_passes",
    "stage_pass",
    "handoff_result",
    "aggregation_packet",
    "judgment_envelope",
    "run_ledger",
)
ARTIFACT_CHOICES = ("auto", "blocked_aggregation") + ARTIFACT_KEYS

STAGE_ARTIFACTS = {
    "orchestrator": {"orchestration_request"},
    "context-manager": {"context_packet"},
    "task-planner": {"execution_plan"},
    "worker-router": {"launch_manifest", "schema_invalid"},
    "worker-layer": {"handoff_result"},
    "aggregator": {"aggregation_packet", "blocked_aggregation"},
    "review-router": {"launch_manifest", "schema_invalid"},
    "review-layer": {"handoff_result"},
    "meta-judge": {"judgment_envelope"},
}

MCP_TOOL_REQUEST_KEYS = {"mcp_tool_request", "mcp_tool_requests"}
MCP_TOOL_REQUEST_REQUIRED_FIELDS = {
    "tool_name",
    "arguments",
    "purpose",
    "evidence_slot",
    "fallback_blocker",
}
MCP_TOOL_REQUEST_FORBIDDEN_FIELDS = {
    "command",
    "args",
    "env",
    "cwd",
    "server_command",
    "server_args",
    "profile_activation",
    "mcp_server_config",
}
DOCKER_MCP_SEQUENTIALTHINKING_REQUIRED_STAGES = {
    "orchestrator",
    "context-manager",
    "aggregator",
    "review-router",
    "review-layer",
    "meta-judge",
}
DOCKER_MCP_SEQUENTIALTHINKING_REQUIRED_MARKER = "docker_mcp_sequentialthinking_required=true"
DOCKER_MCP_SEQUENTIALTHINKING_EVIDENCE_MARKER = "MCP_DOCKER/sequentialthinking:success"
MCP_QUIESCENCE_REQUIRED_STAGES = {
    "orchestrator",
    "context-manager",
    "task-planner",
    "worker-router",
    "worker-layer",
    "aggregator",
    "review-router",
    "review-layer",
    "meta-judge",
}
MCP_QUIESCENCE_REQUIRED_FIELDS = {
    "open_mcp_process_count",
    "open_mcp_process_ids",
    "cleanup_status",
    "snapshot_at",
}

STAGE_NEXT_OWNER = {
    ("orchestrator", "orchestration_request"): "context-manager",
    ("context-manager", "context_packet"): "task-planner",
    ("task-planner", "execution_plan"): "worker-router",
    ("worker-layer", "handoff_result"): "aggregator",
    ("aggregator", "aggregation_packet"): "review-router",
    ("aggregator", "blocked_aggregation"): "meta-judge",
    ("review-layer", "handoff_result"): "meta-judge",
}

WAIT_HANDLE_TYPES = {"agent_id", "submission_id"}
SCHEMA_STATUSES = {"valid", "invalid", "schema_invalid"}
CONTROL_STAGE_SPAWN_PACKET_MODES = {"curated_stage_packet", "full_history_inherit", "main_agent_role_pass"}


@lru_cache(maxsize=1)
def agent_catalog() -> dict[str, set[str]]:
    root = Path(__file__).resolve().parents[1] / "agents"
    catalog: dict[str, set[str]] = {}
    for category in EXPECTED_AGENT_CATEGORIES:
        category_path = root / category
        catalog[category] = {path.stem for path in category_path.glob("*.toml")} if category_path.is_dir() else set()
    return catalog


@dataclass
class ValidationState:
    artifact_type: str = "unknown"
    next_owner: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def error(self, code: str, path: str, message: str) -> None:
        self.errors.append({"code": code, "path": path, "message": message})

    def warning(self, code: str, path: str, message: str) -> None:
        self.warnings.append({"code": code, "path": path, "message": message})

    def result(self) -> dict[str, Any]:
        ok = not self.errors
        return {
            "validation_status": "passed" if ok else "failed",
            "artifact_type": self.artifact_type,
            "schema_status": "valid" if ok else "invalid",
            "failure_class": "none" if ok else failure_class(self.errors),
            "next_owner": self.next_owner,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_json(path: str | None) -> Any:
    if path in (None, "-"):
        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def failure_class(errors: list[dict[str, str]]) -> str:
    if any(item["code"].startswith("json.") for item in errors):
        return "input_invalid"
    if any(item["code"].startswith("io.") for item in errors):
        return "io_error"
    if any(item["code"].startswith("runtime_validator.exception") for item in errors):
        return "validator_bug"
    if any(".loop_control." in item["path"] or ".loop_carryover." in item["path"] for item in errors):
        return "loop_invalid"
    if any(item["code"].startswith("stage.") for item in errors):
        return "contract_invalid"
    return "schema_invalid"


def validate_payload(payload: Any, *, artifact: str = "auto", stage_owner: str | None = None) -> dict[str, Any]:
    state = ValidationState()
    if isinstance(payload, dict):
        state.next_owner = payload.get("next_owner")
    artifact_type, value = extract_artifact(payload, artifact, state)
    state.artifact_type = artifact_type
    validate_artifact(value, artifact_type, state)
    if stage_owner:
        validate_stage_handoff(payload, value, artifact_type, stage_owner, state)
    return state.result()


def extract_artifact(payload: Any, requested: str, state: ValidationState) -> tuple[str, Any]:
    if requested != "auto":
        if requested == "active_passes":
            return requested, payload
        if isinstance(payload, dict) and requested in payload:
            return requested, payload[requested]
        return requested, payload
    if not isinstance(payload, dict):
        return "unknown", payload
    if payload.get("aggregation_ready") is False:
        return "blocked_aggregation", payload
    present = [key for key in ARTIFACT_KEYS if key in payload]
    if len(present) == 1:
        return present[0], payload[present[0]]
    if len(present) > 1:
        state.error("artifact.multiple", "$", f"multiple artifact keys: {present}")
        return present[0], payload[present[0]]
    return detect_raw_artifact(payload), payload


def detect_raw_artifact(value: dict[str, Any]) -> str:
    markers = (
        ("launch_manifest", {"manifest_kind", "children"}),
        ("schema_invalid", {"missing_fields", "forbidden_fields", "parent_router_pass_id"}),
        ("judgment_envelope", {"decision", "feedback_required", "feedback_target"}),
        ("aggregation_packet", {"normalized_claims", "source_launch_manifest_ref"}),
        ("execution_plan", {"wave_id", "lanes", "source_context_packet_ref"}),
        ("context_packet", {"source_orchestration_request_ref", "approved_facts"}),
        ("orchestration_request", {"run_id", "loop_id", "user_goal", "feedback_reentry"}),
        ("active_passes", {"active_passes"}),
        ("active_pass", {"wait_handle_type", "wait_handle", "agent_id"}),
        ("stage_pass", {"stage_pass_id", "stage_owner", "stage_status"}),
        ("handoff_result", {"sender", "pass_status", "artifact_ref"}),
        ("run_ledger", {"stage_artifact_name", "stage_artifact_ref", "schema_status"}),
    )
    keys = set(value)
    for name, required in markers:
        if required <= keys:
            return name
    return "unknown"


def validate_stage_handoff(wrapper: Any, value: Any, artifact_type: str, stage_owner: str, state: ValidationState) -> None:
    allowed = STAGE_ARTIFACTS.get(stage_owner)
    if allowed is None:
        state.error("stage.unknown", "stage_owner", f"unknown stage owner {stage_owner}")
        return
    if artifact_type not in allowed:
        state.error("stage.artifact", "$", f"{stage_owner} cannot emit {artifact_type}")
    if stage_owner == "worker-router" and artifact_type == "launch_manifest":
        if not isinstance(value, dict) or value.get("manifest_kind") != "worker":
            state.error("stage.manifest_kind", "launch_manifest.manifest_kind", "worker-router must emit worker manifest")
    if stage_owner == "review-router" and artifact_type == "launch_manifest":
        if not isinstance(value, dict) or value.get("manifest_kind") != "review":
            state.error("stage.manifest_kind", "launch_manifest.manifest_kind", "review-router must emit review manifest")
    expected_next = STAGE_NEXT_OWNER.get((stage_owner, artifact_type))
    if expected_next is not None and isinstance(wrapper, dict) and "next_owner" in wrapper:
        if wrapper.get("next_owner") != expected_next:
            state.error("stage.next_owner", "$.next_owner", f"expected {expected_next!r}, got {wrapper.get('next_owner')!r}")
    validate_docker_mcp_sequentialthinking(stage_owner, value, artifact_type, state)
    validate_mcp_quiescence(stage_owner, value, artifact_type, state)


def validate_artifact(value: Any, artifact_type: str, state: ValidationState) -> None:
    if artifact_type == "unknown":
        state.error("artifact.unknown", "$", "cannot detect artifact type")
        return
    dispatch = {
        "orchestration_request": validate_orchestration_request,
        "context_packet": validate_context_packet,
        "execution_plan": validate_execution_plan,
        "launch_manifest": validate_launch_manifest,
        "schema_invalid": validate_schema_invalid,
        "active_pass": validate_active_pass,
        "active_passes": validate_active_passes,
        "stage_pass": validate_stage_pass,
        "handoff_result": validate_handoff_result,
        "aggregation_packet": validate_aggregation_packet,
        "blocked_aggregation": validate_blocked_aggregation,
        "judgment_envelope": validate_judgment_envelope,
        "run_ledger": validate_run_ledger,
    }
    dispatch[artifact_type](value, artifact_type, state)
    validate_embedded_mcp_tool_requests(value, artifact_type, state)


def validate_embedded_mcp_tool_requests(value: Any, path: str, state: ValidationState) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            if key in MCP_TOOL_REQUEST_KEYS:
                validate_mcp_tool_request_container(item, item_path, state)
            else:
                validate_embedded_mcp_tool_requests(item, item_path, state)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_embedded_mcp_tool_requests(item, f"{path}[{index}]", state)


def validate_mcp_tool_request_container(value: Any, path: str, state: ValidationState) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_single_mcp_tool_request(item, f"{path}[{index}]", state)
        return
    validate_single_mcp_tool_request(value, path, state)


def validate_single_mcp_tool_request(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, MCP_TOOL_REQUEST_REQUIRED_FIELDS, path, state)
    forbid_fields(value, MCP_TOOL_REQUEST_FORBIDDEN_FIELDS, path, state)
    if not isinstance(value.get("arguments"), dict):
        state.error("mcp_tool_request.arguments", f"{path}.arguments", "expected object")
    for field_name in ("tool_name", "purpose", "evidence_slot", "fallback_blocker"):
        if not isinstance(value.get(field_name), str) or not value.get(field_name):
            state.error("mcp_tool_request.required_string", f"{path}.{field_name}", "expected non-empty string")


def validate_mcp_quiescence(stage_owner: str, value: Any, artifact_type: str, state: ValidationState) -> None:
    if stage_owner not in MCP_QUIESCENCE_REQUIRED_STAGES:
        return
    snapshot = find_first_key(value, "mcp_quiescence_snapshot")
    path = f"{artifact_type}.mcp_quiescence_snapshot"
    if snapshot is None:
        state.error("mcp_quiescence_snapshot.missing", artifact_type, "mcp_quiescence_snapshot is required before handoff")
        return
    if not object_ok(snapshot, path, state):
        return
    require_fields(snapshot, MCP_QUIESCENCE_REQUIRED_FIELDS, path, state)
    count = snapshot.get("open_mcp_process_count")
    if not isinstance(count, int):
        state.error("mcp_quiescence_snapshot.count", f"{path}.open_mcp_process_count", "expected integer")
    elif count != 0:
        state.error("mcp_quiescence_snapshot.residue", f"{path}.open_mcp_process_count", "expected 0 open MCP processes")
    process_ids = snapshot.get("open_mcp_process_ids")
    if not isinstance(process_ids, list):
        state.error("mcp_quiescence_snapshot.process_ids", f"{path}.open_mcp_process_ids", "expected list")
    elif process_ids:
        state.error("mcp_quiescence_snapshot.process_ids", f"{path}.open_mcp_process_ids", "expected no open MCP process ids")
    if snapshot.get("cleanup_status") != "clean":
        state.error("mcp_quiescence_snapshot.cleanup_status", f"{path}.cleanup_status", "expected clean")


def find_first_key(value: Any, key_name: str) -> Any:
    if isinstance(value, dict):
        if key_name in value:
            return value[key_name]
        for item in value.values():
            found = find_first_key(item, key_name)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_first_key(item, key_name)
            if found is not None:
                return found
    return None


def validate_docker_mcp_sequentialthinking(stage_owner: str, value: Any, artifact_type: str, state: ValidationState) -> None:
    if stage_owner not in DOCKER_MCP_SEQUENTIALTHINKING_REQUIRED_STAGES:
        return
    strings = list(iter_string_values(value))
    has_required_marker = any(DOCKER_MCP_SEQUENTIALTHINKING_REQUIRED_MARKER in item for item in strings)
    has_evidence_marker = any(DOCKER_MCP_SEQUENTIALTHINKING_EVIDENCE_MARKER in item for item in strings)
    if not has_required_marker:
        state.error(
            "docker_mcp_sequentialthinking.required_marker",
            artifact_type,
            f"{stage_owner} requires {DOCKER_MCP_SEQUENTIALTHINKING_REQUIRED_MARKER}",
        )
    if not has_evidence_marker:
        state.error(
            "docker_mcp_sequentialthinking.evidence",
            artifact_type,
            f"{stage_owner} requires evidence naming {DOCKER_MCP_SEQUENTIALTHINKING_EVIDENCE_MARKER}",
        )


def iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from iter_string_values(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from iter_string_values(item)


def validate_orchestration_request(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, ORCHESTRATION_REQUEST_REQUIRED_FIELDS, path, state)
    bool_ok(value.get("direct_answer_exception"), f"{path}.direct_answer_exception", state)
    list_ok(value.get("validation_evidence"), f"{path}.validation_evidence", state)
    validate_loop_carryover(value.get("loop_carryover"), f"{path}.loop_carryover", state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)


def validate_context_packet(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, CONTEXT_PACKET_REQUIRED_FIELDS, path, state)
    expect_equal(value.get("next_stage_consumer"), "task-planner", f"{path}.next_stage_consumer", state)
    for field_name in ("context_authority_ref", "context_packet_version", "context_revision"):
        if not isinstance(value.get(field_name), str) or not value.get(field_name):
            state.error("context_packet.context_authority", f"{path}.{field_name}", "MCP-backed context authority fields must be non-empty strings")
    readiness = value.get("role_pass_readiness")
    if object_ok(readiness, f"{path}.role_pass_readiness", state):
        require_fields(readiness, {"allowed_role_passes", "refresh_required_for", "readiness_reason"}, f"{path}.role_pass_readiness", state)
        for field_name in ("allowed_role_passes", "refresh_required_for"):
            list_ok(readiness.get(field_name), f"{path}.role_pass_readiness.{field_name}", state)
    validate_loop_carryover(value.get("loop_carryover"), f"{path}.loop_carryover", state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)


def validate_execution_plan(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, EXECUTION_PLAN_REQUIRED_FIELDS, path, state)
    lanes = value.get("lanes")
    list_ok(lanes, f"{path}.lanes", state)
    if isinstance(lanes, list):
        for index, lane in enumerate(lanes):
            lane_path = f"{path}.lanes[{index}]"
            if object_ok(lane, lane_path, state):
                require_fields(lane, EXECUTION_PLAN_LANE_REQUIRED_FIELDS, lane_path, state)
    validate_fanout_budget(value.get("fanout_budget"), f"{path}.fanout_budget", state)
    if isinstance(lanes, list) and isinstance(value.get("fanout_budget"), dict):
        max_worker = value["fanout_budget"].get("max_worker_lanes_per_wave")
        if isinstance(max_worker, int) and len(lanes) > max_worker:
            state.error("fanout.worker_budget_exceeded", f"{path}.lanes", f"{len(lanes)} lanes exceed max_worker_lanes_per_wave={max_worker}")
    validate_loop_carryover(value.get("loop_carryover"), f"{path}.loop_carryover", state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)


def validate_launch_manifest(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    kind = value.get("manifest_kind")
    if kind == "worker":
        required = WORKER_LAUNCH_MANIFEST_REQUIRED_FIELDS
    elif kind == "review":
        required = REVIEW_LAUNCH_MANIFEST_REQUIRED_FIELDS
    else:
        required = WORKER_LAUNCH_MANIFEST_REQUIRED_FIELDS | REVIEW_LAUNCH_MANIFEST_REQUIRED_FIELDS
        state.error("launch_manifest.kind", f"{path}.manifest_kind", "expected worker or review")
    require_fields(value, required, path, state)
    expect_equal(value.get("schema_status"), "valid", f"{path}.schema_status", state)
    if kind == "worker":
        expect_equal(value.get("source_parent_ref"), value.get("source_execution_plan_ref"), f"{path}.source_parent_ref", state)
        forbid_fields(value, {"source_aggregation_packet_ref"}, path, state)
    if kind == "review":
        expect_equal(value.get("source_parent_ref"), value.get("source_aggregation_packet_ref"), f"{path}.source_parent_ref", state)
        forbid_fields(value, {"source_execution_plan_ref"}, path, state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)
    children = value.get("children")
    list_ok(children, f"{path}.children", state)
    if not isinstance(children, list):
        return
    budget = value.get("fanout_budget")
    if isinstance(budget, dict):
        budget_key = "max_worker_lanes_per_wave" if kind == "worker" else "max_review_lanes_per_wave"
        max_children = budget.get(budget_key)
        if isinstance(max_children, int) and len(children) > max_children:
            state.error("fanout.launch_budget_exceeded", f"{path}.children", f"{len(children)} children exceed {budget_key}={max_children}")
    seen: set[str] = set()
    merge_keys: set[tuple[Any, Any, Any, Any]] = set()
    role_counts: dict[Any, int] = {}
    for index, lane in enumerate(children):
        lane_path = f"{path}.children[{index}]"
        if not object_ok(lane, lane_path, state):
            continue
        require_fields(lane, LOGICAL_LANE_REQUIRED_FIELDS, lane_path, state)
        forbid_fields(lane, LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS, lane_path, state)
        expect_equal(lane.get("caller_spawn_required"), True, f"{lane_path}.caller_spawn_required", state)
        expect_equal(lane.get("initial_status"), "unmaterialized", f"{lane_path}.initial_status", state)
        if lane.get("spawn_context_mode") not in SPAWN_CONTEXT_MODES:
            state.error(
                "launch_manifest.spawn_context_mode",
                f"{lane_path}.spawn_context_mode",
                f"must be one of {sorted(SPAWN_CONTEXT_MODES)}",
            )
        if lane.get("lane_type") in {"worker", "review"}:
            if lane.get("spawn_context_mode") == "fork_context":
                state.error("launch_manifest.specialist_context_mode", f"{lane_path}.spawn_context_mode", "specialist lanes cannot use fork_context")
            if lane.get("spawn_context_mode") == "scoped_packet_with_waiver":
                waiver = lane.get("spawn_context_waiver")
                if not isinstance(waiver, dict):
                    state.error("launch_manifest.context_waiver_missing", f"{lane_path}.spawn_context_waiver", "scoped_packet_with_waiver requires a waiver object")
                else:
                    require_fields(waiver, {"reason", "risk", "review_axis", "evidence_ref"}, f"{lane_path}.spawn_context_waiver", state)
        validate_lane_dependency(lane, kind, lane_path, state)
        expect_equal(lane.get("context_packet_version"), value.get("context_packet_version"), f"{lane_path}.context_packet_version", state)
        if kind == "worker":
            expect_equal(lane.get("lane_type"), "worker", f"{lane_path}.lane_type", state)
            expect_equal(lane.get("return_owner"), "aggregator", f"{lane_path}.return_owner", state)
        if kind == "review":
            expect_equal(lane.get("lane_type"), "review", f"{lane_path}.lane_type", state)
            expect_equal(lane.get("return_owner"), "meta-judge", f"{lane_path}.return_owner", state)
        lane_id = str(lane.get("lane_id"))
        if lane_id in seen:
            state.error("launch_manifest.duplicate_lane", lane_path, f"duplicate lane_id {lane_id}")
        seen.add(lane_id)
        merge_key = (lane.get("owned_scope"), lane.get("expected_artifact"), lane.get("merge_point"), lane.get("context_packet_version"))
        if merge_key in merge_keys:
            state.error("launch_manifest.merge_overlap", lane_path, "parallel lanes collapse onto the same merge contract")
        merge_keys.add(merge_key)
        role_counts[lane.get("agent_role")] = role_counts.get(lane.get("agent_role"), 0) + 1
    if isinstance(budget, dict):
        max_same_role = budget.get("max_same_role_parallel_lanes")
        if isinstance(max_same_role, int):
            for role, count in role_counts.items():
                if count > max_same_role:
                    state.error("fanout.same_role_budget_exceeded", f"{path}.children", f"{count} lanes for role {role!r} exceed max_same_role_parallel_lanes={max_same_role}")


def validate_lane_dependency(lane: dict[str, Any], kind: Any, path: str, state: ValidationState) -> None:
    category = lane.get("agent_category")
    role = lane.get("agent_role")
    if not isinstance(category, str) or category not in EXPECTED_AGENT_CATEGORIES:
        state.error("launch_manifest.agent_category", f"{path}.agent_category", f"unknown category: {category!r}")
        return
    if not isinstance(role, str) or not role:
        state.error("launch_manifest.agent_role", f"{path}.agent_role", "agent_role must be a non-empty string")
        return
    roles = agent_catalog().get(category, set())
    if role not in roles:
        state.error("launch_manifest.agent_role_missing", f"{path}.agent_role", f"{category}/{role}.toml does not exist")
    if role in CANONICAL_STAGE_ROLES:
        state.error("launch_manifest.stage_role_dependency", f"{path}.agent_role", "canonical stage owners cannot be materialized as specialist lanes")
    if kind == "review" and category not in REVIEW_LANE_ALLOWED_CATEGORIES and role not in REVIEW_LANE_ALLOWED_ROLES:
        state.error("launch_manifest.review_role_dependency", f"{path}.agent_role", "review lanes must use reviewer or review-support specialist roles")


def validate_fanout_budget(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, FANOUT_BUDGET_REQUIRED_FIELDS, path, state)
    for field_name in (
        "max_worker_lanes_per_wave",
        "max_review_lanes_per_wave",
        "max_total_child_agents_per_loop",
        "max_same_role_parallel_lanes",
        "max_mcp_concurrent_child_lanes",
    ):
        item = value.get(field_name)
        if not isinstance(item, int) or item < 1:
            state.error("fanout.invalid_limit", f"{path}.{field_name}", "fanout limits must be positive integers")
    total = value.get("max_total_child_agents_per_loop")
    workers = value.get("max_worker_lanes_per_wave")
    reviewers = value.get("max_review_lanes_per_wave")
    if isinstance(total, int) and isinstance(workers, int) and isinstance(reviewers, int) and workers + reviewers > total:
        state.error("fanout.total_budget_exceeded", path, "worker plus reviewer wave limits exceed max_total_child_agents_per_loop")


def validate_schema_invalid(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, SCHEMA_INVALID_REQUIRED_FIELDS, path, state)
    if value.get("manifest_kind") not in {"worker", "review"}:
        state.error("schema_invalid.kind", f"{path}.manifest_kind", "expected worker or review")
    for field_name in ("lane_ids", "missing_fields", "forbidden_fields"):
        list_ok(value.get(field_name), f"{path}.{field_name}", state)


def validate_active_pass(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS, path, state)
    handle_type = value.get("wait_handle_type")
    if handle_type not in WAIT_HANDLE_TYPES:
        state.error("active_pass.wait_handle_type", f"{path}.wait_handle_type", "expected agent_id or submission_id")
    elif value.get("wait_handle") != value.get(handle_type):
        state.error("active_pass.wait_handle", f"{path}.wait_handle", "must copy the selected wait handle field")
    if value.get("spawn_tool") != "spawn_agent":
        state.error("active_pass.spawn_tool", f"{path}.spawn_tool", "physical pass must record spawn_tool=spawn_agent")
    # 한국어 유지보수 주석: agent_id 문자열만으로는 실제 생성 증거가 되지 않는다.
    # spawn/wait 시점의 receipt를 별도 필드로 강제해 논리 lane과 물리 실행을 분리한다.
    for field_name in ("source_launch_manifest_ref", "spawn_receipt_ref", "spawned_at", "wait_registered_at"):
        if not isinstance(value.get(field_name), str) or not value.get(field_name):
            state.error("active_pass.physical_witness", f"{path}.{field_name}", "non-empty physical spawn/wait witness is required")
    if value.get("status") in {"returned", "closed", "timed_out", "superseded", "schema_invalid"}:
        proof = value.get("pass_closure_proof")
        if not isinstance(proof, dict):
            state.error("active_pass.pass_closure_proof", f"{path}.pass_closure_proof", "completed or classified passes require pass_closure_proof")
        else:
            proof_fields = {"wait_result_ref", "classification_ref", "superseded_ref"}
            present = [field_name for field_name in proof_fields if proof.get(field_name)]
            if len(present) != 1:
                state.error("active_pass.pass_closure_proof", f"{path}.pass_closure_proof", "exactly one closure proof ref is required; close_agent_ref is cleanup only")


def validate_active_passes(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, ACTIVE_PASSES_REQUIRED_FIELDS, path, state)
    passes = value.get("active_passes")
    list_ok(passes, f"{path}.active_passes", state)
    if isinstance(passes, list):
        for index, item in enumerate(passes):
            validate_active_pass(item, f"{path}.active_passes[{index}]", state)


def validate_stage_pass(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, STAGE_PASS_REQUIRED_FIELDS, path, state)
    if value.get("schema_status") not in SCHEMA_STATUSES:
        state.error("stage_pass.schema_status", f"{path}.schema_status", "invalid schema_status")
    if value.get("stage_status") == "closed" and not value.get("closed_at"):
        state.error("stage_pass.closed_at", f"{path}.closed_at", "closed stage requires closed_at")
    spawn_contract = value.get("stage_spawn_contract")
    if object_ok(spawn_contract, f"{path}.stage_spawn_contract", state):
        require_fields(spawn_contract, {"spawn_agent_type", "spawn_fork_context", "spawn_packet_mode"}, f"{path}.stage_spawn_contract", state)
        if spawn_contract.get("spawn_packet_mode") not in CONTROL_STAGE_SPAWN_PACKET_MODES:
            state.error("stage_pass.stage_spawn_contract", f"{path}.stage_spawn_contract.spawn_packet_mode", "invalid spawn_packet_mode")


def validate_handoff_result(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, HANDOFF_RESULT_REQUIRED_FIELDS, path, state)
    if value.get("pass_status") not in PASS_STATUSES:
        state.error("handoff_result.pass_status", f"{path}.pass_status", f"expected one of {sorted(PASS_STATUSES)}")
    list_ok(value.get("evidence_refs"), f"{path}.evidence_refs", state)
    list_ok(value.get("findings"), f"{path}.findings", state)


def validate_aggregation_packet(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, AGGREGATION_PACKET_REQUIRED_FIELDS, path, state)
    validate_loop_carryover(value.get("loop_carryover"), f"{path}.loop_carryover", state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)
    bundle = value.get("aggregation_input_bundle")
    if object_ok(bundle, f"{path}.aggregation_input_bundle", state):
        require_fields(bundle, {"handoff_results_ref", "active_passes_ref", "missing_lane_classes_ref", "schema_invalid_outputs_ref", "aggregation_input_mode"}, f"{path}.aggregation_input_bundle", state)
        for field_name in ("handoff_results_ref", "missing_lane_classes_ref", "schema_invalid_outputs_ref"):
            list_ok(bundle.get(field_name), f"{path}.aggregation_input_bundle.{field_name}", state)
        if bundle.get("aggregation_input_mode") != "canonical":
            state.error("aggregation_packet.aggregation_input_bundle", f"{path}.aggregation_input_bundle.aggregation_input_mode", "expected canonical")
    for field_name in ("evidence_refs", "artifact_refs", "artifact_kinds", "source_pass_ids", "source_lane_ids", "source_parent_pass_ids", "missing_lanes", "schema_invalid_outputs", "required_review_axes", "coverage_status"):
        list_ok(value.get(field_name), f"{path}.{field_name}", state)
    if isinstance(value.get("schema_invalid_outputs"), list):
        for index, item in enumerate(value["schema_invalid_outputs"]):
            validate_schema_invalid(item, f"{path}.schema_invalid_outputs[{index}]", state)
    missing_lanes = value.get("missing_lanes")
    if isinstance(missing_lanes, list):
        for index, item in enumerate(missing_lanes):
            item_path = f"{path}.missing_lanes[{index}]"
            if not object_ok(item, item_path, state):
                continue
            if item.get("failure_class") not in MISSING_LANE_CLASSES:
                state.error("aggregation_packet.missing_lanes", f"{item_path}.failure_class", "invalid missing-lane class")
    if isinstance(value.get("required_review_axes"), list) and isinstance(value.get("coverage_status"), list):
        covered = {item.get("axis") for item in value["coverage_status"] if isinstance(item, dict)}
        missing = set(value["required_review_axes"]) - covered
        if missing:
            state.error("aggregation_packet.coverage_status", f"{path}.coverage_status", f"missing coverage axes: {sorted(missing)}")


def validate_blocked_aggregation(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    expect_equal(value.get("aggregation_ready"), False, f"{path}.aggregation_ready", state)
    expect_equal(value.get("next_owner"), "meta-judge", f"{path}.next_owner", state)
    forbid_fields(value, {"aggregation_packet"}, path, state)
    for field_name in ("source_blocked_aggregation_ref", "aggregation_inputs", "context_packet_version", "loop_carryover", "loop_control", "required_validation_evidence", "contract_provenance"):
        if field_name not in value:
            state.error("missing_fields", path, f"missing {field_name}")
    validate_loop_carryover(value.get("loop_carryover"), f"{path}.loop_carryover", state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)
    list_ok(value.get("required_validation_evidence"), f"{path}.required_validation_evidence", state)
    inputs = value.get("aggregation_inputs")
    if object_ok(inputs, f"{path}.aggregation_inputs", state):
        for field_name in ("handoff_results", "active_passes_summary", "missing_lane_classes", "schema_invalid_outputs", "handoff_results_ref", "missing_lane_classes_ref", "schema_invalid_outputs_ref"):
            list_ok(inputs.get(field_name), f"{path}.aggregation_inputs.{field_name}", state)
        if not isinstance(inputs.get("active_passes_ref"), str) or not inputs.get("active_passes_ref"):
            state.error("blocked_aggregation.aggregation_input_bundle", f"{path}.aggregation_inputs.active_passes_ref", "active_passes_ref is required")
        if inputs.get("aggregation_input_mode") != "canonical":
            state.error("blocked_aggregation.aggregation_input_bundle", f"{path}.aggregation_inputs.aggregation_input_mode", "expected canonical")
        handoff_results = inputs.get("handoff_results")
        if isinstance(handoff_results, list):
            for index, item in enumerate(handoff_results):
                validate_handoff_result(item, f"{path}.aggregation_inputs.handoff_results[{index}]", state)
        active_summary = inputs.get("active_passes_summary")
        if isinstance(active_summary, list):
            for index, item in enumerate(active_summary):
                validate_active_pass(item, f"{path}.aggregation_inputs.active_passes_summary[{index}]", state)
        classes = inputs.get("missing_lane_classes")
        if isinstance(classes, list):
            for index, item in enumerate(classes):
                if item not in MISSING_LANE_CLASSES:
                    state.error("blocked_aggregation.missing_lane_class", f"{path}.aggregation_inputs.missing_lane_classes[{index}]", f"invalid missing-lane class {item!r}")
        invalid_outputs = inputs.get("schema_invalid_outputs")
        if isinstance(invalid_outputs, list):
            for index, item in enumerate(invalid_outputs):
                validate_schema_invalid(item, f"{path}.aggregation_inputs.schema_invalid_outputs[{index}]", state)
        if isinstance(classes, list) and isinstance(invalid_outputs, list):
            has_schema_invalid = "schema_invalid" in classes
            if has_schema_invalid and not invalid_outputs:
                state.error("blocked_aggregation.schema_invalid_outputs", f"{path}.aggregation_inputs.schema_invalid_outputs", "schema_invalid class requires addressable schema_invalid_outputs")
            if invalid_outputs and not has_schema_invalid:
                state.error("blocked_aggregation.schema_invalid_outputs", f"{path}.aggregation_inputs.missing_lane_classes", "schema_invalid_outputs require missing_lane_classes to include schema_invalid")


def validate_judgment_envelope(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, JUDGMENT_ENVELOPE_REQUIRED_FIELDS, path, state)
    if value.get("loop_stage") not in JUDGMENT_ALLOWED_LOOP_STAGES:
        state.error("judgment.loop_stage", f"{path}.loop_stage", f"expected one of {sorted(JUDGMENT_ALLOWED_LOOP_STAGES)}")
    if value.get("decision") not in JUDGMENT_ALLOWED_DECISIONS:
        state.error("judgment.decision", f"{path}.decision", f"expected one of {sorted(JUDGMENT_ALLOWED_DECISIONS)}")
    bool_ok(value.get("feedback_required"), f"{path}.feedback_required", state)
    list_ok(value.get("success_criteria"), f"{path}.success_criteria", state)
    list_ok(value.get("validation_evidence"), f"{path}.validation_evidence", state)
    list_ok(value.get("review_input_refs"), f"{path}.review_input_refs", state)
    list_ok(value.get("feedback_gate_evidence"), f"{path}.feedback_gate_evidence", state)
    if isinstance(value.get("feedback_gate_evidence"), list) and not value["feedback_gate_evidence"]:
        state.error("judgment.feedback_gate_evidence", f"{path}.feedback_gate_evidence", "formal judgment requires feedback gate evidence")
    if not isinstance(value.get("meta_judge_stage_pass_ref"), str) or not value.get("meta_judge_stage_pass_ref"):
        state.error("judgment.meta_judge_stage_pass_ref", f"{path}.meta_judge_stage_pass_ref", "meta-judge stage pass ref is required")
    if value.get("confidence") not in CONFIDENCE_LEVELS:
        state.error("judgment.confidence", f"{path}.confidence", f"expected one of {sorted(CONFIDENCE_LEVELS)}")
    target = value.get("feedback_target")
    if target in FEEDBACK_TARGET_REENTRY:
        owner, start = FEEDBACK_TARGET_REENTRY[target]
        expect_equal(value.get("next_owner"), owner, f"{path}.next_owner", state)
        expect_equal(value.get("next_loop_start"), start, f"{path}.next_loop_start", state)
    else:
        state.error("judgment.feedback_target", f"{path}.feedback_target", "unknown feedback target")
    if value.get("feedback_required") is True:
        expect_equal(value.get("decision"), "feedback", f"{path}.decision", state)
        if isinstance(value.get("success_criteria"), list) and not value["success_criteria"]:
            state.error("judgment.success_criteria", f"{path}.success_criteria", "feedback requires non-empty success criteria")
        if not value.get("final_blocked_reason"):
            state.error("judgment.final_blocked_reason", f"{path}.final_blocked_reason", "required when feedback_required=true")
        validate_bounded_rework_request(value.get("bounded_rework_request"), f"{path}.bounded_rework_request", state)
    if value.get("feedback_required") is False:
        expect_equal(value.get("decision"), "final output", f"{path}.decision", state)
        expect_equal(target, "none", f"{path}.feedback_target", state)
        if value.get("bounded_rework_request") not in (None, {}, []):
            state.error("judgment.bounded_rework_request", f"{path}.bounded_rework_request", "must be empty for final output")
        carryover = value.get("loop_carryover")
        if isinstance(carryover, dict):
            for field_name in ("unmet_success_criteria", "unresolved_blockers", "required_validation_evidence"):
                if carryover.get(field_name):
                    state.error("judgment.final_with_open_carryover", f"{path}.loop_carryover.{field_name}", "final output requires empty carryover blockers/evidence gaps")
    validate_review_coverage(value.get("review_coverage"), f"{path}.review_coverage", state)
    validate_loop_carryover(value.get("loop_carryover"), f"{path}.loop_carryover", state)
    validate_loop_control(value.get("loop_control"), f"{path}.loop_control", state)
    validate_contract_provenance(value.get("contract_provenance"), f"{path}.contract_provenance", state)
    gate_bundle = value.get("gate_evidence_bundle")
    if object_ok(gate_bundle, f"{path}.gate_evidence_bundle", state):
        require_fields(gate_bundle, {"stage_passes_ref", "active_passes_ref", "review_results_ref", "mcp_evidence_summary"}, f"{path}.gate_evidence_bundle", state)
        if not isinstance(gate_bundle.get("mcp_evidence_summary"), dict):
            state.error("judgment.gate_evidence_bundle", f"{path}.gate_evidence_bundle.mcp_evidence_summary", "expected object")
    tool_snapshot = value.get("tool_quiescence_snapshot")
    if object_ok(tool_snapshot, f"{path}.tool_quiescence_snapshot", state):
        require_fields(tool_snapshot, {"open_tool_call_count", "open_tool_call_ids", "snapshot_at"}, f"{path}.tool_quiescence_snapshot", state)
        if not isinstance(tool_snapshot.get("open_tool_call_count"), int):
            state.error("judgment.tool_quiescence_snapshot", f"{path}.tool_quiescence_snapshot.open_tool_call_count", "expected integer")
        if isinstance(tool_snapshot.get("open_tool_call_count"), int) and tool_snapshot["open_tool_call_count"] > 0:
            state.error("judgment.tool_quiescence_snapshot", f"{path}.tool_quiescence_snapshot.open_tool_call_count", "open tool calls block judgment")
        list_ok(tool_snapshot.get("open_tool_call_ids"), f"{path}.tool_quiescence_snapshot.open_tool_call_ids", state)
    waivers = value.get("review_waivers")
    list_ok(waivers, f"{path}.review_waivers", state)
    if isinstance(waivers, list):
        for index, waiver in enumerate(waivers):
            waiver_path = f"{path}.review_waivers[{index}]"
            if object_ok(waiver, waiver_path, state):
                require_fields(waiver, REVIEW_WAIVER_REQUIRED_FIELDS, waiver_path, state)
        coverage = value.get("review_coverage")
        if isinstance(coverage, dict) and isinstance(coverage.get("waived_axes"), list):
            waiver_axes = {waiver.get("axis") for waiver in waivers if isinstance(waiver, dict)}
            if set(coverage["waived_axes"]) != waiver_axes:
                state.error("judgment.review_waiver_parity", f"{path}.review_waivers", "waived_axes must match review_waivers[].axis")
    if isinstance(value.get("review_input_refs"), list) and isinstance(waivers, list):
        if not value["review_input_refs"] and not waivers:
            state.error("judgment.review_input_refs", f"{path}.review_input_refs", "formal judgment requires reviewer input refs or explicit review waivers")


def validate_run_ledger(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, RUN_LEDGER_REQUIRED_FIELDS, path, state)
    if value.get("schema_status") not in SCHEMA_STATUSES:
        state.error("run_ledger.schema_status", f"{path}.schema_status", "invalid schema_status")
    bool_ok(value.get("feedback_gate_mandatory"), f"{path}.feedback_gate_mandatory", state)
    bool_ok(value.get("feedback_required"), f"{path}.feedback_required", state)


def validate_contract_provenance(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, CONTRACT_PROVENANCE_REQUIRED_FIELDS, path, state)
    list_ok(value.get("source_contract_refs"), f"{path}.source_contract_refs", state)
    bool_ok(value.get("contract_lookup_missing"), f"{path}.contract_lookup_missing", state)


def validate_loop_carryover(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, LOOP_CARRYOVER_REQUIRED_FIELDS, path, state)
    for field_name in ("preserved_allowed_scope", "unmet_success_criteria", "unresolved_blockers", "rejected_assumptions", "required_validation_evidence"):
        list_ok(value.get(field_name), f"{path}.{field_name}", state)


def validate_loop_control(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, LOOP_CONTROL_REQUIRED_FIELDS, path, state)
    for field_name in ("loop_attempt", "repeat_feedback_count", "max_loop_attempts"):
        if not isinstance(value.get(field_name), int):
            state.error("type.int", f"{path}.{field_name}", "expected integer")
    progress = value.get("progress_delta")
    list_ok(progress, f"{path}.progress_delta", state)
    if isinstance(progress, list):
        for index, delta in enumerate(progress):
            delta_path = f"{path}.progress_delta[{index}]"
            if object_ok(delta, delta_path, state):
                require_fields(delta, PROGRESS_DELTA_REQUIRED_FIELDS, delta_path, state)
                for field_name in PROGRESS_DELTA_REQUIRED_FIELDS:
                    list_ok(delta.get(field_name), f"{delta_path}.{field_name}", state)
    has_progress = False
    if isinstance(progress, list):
        has_progress = any(
            isinstance(delta, dict)
            and any(delta.get(field_name) for field_name in PROGRESS_DELTA_REQUIRED_FIELDS)
            for delta in progress
        )
    if isinstance(value.get("repeat_feedback_count"), int) and value["repeat_feedback_count"] >= 2 and not has_progress:
        action = str(value.get("no_progress_action", ""))
        if "respond to user" not in action and "schema/tool/doc repair" not in action:
            state.error("loop_control.no_progress_action", f"{path}.no_progress_action", "repeated no-progress feedback requires user response or schema/tool/doc repair")


def validate_bounded_rework_request(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, BOUNDED_REWORK_REQUEST_REQUIRED_FIELDS, path, state)
    forbid_fields(value, {"loop_carryover", "loop_control", "success_criteria"}, path, state)
    for field_name in ("requested_scope_refs", "allowed_scope_subset_of", "requested_actions", "success_criteria_delta", "blocker_refs"):
        list_ok(value.get(field_name), f"{path}.{field_name}", state)


def validate_review_coverage(value: Any, path: str, state: ValidationState) -> None:
    if not object_ok(value, path, state):
        return
    require_fields(value, REVIEW_COVERAGE_REQUIRED_FIELDS, path, state)
    for field_name in REVIEW_COVERAGE_REQUIRED_FIELDS:
        list_ok(value.get(field_name), f"{path}.{field_name}", state)
    if all(isinstance(value.get(field_name), list) for field_name in REVIEW_COVERAGE_REQUIRED_FIELDS):
        uncovered = set(value["required_axes"]) - set(value["covered_axes"]) - set(value["waived_axes"])
        if uncovered:
            state.error("review_coverage.uncovered", path, f"uncovered axes: {sorted(uncovered)}")


def object_ok(value: Any, path: str, state: ValidationState) -> bool:
    if not isinstance(value, dict):
        state.error("type.object", path, "expected object")
        return False
    return True


def list_ok(value: Any, path: str, state: ValidationState) -> bool:
    if not isinstance(value, list):
        state.error("type.list", path, "expected list")
        return False
    return True


def bool_ok(value: Any, path: str, state: ValidationState) -> bool:
    if not isinstance(value, bool):
        state.error("type.bool", path, "expected boolean")
        return False
    return True


def require_fields(value: dict[str, Any], fields: set[str], path: str, state: ValidationState) -> None:
    missing = sorted(fields - set(value))
    if missing:
        state.error("missing_fields", path, f"missing fields: {missing}")


def forbid_fields(value: dict[str, Any], fields: set[str], path: str, state: ValidationState) -> None:
    present = sorted(fields & set(value))
    if present:
        state.error("forbidden_fields", path, f"forbidden fields: {present}")


def expect_equal(actual: Any, expected: Any, path: str, state: ValidationState) -> None:
    if actual != expected:
        state.error("value.equal", path, f"expected {expected!r}, got {actual!r}")


def main(argv: list[str]) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate a concrete Codex runtime artifact JSON object.")
    parser.add_argument("--input", "-i", help="JSON file path; omit or use - for stdin")
    parser.add_argument("--artifact", default="auto", choices=ARTIFACT_CHOICES, help="artifact type to validate")
    parser.add_argument("--stage-owner", choices=sorted(STAGE_ARTIFACTS), help="optional canonical stage owner")
    args = parser.parse_args(argv)
    try:
        payload = load_json(args.input)
        result = validate_payload(payload, artifact=args.artifact, stage_owner=args.stage_owner)
    except json.JSONDecodeError as exc:
        result = {
            "validation_status": "failed",
            "artifact_type": args.artifact,
            "schema_status": "invalid",
            "failure_class": "input_invalid",
            "next_owner": None,
            "errors": [{"code": "json.decode", "path": args.input or "stdin", "message": str(exc)}],
            "warnings": [],
        }
    except OSError as exc:
        result = {
            "validation_status": "failed",
            "artifact_type": args.artifact,
            "schema_status": "invalid",
            "failure_class": "io_error",
            "next_owner": None,
            "errors": [{"code": "io.read", "path": args.input or "stdin", "message": str(exc)}],
            "warnings": [],
        }
    except Exception as exc:  # CLI must return machine-readable failure.
        result = {
            "validation_status": "failed",
            "artifact_type": args.artifact,
            "schema_status": "invalid",
            "failure_class": "validator_bug",
            "next_owner": None,
            "errors": [{"code": "runtime_validator.exception", "path": args.input or "stdin", "message": str(exc)}],
            "warnings": [],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["validation_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
