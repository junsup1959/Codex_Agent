#!/usr/bin/env python3
"""Smoke-test runtime artifact validator, harness gate, and handoff wiring."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import harness_gate
import harness_handoff

CHECKS_RUN = 0


def load_runtime_validator():
    script = Path(__file__).with_name("validate-runtime-artifact.py")
    spec = importlib.util.spec_from_file_location("codex_runtime_artifact_validator_smoke", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime validator from {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME_VALIDATOR = load_runtime_validator()


def provenance() -> dict[str, Any]:
    return {"source_contract_refs": ["07-contracts-ledgers.md"], "contract_lookup_missing": False}


def loop_carryover() -> dict[str, Any]:
    return {
        "preserved_allowed_scope": ["architecture files"],
        "unmet_success_criteria": [],
        "unresolved_blockers": [],
        "rejected_assumptions": [],
        "required_validation_evidence": [],
        "context_packet_version": "ctx-1",
        "source_judgment_ref": "judgment:prior",
    }


def loop_control() -> dict[str, Any]:
    return {
        "loop_attempt": 1,
        "repeat_feedback_count": 0,
        "max_loop_attempts": 4,
        "progress_delta": [],
        "no_progress_action": "respond to user or require schema/tool/doc repair",
    }


def mcp_quiescence() -> dict[str, Any]:
    return {
        "open_mcp_process_count": 0,
        "open_mcp_process_ids": [],
        "cleanup_status": "clean",
        "snapshot_at": "2026-04-28T00:00:12Z",
    }


def fanout_budget() -> dict[str, Any]:
    return {
        "max_worker_lanes_per_wave": 2,
        "max_review_lanes_per_wave": 2,
        "max_total_child_agents_per_loop": 4,
        "max_same_role_parallel_lanes": 1,
        "max_mcp_concurrent_child_lanes": 1,
        "budget_reason": "smoke default bounded fanout",
        "overflow_policy": "coalesce_axes_or_feedback",
    }


def lane(*, lane_type: str = "worker", return_owner: str = "aggregator") -> dict[str, Any]:
    return {
        "lane_id": f"lane-{lane_type}-1",
        "parent_router_pass_id": "router-pass-1",
        "agent_category": "10-research-analysis",
        "agent_role": "docs-researcher",
        "lane_type": lane_type,
        "owned_scope": "runtime gate smoke",
        "expected_artifact": "handoff_result",
        "merge_point": "aggregation_packet.inputs",
        "return_owner": return_owner,
        "validation_prompt": "return bounded handoff_result",
        "context_packet_version": "ctx-1",
        "spawn_context_mode": "scoped_packet",
        "caller_spawn_required": True,
        "initial_status": "unmaterialized",
    }


def worker_manifest() -> dict[str, Any]:
    return {
        "launch_manifest": {
            "manifest_kind": "worker",
            "source_parent_ref": "execution_plan:wave-1",
            "source_execution_plan_ref": "execution_plan:wave-1",
            "context_packet_version": "ctx-1",
            "children": [lane()],
            "loop_control": loop_control(),
            "fanout_budget": fanout_budget(),
            "mcp_quiescence_snapshot": mcp_quiescence(),
            "contract_provenance": provenance(),
            "schema_status": "valid",
        }
    }


def review_manifest(*, agent_category: str = "10-research-analysis", agent_role: str = "docs-researcher") -> dict[str, Any]:
    review_lane = lane(lane_type="review", return_owner="meta-judge")
    review_lane["agent_category"] = agent_category
    review_lane["agent_role"] = agent_role
    review_lane["validation_prompt"] = "return bounded handoff_result; docker_mcp_sequentialthinking_required=true; evidence=MCP_DOCKER/sequentialthinking:success"
    return {
        "launch_manifest": {
            "manifest_kind": "review",
            "source_parent_ref": "aggregation_packet:loop-1",
            "source_aggregation_packet_ref": "aggregation_packet:loop-1",
            "context_packet_version": "ctx-1",
            "children": [review_lane],
            "validation_evidence": ["docker_mcp_sequentialthinking_required=true", "MCP_DOCKER/sequentialthinking:success"],
            "loop_control": loop_control(),
            "fanout_budget": fanout_budget(),
            "mcp_quiescence_snapshot": mcp_quiescence(),
            "contract_provenance": provenance(),
            "schema_status": "valid",
        }
    }


def active_passes() -> dict[str, Any]:
    return {
        "active_passes": [
            {
                "run_id": "run-1",
                "loop_id": "loop-1",
                "loop_attempt": 1,
                "lane_id": "lane-worker-1",
                "pass_id": "child-pass-1",
                "role": "docs-researcher",
                "agent_category": "10-research-analysis",
                "agent_role": "docs-researcher",
                "agent_id": "agent-1",
                "submission_id": "submission-1",
                "wait_handle_type": "agent_id",
                "wait_handle": "agent-1",
                "source_launch_manifest_ref": "launch_manifest:wave-1",
                "spawn_tool": "spawn_agent",
                "spawn_receipt_ref": "spawn_agent:agent-1",
                "spawned_at": "2026-04-28T00:00:02Z",
                "wait_registered_at": "2026-04-28T00:00:03Z",
                "owned_scope": "runtime gate smoke",
                "merge_point": "aggregation_packet.inputs",
                "context_packet_version": "ctx-1",
                "status": "active",
            }
        ]
    }


def stage_passes() -> dict[str, Any]:
    return {
        "stage_passes": [
            {
                "run_id": "run-1",
                "loop_id": "loop-1",
                "loop_attempt": 1,
                "stage_pass_id": "meta-judge:loop-1",
                "stage_owner": "meta-judge",
                "stage_status": "closed",
                "artifact_name": "judgment_envelope",
                "artifact_ref": "judgment:loop-1",
                "context_packet_version": "ctx-1",
                "schema_status": "valid",
                "created_at": "2026-04-28T00:00:10Z",
                "closed_at": "2026-04-28T00:00:11Z",
                "next_owner": "orchestrator",
                "stage_spawn_contract": {
                    "spawn_agent_type": "meta-judge",
                    "spawn_fork_context": False,
                    "spawn_packet_mode": "curated_stage_packet",
                },
            }
        ]
    }


def review_results() -> dict[str, Any]:
    return {
        "review_results": [
            {
                "sender": "architecture-reviewer",
                "lane_id": "lane-review-1",
                "pass_id": "review-pass-1",
                "parent_pass_id": "review-router-pass-1",
                "pass_status": "returned",
                "owned_scope": "runtime gate smoke",
                "artifact_summary": "review returned",
                "artifact_ref": "artifact:review-pass-1",
                "artifact_kind": "review-note",
                "evidence_refs": ["evidence:review-pass-1"],
                "findings": [],
                "confidence": "high",
                "merge_point": "judgment_envelope.review_input_refs",
                "context_packet_version": "ctx-1",
                "caller_signals": [],
                "mcp_quiescence_snapshot": mcp_quiescence(),
            }
        ]
    }


def run_ledger() -> dict[str, Any]:
    return {
        "run_ledger": {
            "run_id": "run-1",
            "loop_id": "loop-1",
            "user_goal": "runtime gate smoke",
            "allowed_scope": ["architecture files"],
            "stage": "judgment",
            "stage_artifact_name": "judgment_envelope",
            "stage_artifact_ref": "judgment:loop-1",
            "schema_status": "valid",
            "validation_evidence": ["smoke fixture"],
            "context_packet_version": "ctx-1",
            "loop_attempt": 1,
            "repeat_feedback_count": 0,
            "feedback_gate_mandatory": True,
            "feedback_required": False,
            "failure_class": "none",
            "decision": "final output",
            "next_owner": "orchestrator",
            "created_at": "2026-04-28T00:00:00Z",
            "updated_at": "2026-04-28T00:00:11Z",
        }
    }


def gate_judgment(
    payload: dict[str, Any],
    *,
    stage_passes_payload: Any | None = None,
    review_results_payload: Any | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    default_stage_passes = stage_passes()
    judgment_payload = payload.get("judgment_envelope", payload) if isinstance(payload, dict) else {}
    if isinstance(judgment_payload, dict):
        loop_control_payload = judgment_payload.get("loop_control") if isinstance(judgment_payload.get("loop_control"), dict) else {}
        loop_carryover_payload = judgment_payload.get("loop_carryover") if isinstance(judgment_payload.get("loop_carryover"), dict) else {}
        default_stage_passes["stage_passes"][0]["loop_id"] = judgment_payload.get("loop_id", "loop-1")
        default_stage_passes["stage_passes"][0]["loop_attempt"] = loop_control_payload.get("loop_attempt", 1)
        default_stage_passes["stage_passes"][0]["context_packet_version"] = loop_carryover_payload.get("context_packet_version", "ctx-1")
    return harness_gate.gate_stage_output(
        payload,
        stage_owner="meta-judge",
        stage_passes=stage_passes_payload if stage_passes_payload is not None else default_stage_passes,
        review_results=review_results_payload if review_results_payload is not None else review_results(),
        **kwargs,
    )


def handoff_result_with_next_owner(next_owner: str) -> dict[str, Any]:
    return {
        "handoff_result": {
            "sender": "docs-researcher",
            "lane_id": "lane-worker-1",
            "pass_id": "child-pass-1",
            "parent_pass_id": "router-pass-1",
            "pass_status": "returned",
            "owned_scope": "runtime gate smoke",
            "artifact_summary": "bounded result",
            "artifact_ref": "artifact:child-pass-1",
            "artifact_kind": "analysis-note",
            "evidence_refs": [],
            "findings": [],
            "confidence": "medium",
            "merge_point": "aggregation_packet.inputs",
            "context_packet_version": "ctx-1",
            "caller_signals": [],
            "mcp_quiescence_snapshot": mcp_quiescence(),
        },
        "next_owner": next_owner,
    }


def blocked_aggregation() -> dict[str, Any]:
    return {
        "aggregation_ready": False,
        "source_blocked_aggregation_ref": "blocked_aggregation:loop-1",
        "aggregation_inputs": {
            "handoff_results": [],
            "active_passes_summary": [],
            "missing_lane_classes": ["schema_invalid"],
            "schema_invalid_outputs": [
                {
                    "manifest_kind": "worker",
                    "source_parent_ref": "execution_plan:wave-1",
                    "context_packet_version": "ctx-1",
                    "parent_router_pass_id": "router-pass-1",
                    "lane_ids": ["lane-worker-1"],
                    "missing_fields": ["artifact_ref"],
                    "forbidden_fields": [],
                }
            ],
            "handoff_results_ref": [],
            "active_passes_ref": "active_passes:run-1",
            "missing_lane_classes_ref": ["missing_lane_classes:router-pass-1"],
            "schema_invalid_outputs_ref": ["schema_invalid:router-pass-1"],
            "aggregation_input_mode": "canonical",
        },
        "next_owner": "meta-judge",
        "context_packet_version": "ctx-1",
        "loop_carryover": loop_carryover(),
        "loop_control": loop_control(),
        "required_validation_evidence": ["valid aggregation_packet", "docker_mcp_sequentialthinking_required=true", "MCP_DOCKER/sequentialthinking:success"],
        "mcp_quiescence_snapshot": mcp_quiescence(),
        "contract_provenance": provenance(),
    }


def judgment(*, feedback: bool) -> dict[str, Any]:
    if feedback:
        request = {
            "target": "aggregator",
            "reason": "repair invalid aggregation",
            "source_judgment_ref": "judgment:loop-1",
            "requested_scope_refs": ["aggregation inputs"],
            "allowed_scope_subset_of": ["architecture files"],
            "requested_actions": ["rerun aggregation"],
            "success_criteria_delta": ["valid aggregation_packet"],
            "blocker_refs": ["schema_invalid:router-pass-1"],
        }
        decision = "feedback"
        feedback_target = "aggregator"
        next_loop_start = "context-manager"
        final_blocked_reason = "schema invalid output"
    else:
        request = None
        decision = "final output"
        feedback_target = "none"
        next_loop_start = "none"
        final_blocked_reason = ""
    return {
        "judgment_envelope": {
            "loop_id": "loop-1",
            "loop_stage": "judgment",
            "decision": decision,
            "feedback_required": feedback,
            "feedback_target": feedback_target,
            "next_owner": "orchestrator",
            "next_loop_start": next_loop_start,
            "final_blocked_reason": final_blocked_reason,
            "bounded_rework_request": request,
            "success_criteria": ["runtime gate smoke"],
            "confidence": "high",
            "validation_evidence": ["smoke fixture", "docker_mcp_sequentialthinking_required=true", "MCP_DOCKER/sequentialthinking:success"],
            "review_input_refs": ["handoff_result:review-pass-1"],
            "meta_judge_stage_pass_ref": "stage_pass:meta-judge:loop-1",
            "feedback_gate_evidence": ["feedback_gate:reviewed-required-fields"],
            "review_coverage": {"required_axes": ["architecture"], "covered_axes": ["architecture"], "waived_axes": []},
            "review_waivers": [],
            "source_aggregation_packet_ref": "aggregation_packet:loop-1",
            "source_blocked_aggregation_ref": "",
            "loop_carryover": loop_carryover(),
            "loop_control": loop_control(),
            "mcp_quiescence_snapshot": mcp_quiescence(),
            "gate_evidence_bundle": {
                "stage_passes_ref": "stage_passes:loop-1",
                "active_passes_ref": "active_passes:run-1",
                "review_results_ref": "review_results:loop-1",
                "mcp_evidence_summary": {"success": ["MCP_DOCKER/sequentialthinking:success"], "blocked": [], "waived": [], "error_unclassified": []},
            },
            "tool_quiescence_snapshot": {
                "open_tool_call_count": 0,
                "open_tool_call_ids": [],
                "snapshot_at": "2026-04-28T00:00:11Z",
            },
            "contract_provenance": provenance(),
        }
    }


def progress_delta(*, blocker: str = "schema_invalid:router-pass-1") -> dict[str, Any]:
    return {
        "new_artifact_refs": ["artifact:repair"],
        "new_evidence_refs": ["evidence:repair"],
        "changed_blocker_fingerprint": [blocker],
        "changed_context_packet_version": [],
    }


def judgment_with_loop(
    *,
    feedback: bool,
    attempt: int,
    repeat: int,
    blockers: list[dict[str, Any]] | None = None,
    progress: list[dict[str, Any]] | None = None,
    scope: list[str] | None = None,
) -> dict[str, Any]:
    item = judgment(feedback=feedback)
    envelope = item["judgment_envelope"]
    envelope["loop_control"]["loop_attempt"] = attempt
    envelope["loop_control"]["repeat_feedback_count"] = repeat
    envelope["loop_control"]["progress_delta"] = progress if progress is not None else []
    envelope["loop_carryover"]["preserved_allowed_scope"] = scope if scope is not None else ["architecture files"]
    envelope["loop_carryover"]["unresolved_blockers"] = blockers if blockers is not None else []
    return item


def blocker() -> dict[str, Any]:
    return {
        "blocker_type": "schema_invalid",
        "source_pass_id": "router-pass-1",
        "artifact_ref": "launch_manifest:bad",
        "evidence_refs": ["evidence:bad-manifest"],
    }


def check(name: str, condition: bool, failures: list[str]) -> None:
    global CHECKS_RUN
    CHECKS_RUN += 1
    if not condition:
        failures.append(name)


def main() -> int:
    failures: list[str] = []
    valid_manifest = worker_manifest()

    runtime = RUNTIME_VALIDATOR.validate_payload(valid_manifest, stage_owner="worker-router")
    check("runtime_valid_worker_manifest", runtime["validation_status"] == "passed", failures)

    valid_review_runtime = RUNTIME_VALIDATOR.validate_payload(review_manifest(), stage_owner="review-router")
    check("runtime_valid_review_manifest_dependency", valid_review_runtime["validation_status"] == "passed", failures)

    missing_specialist_manifest = deepcopy(valid_manifest)
    missing_specialist_manifest["launch_manifest"]["children"][0]["agent_role"] = "missing-specialist"
    missing_specialist_runtime = RUNTIME_VALIDATOR.validate_payload(missing_specialist_manifest, stage_owner="worker-router")
    check("runtime_missing_specialist_blocks", missing_specialist_runtime["validation_status"] == "failed", failures)

    stage_owner_as_worker_manifest = deepcopy(valid_manifest)
    stage_owner_as_worker_manifest["launch_manifest"]["children"][0]["agent_category"] = "09-meta-orchestration"
    stage_owner_as_worker_manifest["launch_manifest"]["children"][0]["agent_role"] = "meta-judge"
    stage_owner_as_worker_runtime = RUNTIME_VALIDATOR.validate_payload(stage_owner_as_worker_manifest, stage_owner="worker-router")
    check("runtime_stage_owner_as_worker_blocks", stage_owner_as_worker_runtime["validation_status"] == "failed", failures)

    bad_review_dependency = RUNTIME_VALIDATOR.validate_payload(
        review_manifest(agent_category="01-core-development", agent_role="backend-developer"),
        stage_owner="review-router",
    )
    check("runtime_non_review_specialist_in_review_blocks", bad_review_dependency["validation_status"] == "failed", failures)

    gate = harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router")
    check("gate_allows_valid_manifest", gate["allow_next_stage"] is True and gate["next_owner"] == "caller", failures)

    handoff = harness_handoff.handoff_stage_output(valid_manifest, stage_owner="worker-router")
    check("handoff_allows_valid_manifest", handoff["handoff_status"] == "allowed", failures)

    materialized = harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router", expected_next_owner="worker-layer", active_passes=active_passes())
    check("router_materialized_allows_worker_layer", materialized["allow_next_stage"] is True and materialized["next_owner"] == "worker-layer", failures)

    role_mismatch_passes = active_passes()
    role_mismatch_passes["active_passes"][0]["agent_role"] = "search-specialist"
    check("materialization_active_pass_role_mismatch_blocks", harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router", expected_next_owner="worker-layer", active_passes=role_mismatch_passes)["allow_next_stage"] is False, failures)

    stray_passes = active_passes()
    stray_passes["active_passes"][0]["lane_id"] = "lane-stray"
    check("materialization_stray_active_pass_blocks", harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router", expected_next_owner="worker-layer", active_passes=stray_passes)["allow_next_stage"] is False, failures)

    fork_context_manifest = deepcopy(valid_manifest)
    fork_context_manifest["launch_manifest"]["children"][0]["spawn_context_mode"] = "fork_context"
    check("runtime_specialist_fork_context_blocks", RUNTIME_VALIDATOR.validate_payload(fork_context_manifest, stage_owner="worker-router")["validation_status"] == "failed", failures)

    invalid_spawn_context_manifest = deepcopy(valid_manifest)
    invalid_spawn_context_manifest["launch_manifest"]["children"][0]["spawn_context_mode"] = "unknown_mode"
    check("runtime_invalid_spawn_context_mode_blocks", RUNTIME_VALIDATOR.validate_payload(invalid_spawn_context_manifest, stage_owner="worker-router")["validation_status"] == "failed", failures)

    waiver_manifest = deepcopy(valid_manifest)
    waiver_manifest["launch_manifest"]["children"][0]["spawn_context_mode"] = "scoped_packet_with_waiver"
    check("runtime_missing_context_waiver_blocks", RUNTIME_VALIDATOR.validate_payload(waiver_manifest, stage_owner="worker-router")["validation_status"] == "failed", failures)

    unmaterialized = harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router", expected_next_owner="worker-layer")
    check("router_missing_active_passes_blocks", unmaterialized["allow_next_stage"] is False and unmaterialized["failure_class"] == "unmaterialized_lane", failures)

    invalid = {"launch_manifest": {"manifest_kind": "worker"}}
    invalid_gate = harness_gate.gate_stage_output(invalid, stage_owner="worker-router")
    check("gate_blocks_invalid_manifest", invalid_gate["allow_next_stage"] is False and invalid_gate["route_kind"] == "retry_same_stage", failures)

    wrong_stage = harness_gate.gate_stage_output(valid_manifest, stage_owner="context-manager")
    check("gate_blocks_wrong_stage_owner", wrong_stage["allow_next_stage"] is False, failures)

    wrong_expected = harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router", expected_next_owner="review-layer", active_passes=active_passes())
    check("gate_blocks_wrong_expected_next_owner", wrong_expected["allow_next_stage"] is False, failures)

    injected_next = harness_gate.gate_stage_output(handoff_result_with_next_owner("review-router"), stage_owner="worker-layer")
    check("handoff_result_next_owner_injection_blocks", injected_next["allow_next_stage"] is False, failures)

    timed_out_result = {"handoff_result": deepcopy(handoff_result_with_next_owner("aggregator")["handoff_result"])}
    timed_out_result["handoff_result"]["pass_status"] = "timed_out"
    check("handoff_result_timed_out_status_allowed", RUNTIME_VALIDATOR.validate_payload(timed_out_result, stage_owner="worker-layer")["validation_status"] == "passed", failures)

    schema_invalid_result = {"handoff_result": deepcopy(handoff_result_with_next_owner("aggregator")["handoff_result"])}
    schema_invalid_result["handoff_result"]["pass_status"] = "schema_invalid"
    check("handoff_result_schema_invalid_status_allowed", RUNTIME_VALIDATOR.validate_payload(schema_invalid_result, stage_owner="worker-layer")["validation_status"] == "passed", failures)

    check("active_passes_artifact_validates", RUNTIME_VALIDATOR.validate_payload(active_passes(), artifact="active_passes")["validation_status"] == "passed", failures)
    check("active_passes_raw_list_shape_blocks", RUNTIME_VALIDATOR.validate_payload(active_passes()["active_passes"], artifact="active_passes")["validation_status"] == "failed", failures)
    bad_active_passes = active_passes()
    bad_active_passes["active_passes"][0]["wait_handle"] = "wrong-handle"
    check("active_passes_bad_wait_handle_blocks", RUNTIME_VALIDATOR.validate_payload(bad_active_passes, artifact="active_passes")["validation_status"] == "failed", failures)
    synthetic_active_passes = active_passes()
    del synthetic_active_passes["active_passes"][0]["spawn_receipt_ref"]
    check("active_passes_missing_spawn_receipt_blocks", RUNTIME_VALIDATOR.validate_payload(synthetic_active_passes, artifact="active_passes")["validation_status"] == "failed", failures)
    no_wait_registration = active_passes()
    del no_wait_registration["active_passes"][0]["wait_registered_at"]
    check("active_passes_missing_wait_registration_blocks", RUNTIME_VALIDATOR.validate_payload(no_wait_registration, artifact="active_passes")["validation_status"] == "failed", failures)

    blocked = harness_gate.gate_stage_output(blocked_aggregation(), stage_owner="aggregator")
    check("blocked_aggregation_routes_to_meta_judge", blocked["allow_next_stage"] is True and blocked["next_owner"] == "meta-judge", failures)

    bad_blocked = blocked_aggregation()
    bad_blocked["aggregation_inputs"]["missing_lane_classes"] = ["bogus_class"]
    bad_blocked["aggregation_inputs"]["schema_invalid_outputs"] = ["not-an-object"]
    bad_blocked_gate = harness_gate.gate_stage_output(bad_blocked, stage_owner="aggregator")
    check("blocked_aggregation_bad_taxonomy_blocks", bad_blocked_gate["allow_next_stage"] is False, failures)

    bad_schema_invalid_parity = blocked_aggregation()
    bad_schema_invalid_parity["aggregation_inputs"]["missing_lane_classes"] = ["schema_invalid"]
    bad_schema_invalid_parity["aggregation_inputs"]["schema_invalid_outputs"] = []
    check("blocked_aggregation_schema_invalid_requires_outputs", harness_gate.gate_stage_output(bad_schema_invalid_parity, stage_owner="aggregator")["allow_next_stage"] is False, failures)

    bad_blocked_evidence = blocked_aggregation()
    bad_blocked_evidence["aggregation_inputs"]["handoff_results"] = ["not-an-object"]
    bad_blocked_evidence["aggregation_inputs"]["active_passes_summary"] = ["also-not-an-object"]
    check("blocked_aggregation_bad_input_shapes_block", harness_gate.gate_stage_output(bad_blocked_evidence, stage_owner="aggregator")["allow_next_stage"] is False, failures)

    string_only_feedback = harness_gate.gate_stage_output(judgment(feedback=True), stage_owner="meta-judge")
    check("feedback_string_only_judgment_blocks", string_only_feedback["allow_next_stage"] is False and string_only_feedback["failure_class"] == "contract_invalid", failures)

    string_only_final = harness_gate.gate_stage_output(judgment(feedback=False), stage_owner="meta-judge")
    check("final_string_only_judgment_blocks", string_only_final["allow_next_stage"] is False and string_only_final["failure_class"] == "contract_invalid", failures)

    feedback = gate_judgment(judgment(feedback=True))
    check("feedback_judgment_preserves_feedback", feedback["allow_next_stage"] is True and feedback["feedback_required"] is True and feedback["next_loop_start"] == "context-manager", failures)

    final = gate_judgment(judgment(feedback=False))
    check("final_judgment_preserves_final", final["allow_next_stage"] is True and final["feedback_required"] is False and final["next_loop_start"] == "none", failures)

    valid_run_ledger = RUNTIME_VALIDATOR.validate_payload(run_ledger(), artifact="run_ledger")
    check("run_ledger_requires_feedback_gate_mandatory_valid", valid_run_ledger["validation_status"] == "passed", failures)

    missing_gate_mandatory = deepcopy(run_ledger())
    del missing_gate_mandatory["run_ledger"]["feedback_gate_mandatory"]
    check("run_ledger_missing_feedback_gate_mandatory_blocks", RUNTIME_VALIDATOR.validate_payload(missing_gate_mandatory, artifact="run_ledger")["validation_status"] == "failed", failures)

    meta_loop_mismatch = stage_passes()
    meta_loop_mismatch["stage_passes"][0]["loop_id"] = "loop-stale"
    check("completion_meta_stage_loop_mismatch_blocks", gate_judgment(judgment(feedback=False), stage_passes_payload=meta_loop_mismatch)["allow_next_stage"] is False, failures)

    meta_attempt_mismatch = stage_passes()
    meta_attempt_mismatch["stage_passes"][0]["loop_attempt"] = 2
    check("completion_meta_stage_attempt_mismatch_blocks", gate_judgment(judgment(feedback=False), stage_passes_payload=meta_attempt_mismatch)["allow_next_stage"] is False, failures)

    meta_context_mismatch = stage_passes()
    meta_context_mismatch["stage_passes"][0]["context_packet_version"] = "ctx-stale"
    check("completion_meta_stage_context_mismatch_blocks", gate_judgment(judgment(feedback=False), stage_passes_payload=meta_context_mismatch)["allow_next_stage"] is False, failures)

    review_context_mismatch = review_results()
    review_context_mismatch["review_results"][0]["context_packet_version"] = "ctx-stale"
    check("completion_review_context_mismatch_blocks", gate_judgment(judgment(feedback=False), review_results_payload=review_context_mismatch)["allow_next_stage"] is False, failures)

    final_missing_gate_evidence = judgment(feedback=False)
    final_missing_gate_evidence["judgment_envelope"]["feedback_gate_evidence"] = []
    check("final_missing_feedback_gate_evidence_blocks", gate_judgment(final_missing_gate_evidence)["allow_next_stage"] is False, failures)

    bad_loop_stage = judgment(feedback=False)
    bad_loop_stage["judgment_envelope"]["loop_stage"] = "banana"
    check("judgment_bad_loop_stage_blocks", gate_judgment(bad_loop_stage)["allow_next_stage"] is False, failures)

    bad_judgment_lists = judgment(feedback=True)
    bad_judgment_lists["judgment_envelope"]["success_criteria"] = "not-a-list"
    bad_judgment_lists["judgment_envelope"]["validation_evidence"] = "not-a-list"
    check("judgment_bad_list_fields_block", gate_judgment(bad_judgment_lists)["allow_next_stage"] is False, failures)

    missing_physical_evidence = judgment(feedback=True)
    missing_physical_evidence["judgment_envelope"]["review_input_refs"] = []
    missing_physical_evidence["judgment_envelope"]["meta_judge_stage_pass_ref"] = ""
    missing_physical_evidence["judgment_envelope"]["feedback_gate_evidence"] = []
    check("judgment_missing_physical_gate_evidence_blocks", gate_judgment(missing_physical_evidence)["allow_next_stage"] is False, failures)

    empty_feedback_criteria = judgment(feedback=True)
    empty_feedback_criteria["judgment_envelope"]["success_criteria"] = []
    check("feedback_requires_success_criteria", gate_judgment(empty_feedback_criteria)["allow_next_stage"] is False, failures)

    previous = judgment_with_loop(feedback=True, attempt=1, repeat=1, blockers=[blocker()])
    current = judgment_with_loop(feedback=True, attempt=2, repeat=2, blockers=[blocker()])
    lineage_ok = gate_judgment(current, previous_judgment=previous)
    check("lineage_feedback_preserves_blockers", lineage_ok["allow_next_stage"] is True, failures)

    wrong_loop_id = judgment_with_loop(feedback=True, attempt=2, repeat=2, blockers=[blocker()])
    wrong_loop_id["judgment_envelope"]["loop_id"] = "loop-other"
    check("lineage_wrong_loop_id_blocks", gate_judgment(wrong_loop_id, previous_judgment=previous)["allow_next_stage"] is False, failures)

    wrong_source_ref = judgment_with_loop(feedback=True, attempt=2, repeat=2, blockers=[blocker()])
    wrong_source_ref["judgment_envelope"]["loop_carryover"]["source_judgment_ref"] = "judgment:unrelated"
    check("lineage_wrong_source_judgment_ref_blocks", gate_judgment(wrong_source_ref, previous_judgment=previous)["allow_next_stage"] is False, failures)

    scope_widen = judgment_with_loop(feedback=True, attempt=2, repeat=2, blockers=[blocker()], scope=["architecture files", "new scope"])
    check("lineage_scope_widen_blocks", gate_judgment(scope_widen, previous_judgment=previous)["allow_next_stage"] is False, failures)

    unchanged_repeat = judgment_with_loop(feedback=True, attempt=2, repeat=1, blockers=[blocker()])
    check("lineage_repeat_count_not_incremented_blocks", gate_judgment(unchanged_repeat, previous_judgment=previous)["allow_next_stage"] is False, failures)

    no_progress_escape_missing = judgment_with_loop(feedback=True, attempt=3, repeat=3, blockers=[blocker()])
    no_progress_escape_missing["judgment_envelope"]["loop_control"]["no_progress_action"] = "none"
    check("lineage_repeated_no_progress_escape_blocks", gate_judgment(no_progress_escape_missing, previous_judgment=previous)["allow_next_stage"] is False, failures)

    artifact_only_progress = judgment_with_loop(feedback=False, attempt=2, repeat=1, blockers=[], progress=[{"new_artifact_refs": ["artifact:only"], "new_evidence_refs": [], "changed_blocker_fingerprint": [], "changed_context_packet_version": []}])
    check("lineage_artifact_only_progress_allows_final", gate_judgment(artifact_only_progress, previous_judgment=previous)["allow_next_stage"] is True, failures)

    dropped_blocker = judgment_with_loop(feedback=True, attempt=2, repeat=2, blockers=[])
    check("lineage_blocker_drop_without_progress_blocks", gate_judgment(dropped_blocker, previous_judgment=previous)["allow_next_stage"] is False, failures)

    nonmonotonic = judgment_with_loop(feedback=True, attempt=1, repeat=2, blockers=[blocker()])
    check("lineage_nonmonotonic_attempt_blocks", gate_judgment(nonmonotonic, previous_judgment=previous)["allow_next_stage"] is False, failures)

    final_without_progress = judgment_with_loop(feedback=False, attempt=2, repeat=1, blockers=[])
    check("lineage_final_without_progress_blocks", gate_judgment(final_without_progress, previous_judgment=previous)["allow_next_stage"] is False, failures)

    fourth_loop = judgment_with_loop(feedback=False, attempt=4, repeat=3, blockers=[], progress=[progress_delta()])
    check("lineage_fourth_loop_with_progress_allows", gate_judgment(fourth_loop, previous_judgment=previous)["allow_next_stage"] is True, failures)

    final_source_mismatch = gate_judgment(judgment(feedback=False), expected_source_ref="aggregation_packet:newer")
    check("final_source_ref_mismatch_blocks", final_source_mismatch["allow_next_stage"] is False, failures)

    blocked_source_ok = harness_gate.gate_stage_output(blocked_aggregation(), stage_owner="aggregator", expected_source_ref="blocked_aggregation:loop-1")
    check("blocked_aggregation_source_ref_matches", blocked_source_ok["allow_next_stage"] is True, failures)

    blocked_branch_judgment = judgment(feedback=True)
    blocked_branch_judgment["judgment_envelope"]["source_aggregation_packet_ref"] = ""
    blocked_branch_judgment["judgment_envelope"]["source_blocked_aggregation_ref"] = "blocked_aggregation:loop-1"
    meta_blocked_source_ok = gate_judgment(blocked_branch_judgment, expected_source_ref="blocked_aggregation:loop-1")
    check("meta_judge_blocked_branch_source_ref_matches", meta_blocked_source_ok["allow_next_stage"] is True, failures)

    context_mismatch = harness_gate.gate_stage_output(worker_manifest(), stage_owner="worker-router", expected_context_packet_version="ctx-newer")
    check("context_packet_version_mismatch_blocks", context_mismatch["allow_next_stage"] is False, failures)

    bad_final = judgment(feedback=False)
    bad_final["judgment_envelope"]["loop_carryover"]["unresolved_blockers"] = [{"blocker_type": "evidence_gap"}]
    check("final_with_open_blocker_blocks", gate_judgment(bad_final)["allow_next_stage"] is False, failures)

    bad_waiver = judgment(feedback=False)
    bad_waiver["judgment_envelope"]["review_coverage"] = {"required_axes": ["security"], "covered_axes": [], "waived_axes": ["security"]}
    bad_waiver["judgment_envelope"]["review_waivers"] = []
    check("final_waiver_without_object_blocks", gate_judgment(bad_waiver)["allow_next_stage"] is False, failures)

    bad_loop = judgment(feedback=True)
    bad_loop["judgment_envelope"]["loop_control"]["repeat_feedback_count"] = 3
    bad_loop["judgment_envelope"]["loop_control"]["no_progress_action"] = "none"
    check("repeated_no_progress_requires_terminal_action", gate_judgment(bad_loop)["allow_next_stage"] is False, failures)

    active_mismatch = active_passes()
    active_mismatch["active_passes"][0]["context_packet_version"] = "ctx-stale"
    check("materialization_active_pass_context_mismatch_blocks", harness_gate.gate_stage_output(valid_manifest, stage_owner="worker-router", expected_next_owner="worker-layer", active_passes=active_mismatch)["allow_next_stage"] is False, failures)

    bad_missing_lane_item = {
        "aggregation_packet": {
            "normalized_claims": [],
            "context_packet_version": "ctx-1",
            "source_launch_manifest_ref": "launch_manifest:wave-1",
            "source_loop_id": "loop-1",
            "source_loop_attempt": 1,
            "source_pass_statuses": {},
            "active_pass_snapshot_ref": "active_passes:run-1",
            "evidence_refs": [],
            "artifact_refs": [],
            "artifact_kinds": [],
            "source_pass_ids": [],
            "source_lane_ids": [],
            "source_parent_pass_ids": [],
            "blocker_fingerprint": [],
            "loop_carryover": loop_carryover(),
            "loop_control": loop_control(),
            "merge_point": "review-router",
            "confidence_summary": "medium",
            "contradiction_list": [],
            "missing_lanes": ["not-an-object"],
            "schema_invalid_outputs": [],
            "stale_context_findings": [],
            "required_review_axes": ["architecture"],
            "coverage_status": [{"axis": "architecture", "status": "covered"}],
            "suggested_reviewer_families": [],
            "mcp_quiescence_snapshot": mcp_quiescence(),
            "aggregation_input_bundle": {
                "handoff_results_ref": [],
                "active_passes_ref": "active_passes:run-1",
                "missing_lane_classes_ref": [],
                "schema_invalid_outputs_ref": [],
                "aggregation_input_mode": "canonical",
            },
            "contract_provenance": provenance(),
        },
        "next_owner": "review-router",
    }
    check("aggregation_missing_lane_item_shape_blocks", harness_gate.gate_stage_output(bad_missing_lane_item, stage_owner="aggregator")["allow_next_stage"] is False, failures)

    check("apply_inheritance_bom_idempotent", apply_inheritance_bom_idempotent(), failures)
    check("handoff_write_error_is_structured", handoff_write_error_is_structured(), failures)
    check("runtime_cli_valid_manifest_exit_zero", runtime_cli_valid_manifest_exit_zero(), failures)
    check("runtime_cli_malformed_json_exit_one", runtime_cli_malformed_json_exit_one(), failures)
    check("session_validator_blocks_invalid_fork_closed_only", session_validator_blocks_invalid_fork_closed_only(), failures)
    check("gate_cli_blocks_next_owner_injection", gate_cli_blocks_next_owner_injection(), failures)
    check("handoff_cli_writes_decision_next_and_ledger", handoff_cli_writes_decision_next_and_ledger(), failures)
    check("handoff_cli_previous_judgment_lineage_blocks", handoff_cli_previous_judgment_lineage_blocks(), failures)

    result = {"smoke_status": "passed" if not failures else "failed", "failures": failures, "cases": CHECKS_RUN}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def apply_inheritance_bom_idempotent() -> bool:
    script = Path(__file__).with_name("apply-agents-inheritance.py")
    block = (
        "# Global Architecture Inheritance\n\n"
        "This project inherits the global Codex architecture by reference:\n\n"
        "- `${CODEX_HOME}/AGENTS.md`\n"
        "- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`\n"
        "- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`\n\n"
        "Do not copy the global architecture body into this project file. Keep project-specific rules below.\n\n"
        "## Validation Hook\n\n"
        "If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true` and run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.\n\n"
        "---\n\n"
        "# Repository Guidelines\n\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "AGENTS.md"
        target.write_text("\ufeff" + block, encoding="utf-8")
        result = subprocess.run([sys.executable, str(script), str(target)], capture_output=True, text=True, encoding="utf-8")
        text = target.read_text(encoding="utf-8-sig")
        return result.returncode == 0 and "already_inherits" in result.stdout and text.count("# Global Architecture Inheritance") == 1


def handoff_write_error_is_structured() -> bool:
    script = Path(__file__).with_name("harness_handoff.py")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        payload = base / "valid.json"
        active = base / "active.json"
        payload.write_text(json.dumps(worker_manifest(), ensure_ascii=False), encoding="utf-8")
        active.write_text(json.dumps(active_passes(), ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--stage-owner",
                "worker-router",
                "--expected-next-owner",
                "worker-layer",
                "--active-passes-json",
                str(active),
                "--input",
                str(payload),
                "--decision-out",
                str(base),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            return False
        return result.returncode == 1 and parsed.get("failure_class") == "io_error" and "Traceback" not in result.stderr


def runtime_cli_valid_manifest_exit_zero() -> bool:
    script = Path(__file__).with_name("validate-runtime-artifact.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "manifest.json"
        path.write_text(json.dumps(worker_manifest(), ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), "--stage-owner", "worker-router", "--input", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        parsed = json.loads(result.stdout)
        return result.returncode == 0 and parsed.get("validation_status") == "passed"


def runtime_cli_malformed_json_exit_one() -> bool:
    script = Path(__file__).with_name("validate-runtime-artifact.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "broken.json"
        path.write_text("{not-json", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), "--input", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        parsed = json.loads(result.stdout)
        return result.returncode == 1 and parsed.get("failure_class") == "input_invalid" and "Traceback" not in result.stderr


def session_validator_blocks_invalid_fork_closed_only() -> bool:
    script = Path(__file__).with_name("validate-session-runtime.py")
    events = [
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "agent architecture audit validate"}],
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "spawn-1",
                "arguments": json.dumps(
                    {
                        "agent_type": "context-manager",
                        "fork_context": True,
                        "message": "architecture_required=true",
                    }
                ),
            },
        },
        {
            "type": "event_msg",
            "payload": {
                "type": "collab_agent_spawn_end",
                "call_id": "spawn-1",
                "new_thread_id": "agent-closed-only",
                "new_agent_role": "context-manager",
                "new_agent_nickname": "ctx",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "close_agent",
                "call_id": "close-1",
                "arguments": json.dumps({"target": "agent-closed-only"}),
            },
        },
        {
            "type": "event_msg",
            "payload": {
                "type": "collab_close_end",
                "call_id": "close-1",
                "receiver_thread_id": "agent-closed-only",
                "receiver_agent_role": "context-manager",
                "status": "closed",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "spawn-worker",
                "arguments": json.dumps(
                    {
                        "agent_type": "worker",
                        "fork_context": False,
                        "message": "generic worker should not be used for architecture_required=true",
                    }
                ),
            },
        },
        {
            "type": "event_msg",
            "payload": {
                "type": "collab_agent_spawn_end",
                "call_id": "spawn-worker",
                "new_thread_id": "agent-generic-worker",
                "new_agent_role": "worker",
                "new_agent_nickname": "worker",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "spawn-aggregator",
                "arguments": json.dumps(
                    {
                        "agent_type": "aggregator",
                        "fork_context": False,
                        "message": "Summarize the work in prose and say aggregation is done.",
                    }
                ),
            },
        },
        {
            "type": "event_msg",
            "payload": {
                "type": "collab_agent_spawn_end",
                "call_id": "spawn-aggregator",
                "new_thread_id": "agent-aggregator",
                "new_agent_role": "aggregator",
                "new_agent_nickname": "agg",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "spawn-meta",
                "arguments": json.dumps(
                    {
                        "agent_type": "meta-judge",
                        "fork_context": False,
                        "message": "final output judgment_envelope aggregation review feedback_required=false",
                    }
                ),
            },
        },
        {
            "type": "event_msg",
            "payload": {
                "type": "collab_agent_spawn_end",
                "call_id": "spawn-meta",
                "new_thread_id": "agent-meta",
                "new_agent_role": "meta-judge",
                "new_agent_nickname": "meta",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "spawn_agent",
                "call_id": "spawn-thread-limit",
                "arguments": json.dumps(
                    {
                        "agent_type": "security-auditor",
                        "fork_context": False,
                        "message": "materialize review lane after router manifest",
                    }
                ),
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": "spawn-thread-limit",
                "output": "collab spawn failed: agent thread limit reached",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "shell_command",
                "call_id": "open-tool",
                "arguments": json.dumps({"command": "echo unfinished"}),
            },
        },
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "session.jsonl"
        path.write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in events), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), "--input", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        parsed = json.loads(result.stdout)
        codes = {error.get("code") for error in parsed.get("errors", [])}
        expected_codes = {
            "session.invalid_fork_agent_type_spawn",
            "session.physical_context_manager_spawned",
            "session.physical_context_manager_closed",
            "session.spawned_child_not_waited",
            "session.open_tool_calls",
            "session.generic_worker_role_used",
            "session.control_stage_physical_spawn_without_override",
            "session.physical_fanout_budget_exceeded",
            "session.aggregator_prose_only",
            "session.final_without_physical_bundle",
            "session.final_without_feedback_gate_evidence",
            "session.spawn_thread_limit_reached",
        }
        return (
            result.returncode == 1
            and parsed.get("validation_status") == "failed"
            and expected_codes <= codes
            and "Traceback" not in result.stderr
        )


def gate_cli_blocks_next_owner_injection() -> bool:
    script = Path(__file__).with_name("harness_gate.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "handoff.json"
        path.write_text(json.dumps(handoff_result_with_next_owner("review-router"), ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), "--stage-owner", "worker-layer", "--input", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        parsed = json.loads(result.stdout)
        nested = parsed.get("validation_result", {})
        return (
            result.returncode == 1
            and parsed.get("gate_status") == "blocked"
            and nested.get("validation_status") == "failed"
            and "Traceback" not in result.stderr
        )


def handoff_cli_writes_decision_next_and_ledger() -> bool:
    script = Path(__file__).with_name("harness_handoff.py")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        payload = base / "valid.json"
        active = base / "active.json"
        decision = base / "decision.json"
        next_input = base / "next.json"
        ledger = base / "ledger.jsonl"
        payload.write_text(json.dumps(worker_manifest(), ensure_ascii=False), encoding="utf-8")
        active.write_text(json.dumps(active_passes(), ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--stage-owner",
                "worker-router",
                "--expected-next-owner",
                "worker-layer",
                "--expected-context-packet-version",
                "ctx-1",
                "--active-passes-json",
                str(active),
                "--input",
                str(payload),
                "--decision-out",
                str(decision),
                "--next-input-out",
                str(next_input),
                "--ledger-out",
                str(ledger),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        parsed = json.loads(result.stdout)
        written = json.loads(decision.read_text(encoding="utf-8"))
        return (
            result.returncode == 0
            and parsed.get("handoff_status") == "allowed"
            and written.get("expected_context_packet_version") == "ctx-1"
            and next_input.is_file()
            and ledger.is_file()
            and "Traceback" not in result.stderr
        )


def handoff_cli_previous_judgment_lineage_blocks() -> bool:
    script = Path(__file__).with_name("harness_handoff.py")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        previous = base / "previous.json"
        current = base / "current.json"
        previous.write_text(json.dumps(judgment_with_loop(feedback=True, attempt=1, repeat=1, blockers=[blocker()]), ensure_ascii=False), encoding="utf-8")
        current.write_text(json.dumps(judgment_with_loop(feedback=True, attempt=2, repeat=2, blockers=[]), ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--stage-owner",
                "meta-judge",
                "--input",
                str(current),
                "--previous-judgment-json",
                str(previous),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        parsed = json.loads(result.stdout)
        nested = parsed.get("gate_decision", {}).get("validation_result", {})
        return (
            result.returncode == 1
            and parsed.get("failure_class") == "loop_invalid"
            and nested.get("validation_status") == "failed"
            and parsed.get("previous_judgment_checked") is True
            and "Traceback" not in result.stderr
        )


if __name__ == "__main__":
    raise SystemExit(main())
