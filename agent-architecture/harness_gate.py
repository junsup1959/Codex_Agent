#!/usr/bin/env python3
"""Gate a stage output before the caller performs the next handoff.

This script gives runtime validation enforcement teeth: a failed runtime
artifact validation becomes a blocked handoff, while valid feedback judgments
preserve feedback re-entry metadata.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

STAGE_HANDOFF_POLICY = {
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

DEFAULT_FAILURE_ROUTE = {
    "allow_next_stage": False,
    "next_owner": None,
    "next_loop_start": None,
    "feedback_required": False,
    "route_kind": "retry_same_stage",
}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_runtime_validator():
    script = Path(__file__).with_name("validate-runtime-artifact.py")
    spec = importlib.util.spec_from_file_location("codex_runtime_artifact_validator", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime validator from {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME_VALIDATOR = load_runtime_validator()


def load_json(path: str | None) -> Any:
    if path in (None, "-"):
        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def gate_stage_output(
    payload: Any,
    *,
    stage_owner: str,
    artifact: str = "auto",
    expected_next_owner: str | None = None,
    expected_source_ref: str | None = None,
    expected_context_packet_version: str | None = None,
    active_passes: Any | None = None,
    stage_passes: Any | None = None,
    review_results: Any | None = None,
    previous_judgment: Any | None = None,
) -> dict[str, Any]:
    validation = RUNTIME_VALIDATOR.validate_payload(payload, artifact=artifact, stage_owner=stage_owner)
    passed = validation["validation_status"] == "passed"
    next_owner = derive_next_owner(payload, stage_owner, validation["artifact_type"]) if passed else DEFAULT_FAILURE_ROUTE["next_owner"]
    next_loop_start = derive_next_loop_start(payload, validation["artifact_type"]) if passed else DEFAULT_FAILURE_ROUTE["next_loop_start"]
    feedback_required = derive_feedback_required(payload, validation["artifact_type"]) if passed else DEFAULT_FAILURE_ROUTE["feedback_required"]
    decision = {
        "gate_status": "passed" if passed else "blocked",
        "runtime_validation_required": True,
        "stage_owner": stage_owner,
        "artifact_type": validation["artifact_type"],
        "expected_next_owner": expected_next_owner,
        "expected_source_ref": expected_source_ref,
        "expected_context_packet_version": expected_context_packet_version,
        "previous_judgment_checked": previous_judgment is not None,
        "schema_status": validation["schema_status"],
        "failure_class": validation["failure_class"],
        "allow_next_stage": passed,
        "next_owner": next_owner,
        "next_loop_start": next_loop_start,
        "feedback_required": feedback_required,
        "route_kind": derive_route_kind(passed=passed, artifact_type=validation["artifact_type"], feedback_required=feedback_required),
        "validation_result": validation,
    }
    allowed = STAGE_HANDOFF_POLICY.get(stage_owner)
    if allowed is None:
        return block(decision, "gate.unknown_stage", "stage_owner", f"unknown stage {stage_owner}")
    if passed and validation["artifact_type"] not in allowed:
        return block(decision, "gate.artifact_policy", "artifact_type", f"{stage_owner} cannot hand off {validation['artifact_type']}")
    if passed and isinstance(payload, dict) and isinstance(payload.get("next_owner"), str) and payload["next_owner"] != next_owner:
        return block(decision, "gate.next_owner_injection", "$.next_owner", f"payload next_owner {payload['next_owner']!r} does not match derived next_owner {next_owner!r}")
    if passed and expected_source_ref:
        source_ref = derive_source_ref(payload, validation["artifact_type"])
        if source_ref != expected_source_ref:
            return block(decision, "gate.source_ref_mismatch", "expected_source_ref", f"expected {expected_source_ref!r}, got {source_ref!r}")
    if passed and expected_context_packet_version:
        context_version = derive_context_packet_version(payload, validation["artifact_type"])
        if context_version != expected_context_packet_version:
            return block(decision, "gate.context_version_mismatch", "expected_context_packet_version", f"expected {expected_context_packet_version!r}, got {context_version!r}")
    if passed and validation["artifact_type"] == "judgment_envelope" and previous_judgment is not None:
        lineage = validate_judgment_lineage(payload, previous_judgment)
        if not lineage["ok"]:
            return block(decision, lineage["code"], "previous_judgment", lineage["message"], failure_class="loop_invalid")
    if passed and stage_owner == "meta-judge" and validation["artifact_type"] == "judgment_envelope":
        completion = validate_completion_evidence(payload, stage_passes, review_results, active_passes)
        if not completion["ok"]:
            return block(decision, completion["code"], completion["path"], completion["message"], failure_class=completion["failure_class"])
    if passed and expected_next_owner and expected_next_owner != next_owner:
        if stage_owner in {"worker-router", "review-router"} and expected_next_owner in {"worker-layer", "review-layer"}:
            required_layer = "worker-layer" if stage_owner == "worker-router" else "review-layer"
            if expected_next_owner != required_layer:
                return block(decision, "gate.router_layer_mismatch", "expected_next_owner", f"{stage_owner} can materialize only to {required_layer}")
            materialized = validate_materialization(payload, active_passes)
            if materialized["ok"]:
                decision["next_owner"] = expected_next_owner
                decision["route_kind"] = "proceed"
                return decision
            return block(decision, materialized["code"], "active_passes", materialized["message"], failure_class=materialized["failure_class"])
        return block(decision, "gate.expected_next_owner", "expected_next_owner", f"expected {expected_next_owner!r}, got {next_owner!r}")
    return decision


def block(decision: dict[str, Any], code: str, path: str, message: str, *, failure_class: str = "contract_invalid") -> dict[str, Any]:
    decision["gate_status"] = "blocked"
    decision["allow_next_stage"] = False
    decision["feedback_required"] = False
    decision["next_owner"] = DEFAULT_FAILURE_ROUTE["next_owner"]
    decision["next_loop_start"] = DEFAULT_FAILURE_ROUTE["next_loop_start"]
    decision["route_kind"] = DEFAULT_FAILURE_ROUTE["route_kind"]
    decision["failure_class"] = failure_class
    decision["schema_status"] = "invalid"
    validation_result = decision["validation_result"]
    validation_result["validation_status"] = "failed"
    validation_result["schema_status"] = "invalid"
    validation_result["failure_class"] = failure_class
    validation_result.setdefault("errors", []).append({"code": code, "path": path, "message": message})
    return decision


def derive_next_owner(payload: Any, stage_owner: str, artifact_type: str) -> str | None:
    if stage_owner == "orchestrator" and artifact_type == "orchestration_request":
        return "context-manager"
    if stage_owner == "context-manager" and artifact_type == "context_packet":
        return "task-planner"
    if stage_owner == "task-planner" and artifact_type == "execution_plan":
        return "worker-router"
    if stage_owner == "worker-router" or stage_owner == "review-router":
        return "caller"
    if stage_owner == "worker-layer":
        return "aggregator"
    if stage_owner == "review-layer":
        return "meta-judge"
    if stage_owner == "aggregator" and artifact_type == "aggregation_packet":
        return "review-router"
    if stage_owner == "aggregator" and artifact_type == "blocked_aggregation":
        return "meta-judge"
    if stage_owner == "meta-judge" and isinstance(payload, dict):
        judgment = payload.get("judgment_envelope", payload)
        if isinstance(judgment, dict):
            return judgment.get("next_owner")
    return None


def derive_route_kind(*, passed: bool, artifact_type: str, feedback_required: bool) -> str:
    if not passed:
        return "retry_same_stage"
    if artifact_type == "judgment_envelope" and feedback_required:
        return "feedback_restart"
    return "proceed"


def validate_materialization(payload: Any, active_passes: Any | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"ok": False, "code": "materialization.payload", "failure_class": "unmaterialized_lane", "message": "payload is not an object"}
    manifest = payload.get("launch_manifest", payload)
    if not isinstance(manifest, dict):
        return {"ok": False, "code": "materialization.manifest", "failure_class": "unmaterialized_lane", "message": "launch_manifest missing"}
    children = manifest.get("children")
    if not isinstance(children, list):
        return {"ok": False, "code": "materialization.children", "failure_class": "unmaterialized_lane", "message": "launch_manifest.children missing"}
    if active_passes is not None and not (isinstance(active_passes, dict) and isinstance(active_passes.get("active_passes"), list)):
        return {"ok": False, "code": "materialization.active_passes_shape", "failure_class": "no_wait_handle", "message": "active_passes must be an object with active_passes[]"}
    passes = extract_active_passes(active_passes)
    if not passes:
        return {"ok": False, "code": "materialization.active_passes_missing", "failure_class": "unmaterialized_lane", "message": "active_passes required before layer handoff"}
    ledger_payload = active_passes if isinstance(active_passes, dict) else {"active_passes": passes}
    ledger_validation = RUNTIME_VALIDATOR.validate_payload(ledger_payload, artifact="active_passes")
    if ledger_validation["validation_status"] != "passed":
        return {"ok": False, "code": "materialization.active_passes_invalid", "failure_class": "no_wait_handle", "message": f"active_passes invalid: {ledger_validation['errors']}"}
    lane_by_id = {child.get("lane_id"): child for child in children if isinstance(child, dict)}
    lane_ids = set(lane_by_id)
    pass_lane_ids: set[Any] = set()
    for index, item in enumerate(passes):
        validation = RUNTIME_VALIDATOR.validate_payload({"active_pass": item}, artifact="active_pass")
        if validation["validation_status"] != "passed":
            return {"ok": False, "code": "materialization.active_pass_invalid", "failure_class": "no_wait_handle", "message": f"active_passes[{index}] invalid: {validation['errors']}"}
        lane_id = item.get("lane_id")
        if lane_id not in lane_by_id:
            return {"ok": False, "code": "materialization.active_pass_stray_lane", "failure_class": "no_wait_handle", "message": f"active_passes[{index}] references unknown lane {lane_id!r}"}
        if lane_id in pass_lane_ids:
            return {"ok": False, "code": "materialization.active_pass_duplicate_lane", "failure_class": "no_wait_handle", "message": f"active_passes has duplicate materialization for lane {lane_id!r}"}
        pass_lane_ids.add(lane_id)
        lane = lane_by_id[lane_id]
        for field_name in ("context_packet_version", "owned_scope", "merge_point", "agent_category", "agent_role"):
            if item.get(field_name) != lane.get(field_name):
                return {"ok": False, "code": "materialization.active_pass_mismatch", "failure_class": "no_wait_handle", "message": f"active_passes[{index}].{field_name} does not match lane {lane_id}"}
        if item.get("role") != lane.get("agent_role"):
            return {"ok": False, "code": "materialization.active_pass_role_mismatch", "failure_class": "no_wait_handle", "message": f"active_passes[{index}].role must match lane agent_role {lane_id}"}
        if item.get("status") != "active":
            return {"ok": False, "code": "materialization.active_pass_status", "failure_class": "no_wait_handle", "message": f"active_passes[{index}].status must be active before layer handoff"}
        mode = lane.get("spawn_context_mode")
        if mode == "fork_context":
            return {"ok": False, "code": "materialization.specialist_fork_context", "failure_class": "contract_invalid", "message": f"specialist lane {lane_id} must use scoped_packet or scoped_packet_with_waiver"}
        if mode == "scoped_packet_with_waiver" and not isinstance(lane.get("spawn_context_waiver"), dict):
            return {"ok": False, "code": "materialization.missing_context_waiver", "failure_class": "contract_invalid", "message": f"specialist lane {lane_id} requires spawn_context_waiver"}
    expected_attempt = manifest.get("loop_control", {}).get("loop_attempt") if isinstance(manifest.get("loop_control"), dict) else None
    if expected_attempt is not None:
        for index, item in enumerate(passes):
            if item.get("loop_attempt") != expected_attempt:
                return {"ok": False, "code": "materialization.loop_attempt_mismatch", "failure_class": "no_wait_handle", "message": f"active_passes[{index}].loop_attempt does not match manifest loop_control.loop_attempt"}
    missing = sorted(lane_ids - pass_lane_ids)
    if missing:
        return {"ok": False, "code": "materialization.lane_unmaterialized", "failure_class": "unmaterialized_lane", "message": f"unmaterialized lanes: {missing}"}
    return {"ok": True}


def extract_active_passes(active_passes: Any | None) -> list[dict[str, Any]]:
    if isinstance(active_passes, dict) and isinstance(active_passes.get("active_passes"), list):
        return [item for item in active_passes["active_passes"] if isinstance(item, dict)]
    return []


def extract_stage_passes(stage_passes: Any | None) -> list[dict[str, Any]]:
    if isinstance(stage_passes, dict) and isinstance(stage_passes.get("stage_passes"), list):
        return [item for item in stage_passes["stage_passes"] if isinstance(item, dict)]
    if isinstance(stage_passes, list):
        return [item for item in stage_passes if isinstance(item, dict)]
    return []


def extract_handoff_results(review_results: Any | None) -> list[dict[str, Any]]:
    if isinstance(review_results, dict):
        if isinstance(review_results.get("review_results"), list):
            source = review_results["review_results"]
        elif isinstance(review_results.get("handoff_results"), list):
            source = review_results["handoff_results"]
        else:
            source = []
    elif isinstance(review_results, list):
        source = review_results
    else:
        source = []
    results = []
    for item in source:
        if isinstance(item, dict) and isinstance(item.get("handoff_result"), dict):
            results.append(item["handoff_result"])
        elif isinstance(item, dict):
            results.append(item)
    return results


def validate_completion_evidence(payload: Any, stage_passes: Any | None, review_results: Any | None, active_passes: Any | None) -> dict[str, Any]:
    judgment = extract_judgment(payload)
    if judgment is None:
        return {"ok": False, "code": "completion.judgment_shape", "path": "judgment_envelope", "message": "judgment_envelope required", "failure_class": "contract_invalid"}
    judgment_loop_id = judgment.get("loop_id")
    loop_control = judgment.get("loop_control") if isinstance(judgment.get("loop_control"), dict) else {}
    judgment_loop_attempt = loop_control.get("loop_attempt")
    carryover = judgment.get("loop_carryover") if isinstance(judgment.get("loop_carryover"), dict) else {}
    judgment_context_packet_version = carryover.get("context_packet_version")
    stage_rows = extract_stage_passes(stage_passes)
    if not stage_rows:
        return {"ok": False, "code": "completion.stage_passes_missing", "path": "stage_passes", "message": "meta-judge completion requires stage_passes evidence", "failure_class": "contract_invalid"}
    meta_ref = judgment.get("meta_judge_stage_pass_ref")
    meta_match = None
    for row in stage_rows:
        validation = RUNTIME_VALIDATOR.validate_payload({"stage_pass": row}, artifact="stage_pass")
        if validation["validation_status"] != "passed":
            return {"ok": False, "code": "completion.stage_pass_invalid", "path": "stage_passes", "message": f"invalid stage_pass: {validation['errors']}", "failure_class": "contract_invalid"}
        refs = {row.get("stage_pass_id"), row.get("artifact_ref"), f"stage_pass:{row.get('stage_pass_id')}"}
        if meta_ref in refs:
            meta_match = row
    if meta_match is None:
        return {"ok": False, "code": "completion.meta_stage_ref_dangling", "path": "judgment_envelope.meta_judge_stage_pass_ref", "message": "meta_judge_stage_pass_ref does not resolve to stage_passes", "failure_class": "contract_invalid"}
    if meta_match.get("stage_owner") != "meta-judge" or meta_match.get("artifact_name") != "judgment_envelope" or meta_match.get("schema_status") != "valid":
        return {"ok": False, "code": "completion.meta_stage_mismatch", "path": "stage_passes", "message": "resolved meta stage pass is not a valid meta-judge judgment pass", "failure_class": "contract_invalid"}
    if meta_match.get("stage_status") != "closed":
        return {"ok": False, "code": "completion.meta_stage_open", "path": "stage_passes", "message": "meta-judge stage pass must be closed before final/feedback claim", "failure_class": "runtime_residue"}
    if meta_match.get("loop_id") != judgment_loop_id:
        return {"ok": False, "code": "completion.meta_stage_loop_mismatch", "path": "stage_passes", "message": "meta_judge_stage_pass_ref must resolve to the same loop_id as the judgment", "failure_class": "contract_invalid"}
    if judgment_loop_attempt is not None and meta_match.get("loop_attempt") != judgment_loop_attempt:
        return {"ok": False, "code": "completion.meta_stage_attempt_mismatch", "path": "stage_passes", "message": "meta_judge_stage_pass_ref must resolve to the same loop_attempt as the judgment", "failure_class": "contract_invalid"}
    if judgment_context_packet_version and meta_match.get("context_packet_version") != judgment_context_packet_version:
        return {"ok": False, "code": "completion.meta_stage_context_mismatch", "path": "stage_passes", "message": "meta_judge_stage_pass_ref must resolve to the same context_packet_version as the judgment", "failure_class": "contract_invalid"}
    for row in extract_active_passes(active_passes):
        if row.get("status") in {"active", "pending_init", "running"}:
            return {"ok": False, "code": "completion.active_pass_residue", "path": "active_passes", "message": "active child pass remains open during completion claim", "failure_class": "runtime_residue"}
    waivers = judgment.get("review_waivers") if isinstance(judgment.get("review_waivers"), list) else []
    review_refs = judgment.get("review_input_refs") if isinstance(judgment.get("review_input_refs"), list) else []
    if review_refs:
        result_rows = extract_handoff_results(review_results)
        if not result_rows:
            return {"ok": False, "code": "completion.review_results_missing", "path": "review_results", "message": "review_input_refs require reviewer handoff_result evidence", "failure_class": "contract_invalid"}
        resolved_refs: set[Any] = set()
        for row in result_rows:
            validation = RUNTIME_VALIDATOR.validate_payload({"handoff_result": row}, artifact="handoff_result")
            if validation["validation_status"] != "passed":
                return {"ok": False, "code": "completion.review_result_invalid", "path": "review_results", "message": f"invalid reviewer handoff_result: {validation['errors']}", "failure_class": "contract_invalid"}
            if row.get("pass_status") != "returned":
                return {"ok": False, "code": "completion.review_not_returned", "path": "review_results", "message": "reviewer result must be returned before completion claim", "failure_class": "runtime_residue"}
            if judgment_context_packet_version and row.get("context_packet_version") != judgment_context_packet_version:
                return {"ok": False, "code": "completion.review_context_mismatch", "path": "review_results", "message": "reviewer handoff_result must use the same context_packet_version as the judgment", "failure_class": "contract_invalid"}
            resolved_refs.update({row.get("artifact_ref"), row.get("pass_id"), f"handoff_result:{row.get('pass_id')}"})
        missing = [ref for ref in review_refs if ref not in resolved_refs]
        if missing:
            return {"ok": False, "code": "completion.review_ref_dangling", "path": "judgment_envelope.review_input_refs", "message": f"review refs do not resolve: {missing}", "failure_class": "contract_invalid"}
    elif not waivers:
        return {"ok": False, "code": "completion.review_evidence_missing", "path": "judgment_envelope.review_input_refs", "message": "completion requires reviewer results or explicit review waivers", "failure_class": "contract_invalid"}
    return {"ok": True}


def extract_judgment(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    judgment = payload.get("judgment_envelope", payload)
    return judgment if isinstance(judgment, dict) else None


def validate_judgment_lineage(payload: Any, previous_judgment: Any) -> dict[str, Any]:
    current = extract_judgment(payload)
    previous = extract_judgment(previous_judgment)
    if current is None or previous is None:
        return {"ok": False, "code": "lineage.judgment_shape", "message": "current and previous judgment_envelope are required"}
    current_control = current.get("loop_control")
    previous_control = previous.get("loop_control")
    current_carryover = current.get("loop_carryover")
    previous_carryover = previous.get("loop_carryover")
    if not all(isinstance(item, dict) for item in (current_control, previous_control, current_carryover, previous_carryover)):
        return {"ok": False, "code": "lineage.loop_shape", "message": "loop_control and loop_carryover are required in both judgments"}
    if current.get("loop_id") != previous.get("loop_id"):
        return {"ok": False, "code": "lineage.loop_id", "message": "loop_id must stay stable across feedback loops"}
    prior_source_ref = previous_carryover.get("source_judgment_ref")
    current_source_ref = current_carryover.get("source_judgment_ref")
    if prior_source_ref and current_source_ref != prior_source_ref:
        return {"ok": False, "code": "lineage.source_judgment_ref", "message": "source_judgment_ref must preserve prior judgment lineage"}
    if current_control.get("loop_attempt", 0) <= previous_control.get("loop_attempt", 0):
        return {"ok": False, "code": "lineage.loop_attempt", "message": "loop_attempt must increase across feedback loops"}
    if current_control.get("repeat_feedback_count", 0) < previous_control.get("repeat_feedback_count", 0):
        return {"ok": False, "code": "lineage.repeat_feedback_count", "message": "repeat_feedback_count must not decrease"}
    if not set(current_carryover.get("preserved_allowed_scope", [])) <= set(previous_carryover.get("preserved_allowed_scope", [])):
        return {"ok": False, "code": "lineage.scope_widened", "message": "preserved_allowed_scope must not widen on feedback restart"}
    previous_blockers = previous_carryover.get("unresolved_blockers", [])
    current_blockers = current_carryover.get("unresolved_blockers", [])
    progress_delta = current_control.get("progress_delta", [])
    progress_changed = any(
        delta.get("changed_blocker_fingerprint")
        or delta.get("new_evidence_refs")
        or delta.get("new_artifact_refs")
        or delta.get("changed_context_packet_version")
        for delta in progress_delta
        if isinstance(delta, dict)
    )
    same_blockers = previous_blockers == current_blockers
    repeat_count = current_control.get("repeat_feedback_count", 0)
    previous_repeat_count = previous_control.get("repeat_feedback_count", 0)
    if same_blockers and not progress_changed and repeat_count <= previous_repeat_count:
        return {"ok": False, "code": "lineage.repeat_count_not_incremented", "message": "repeat_feedback_count must increase when blocker state repeats without progress"}
    if current.get("feedback_required") is True and same_blockers and not progress_changed and repeat_count >= 2:
        action = str(current_control.get("no_progress_action", ""))
        if "respond to user" not in action and "schema/tool/doc repair" not in action:
            return {"ok": False, "code": "lineage.no_progress_escape", "message": "repeated no-progress feedback must stop for user response or schema/tool/doc repair"}
    if previous_blockers and current.get("feedback_required") is True and not current_blockers and not progress_changed:
        return {"ok": False, "code": "lineage.blocker_dropped", "message": "previous unresolved blockers cannot disappear without progress evidence"}
    if previous_blockers and current.get("feedback_required") is False and not progress_changed:
        return {"ok": False, "code": "lineage.final_without_progress", "message": "final output after prior blockers requires progress evidence"}
    return {"ok": True}


def derive_next_loop_start(payload: Any, artifact_type: str) -> str | None:
    if artifact_type == "judgment_envelope" and isinstance(payload, dict):
        judgment = payload.get("judgment_envelope", payload)
        if isinstance(judgment, dict):
            return judgment.get("next_loop_start")
    return None


def derive_source_ref(payload: Any, artifact_type: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    artifact_payload = payload.get(artifact_type, payload)
    source_fields = (
        "source_parent_ref",
        "source_orchestration_request_ref",
        "source_context_packet_ref",
        "source_execution_plan_ref",
        "source_aggregation_packet_ref",
        "source_blocked_aggregation_ref",
        "source_launch_manifest_ref",
    )
    if isinstance(artifact_payload, dict):
        for field_name in source_fields:
            if isinstance(artifact_payload.get(field_name), str) and artifact_payload[field_name]:
                return artifact_payload[field_name]
    return None


def derive_context_packet_version(payload: Any, artifact_type: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    artifact_payload = payload.get(artifact_type, payload)
    if isinstance(artifact_payload, dict) and isinstance(artifact_payload.get("context_packet_version"), str):
        return artifact_payload["context_packet_version"]
    if artifact_type == "judgment_envelope" and isinstance(artifact_payload, dict):
        carryover = artifact_payload.get("loop_carryover")
        if isinstance(carryover, dict) and isinstance(carryover.get("context_packet_version"), str):
            return carryover["context_packet_version"]
    return None


def derive_feedback_required(payload: Any, artifact_type: str) -> bool:
    if artifact_type == "judgment_envelope" and isinstance(payload, dict):
        judgment = payload.get("judgment_envelope", payload)
        if isinstance(judgment, dict) and isinstance(judgment.get("feedback_required"), bool):
            return judgment["feedback_required"]
    return False


def main(argv: list[str]) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Block or allow a Codex stage handoff.")
    parser.add_argument("--stage-owner", required=True, choices=sorted(STAGE_HANDOFF_POLICY), help="stage that emitted the JSON")
    parser.add_argument("--input", "-i", help="JSON file path; omit or use - for stdin")
    parser.add_argument("--artifact", default="auto", help="artifact override for validate-runtime-artifact.py")
    parser.add_argument("--expected-next-owner", help="block if derived next owner does not match")
    parser.add_argument("--expected-source-ref", help="block if source lineage ref does not match")
    parser.add_argument("--expected-context-packet-version", help="block if context packet version does not match")
    parser.add_argument("--active-passes-json", help="active_passes JSON for router materialization and completion checks")
    parser.add_argument("--stage-passes-json", help="stage_passes JSON for meta-judge completion evidence")
    parser.add_argument("--review-results-json", help="review handoff_result JSON bundle for meta-judge completion evidence")
    parser.add_argument("--previous-judgment-json", help="previous judgment_envelope JSON for feedback lineage checks")
    args = parser.parse_args(argv)
    try:
        payload = load_json(args.input)
        active_passes = load_json(args.active_passes_json) if args.active_passes_json else None
        stage_passes = load_json(args.stage_passes_json) if args.stage_passes_json else None
        review_results = load_json(args.review_results_json) if args.review_results_json else None
        previous_judgment = load_json(args.previous_judgment_json) if args.previous_judgment_json else None
        decision = gate_stage_output(
            payload,
            stage_owner=args.stage_owner,
            artifact=args.artifact,
            expected_next_owner=args.expected_next_owner,
            expected_source_ref=args.expected_source_ref,
            expected_context_packet_version=args.expected_context_packet_version,
            active_passes=active_passes,
            stage_passes=stage_passes,
            review_results=review_results,
            previous_judgment=previous_judgment,
        )
    except json.JSONDecodeError as exc:
        decision = cli_exception_decision(args, "input_invalid", "json.decode", exc)
    except OSError as exc:
        decision = cli_exception_decision(args, "io_error", "io.read", exc)
    except Exception as exc:  # CLI must return machine-readable failure.
        decision = cli_exception_decision(args, "validator_bug", "harness_gate.exception", exc)
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0 if decision["gate_status"] == "passed" else 1


def cli_exception_decision(args: argparse.Namespace, failure_class: str, code: str, exc: Exception) -> dict[str, Any]:
    return {
        "gate_status": "blocked",
        "runtime_validation_required": True,
        "stage_owner": args.stage_owner,
        "artifact_type": args.artifact,
        "schema_status": "invalid",
        "failure_class": failure_class,
        "allow_next_stage": False,
        "next_owner": DEFAULT_FAILURE_ROUTE["next_owner"],
        "next_loop_start": DEFAULT_FAILURE_ROUTE["next_loop_start"],
        "feedback_required": DEFAULT_FAILURE_ROUTE["feedback_required"],
        "route_kind": DEFAULT_FAILURE_ROUTE["route_kind"],
        "expected_next_owner": args.expected_next_owner,
        "expected_source_ref": args.expected_source_ref,
        "expected_context_packet_version": args.expected_context_packet_version,
        "previous_judgment_checked": bool(args.previous_judgment_json),
        "validation_result": {
            "validation_status": "failed",
            "schema_status": "invalid",
            "failure_class": failure_class,
            "errors": [{"code": code, "path": args.input or "stdin", "message": str(exc)}],
        },
    }


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
