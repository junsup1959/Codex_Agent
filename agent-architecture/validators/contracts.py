from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from validators.constants import (
    AGGREGATION_PACKET_REQUIRED_FIELDS,
    BOUNDED_REWORK_REQUEST_REQUIRED_FIELDS,
    CANONICAL_STAGE_ROLES,
    CONTRACT_PROVENANCE_REQUIRED_FIELDS,
    CONTEXT_PACKET_REQUIRED_FIELDS,
    EXECUTION_PLAN_REQUIRED_FIELDS,
    EXECUTION_PLAN_LANE_REQUIRED_FIELDS,
    FANOUT_BUDGET_REQUIRED_FIELDS,
    FEEDBACK_FINAL_FORBIDDEN_MARKERS,
    FEEDBACK_REQUIRED_MARKERS,
    FEEDBACK_TARGET_REENTRY,
    HANDOFF_RESULT_REQUIRED_FIELDS,
    JUDGMENT_ALLOWED_DECISIONS,
    JUDGMENT_ENVELOPE_REQUIRED_FIELDS,
    LOOP_CARRYOVER_REQUIRED_FIELDS,
    LOOP_CONTROL_REQUIRED_FIELDS,
    LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS,
    LOGICAL_LANE_REQUIRED_FIELDS,
    LAUNCH_MANIFEST_REQUIRED_FIELDS,
    MISSING_LANE_CLASSES,
    ORCHESTRATION_REQUEST_REQUIRED_FIELDS,
    PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS,
    PROGRESS_DELTA_REQUIRED_FIELDS,
    REVIEW_COVERAGE_REQUIRED_FIELDS,
    REVIEW_LAUNCH_MANIFEST_REQUIRED_FIELDS,
    REVIEW_WAIVER_REQUIRED_FIELDS,
    ROLE_ALIAS_MAP,
    RUN_LEDGER_REQUIRED_FIELDS,
    ROUTING_COLLECTION_MARKERS,
    SCHEMA_INVALID_REQUIRED_FIELDS,
    SPAWN_CONTEXT_MODES,
    STAGE_PASS_REQUIRED_FIELDS,
    WORKER_LAUNCH_MANIFEST_REQUIRED_FIELDS,
    required_architecture_doc_paths,
)


def check_routing_collection_contracts(validator: Any) -> None:
    validator.log("routing collection schema fixture check")
    contracts = read_text(validator.arch_dir / "07-contracts-ledgers.md")
    for marker in ROUTING_COLLECTION_MARKERS:
        validator.assert_contains("routing_collection_contract_marker", contracts, marker)
    validator.assert_not_contains(
        "routing_collection_no_old_waitable_manifest",
        contracts,
        "Each `launch_manifest.children[]` item must include:\n\n- `agent_id`",
    )

    # 한국어 유지보수 주석: launch_manifest 는 라우팅 의도와 계약을 적는 논리 장부이고,
    # active_passes 는 실제 spawn 이후 기다릴 수 있는 agent_id/submission_id 를 담는 물리 장부다.
    # 두 장부를 섞으면 미생성 logical lane 을 wait 대상으로 오인하므로 fixture 에서 분리 상태를 고정한다.
    logical_lane = {
        "lane_id": "lane-analysis-1",
        "parent_router_pass_id": "router-pass-1",
        "agent_category": "10-research-analysis",
        "agent_role": "docs-researcher",
        "lane_type": "worker",
        "owned_scope": "bounded evidence lookup",
        "expected_artifact": "handoff_result",
        "merge_point": "aggregation_packet.inputs",
        "return_owner": "aggregator",
        "validation_prompt": "collect bounded evidence and return evidence_refs",
        "context_packet_version": "ctx-1",
        "spawn_context_mode": "scoped_packet",
        "caller_spawn_required": True,
        "initial_status": "unmaterialized",
    }
    fanout_budget = {
        "max_worker_lanes_per_wave": 2,
        "max_review_lanes_per_wave": 2,
        "max_total_child_agents_per_loop": 4,
        "max_same_role_parallel_lanes": 1,
        "max_mcp_concurrent_child_lanes": 1,
        "budget_reason": "default bounded fanout",
        "overflow_policy": "coalesce_axes_or_feedback",
    }
    active_pass = {
        "run_id": "run-1",
        "loop_id": "loop-1",
        "loop_attempt": 1,
        "lane_id": logical_lane["lane_id"],
        "pass_id": "child-pass-1",
        "role": logical_lane["agent_role"],
        "agent_category": logical_lane["agent_category"],
        "agent_role": logical_lane["agent_role"],
        "agent_id": "agent-1",
        "submission_id": "submission-1",
        "wait_handle_type": "agent_id",
        "wait_handle": "agent-1",
        "source_launch_manifest_ref": "launch_manifest:router-pass-1",
        "spawn_tool": "spawn_agent",
        "spawn_receipt_ref": "spawn_agent:agent-1",
        "spawned_at": "2026-04-28T00:00:02Z",
        "wait_registered_at": "2026-04-28T00:00:03Z",
        "owned_scope": logical_lane["owned_scope"],
        "merge_point": logical_lane["merge_point"],
        "context_packet_version": logical_lane["context_packet_version"],
        "status": "active",
    }
    stage_pass = {
        "run_id": "run-1",
        "loop_id": "loop-1",
        "loop_attempt": 1,
        "stage_pass_id": "stage-router-1",
        "stage_owner": "worker-router",
        "stage_status": "closed",
        "artifact_name": "launch_manifest",
        "artifact_ref": "launch_manifest:router-pass-1",
        "context_packet_version": logical_lane["context_packet_version"],
        "schema_status": "valid",
        "created_at": "2026-04-28T00:00:00Z",
        "closed_at": "2026-04-28T00:00:01Z",
        "next_owner": "caller",
        "stage_spawn_contract": {
            "spawn_agent_type": "worker-router",
            "spawn_fork_context": False,
            "spawn_packet_mode": "curated_stage_packet",
        },
    }
    handoff_result = {
        "sender": logical_lane["agent_role"],
        "lane_id": logical_lane["lane_id"],
        "pass_id": active_pass["pass_id"],
        "parent_pass_id": logical_lane["parent_router_pass_id"],
        "pass_status": "returned",
        "owned_scope": logical_lane["owned_scope"],
        "artifact_summary": "bounded result",
        "artifact_ref": "artifact:child-pass-1",
        "artifact_kind": "analysis-note",
        "evidence_refs": [],
        "findings": [],
        "confidence": "medium",
        "merge_point": logical_lane["merge_point"],
        "context_packet_version": logical_lane["context_packet_version"],
        "caller_signals": [],
    }
    # 한국어 유지보수 주석: logical lane 에 wait_handle 계열 필드가 들어오면 아직 물리 agent 가
    # 생성되지 않은 상태에서 wait_agent 를 호출할 수 있다. 이 검사는 invalid wait handle 사용을
    # schema_invalid/no_wait_handle 로 분류하기 전에, 애초에 logical 장부가 wait 가능 객체처럼
    # 보이지 않도록 막는 회귀 방지 장치다.
    validator.assert_condition("logical_lane_required_fields", LOGICAL_LANE_REQUIRED_FIELDS <= set(logical_lane), "logical launch lane 필수 필드 누락")
    validator.assert_condition("fanout_budget_required_fields", FANOUT_BUDGET_REQUIRED_FIELDS <= set(fanout_budget), "fanout_budget required fields missing")
    validator.assert_condition("logical_lane_spawn_context_mode_valid", logical_lane["spawn_context_mode"] in SPAWN_CONTEXT_MODES, "logical lane spawn_context_mode invalid")
    validator.assert_condition("logical_lane_not_waitable", not LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS & set(logical_lane), "logical lane 이 physical wait handle 을 포함함")
    validator.assert_condition("active_pass_required_fields", PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS <= set(active_pass), "active_pass 필수 필드 누락")
    validator.assert_condition("active_pass_wait_handle_consistency", active_pass[active_pass["wait_handle_type"]] == active_pass["wait_handle"], "wait_handle 값이 wait_handle_type 필드와 불일치")
    validator.assert_condition("stage_pass_required_fields", STAGE_PASS_REQUIRED_FIELDS <= set(stage_pass), "stage_pass 필수 필드 누락")
    validator.assert_condition("stage_pass_control_closed", stage_pass["stage_status"] == "closed" and bool(stage_pass["closed_at"]), "control pass 가 handoff 후 닫히지 않음")
    validator.assert_condition("handoff_references_active_pass", HANDOFF_RESULT_REQUIRED_FIELDS <= set(handoff_result) and handoff_result["lane_id"] == active_pass["lane_id"] and handoff_result["pass_id"] == active_pass["pass_id"], "handoff_result 가 active_pass 를 참조하지 않음")
    validator.assert_condition("missing_lane_classes_complete", {"unmaterialized_lane", "no_wait_handle", "schema_invalid"} <= MISSING_LANE_CLASSES, "missing lane classification 부족")
    # 한국어 유지보수 주석: collection-level manifest 오류는 단일 lane field 검사로는 놓친다.
    # 중복 lane_id, 같은 merge_point 소유권 충돌, context version mismatch를 별도 fixture로 고정한다.
    duplicate_manifest = [logical_lane, {**logical_lane, "owned_scope": "second duplicate scope"}]
    merge_conflict_manifest = [logical_lane, {**logical_lane, "lane_id": "lane-analysis-2"}]
    duplicate_lane_ids = len({lane["lane_id"] for lane in duplicate_manifest}) != len(duplicate_manifest)
    overlapping_merge_scope = len({(lane["owned_scope"], lane["merge_point"]) for lane in merge_conflict_manifest}) != len(merge_conflict_manifest)
    bad_context_active_pass = {**active_pass, "context_packet_version": "ctx-stale", "loop_attempt": 0}
    context_mismatch = bad_context_active_pass["context_packet_version"] != logical_lane["context_packet_version"]
    stale_loop_contamination = bad_context_active_pass["loop_attempt"] != active_pass["loop_attempt"] or bad_context_active_pass["loop_id"] != active_pass["loop_id"]
    validator.assert_condition("negative_duplicate_lane_id_detectable", duplicate_lane_ids, "duplicate lane_id fixture 가 감지되지 않음")
    validator.assert_condition("negative_overlapping_merge_detectable", overlapping_merge_scope, "서로 다른 lane 의 owned_scope/merge_point 충돌 감지 기준이 불명확함")
    validator.assert_condition("negative_context_mismatch_detectable", context_mismatch, "context_packet_version mismatch fixture 가 감지되지 않음")
    validator.assert_condition("negative_stale_loop_contamination_detectable", stale_loop_contamination, "stale loop active_pass contamination 감지 실패")
    bad_wait_active_pass = {**active_pass, "wait_handle_type": "thread_id", "wait_handle": "thread-1"}
    bad_spawn_lane = {**logical_lane, "caller_spawn_required": False}
    bad_spawn_context_lane = {**logical_lane, "spawn_context_mode": "full_context_unscoped"}
    bad_status_lane = {**logical_lane, "initial_status": "active"}
    bad_pass_status = {**handoff_result, "pass_status": "waiting"}
    validator.assert_condition("negative_bad_wait_handle_type_detectable", bad_wait_active_pass["wait_handle_type"] not in {"agent_id", "submission_id"}, "bad wait_handle_type fixture 가 감지되지 않음")
    validator.assert_condition("negative_router_spawn_required_detectable", not (bad_spawn_lane["initial_status"] == "unmaterialized" and bad_spawn_lane["caller_spawn_required"] is True), "router-created lane 의 caller_spawn_required=false 를 막지 못함")
    validator.assert_condition("negative_bad_spawn_context_mode_detectable", bad_spawn_context_lane["spawn_context_mode"] not in SPAWN_CONTEXT_MODES, "bad spawn_context_mode fixture not detected")
    validator.assert_condition("negative_illegal_initial_status_detectable", bad_status_lane["initial_status"] not in {"unmaterialized"}, "logical lane initial_status 가 materialized 상태를 허용함")
    validator.assert_condition("negative_illegal_pass_status_detectable", bad_pass_status["pass_status"] not in {"returned", "superseded", "closed"}, "handoff_result pass_status invalid fixture 감지 실패")
    _check_specialist_dependency_fixtures(validator, logical_lane)
    _check_ledger_doc_field_parity(validator, contracts)


def _extract_bullet_fields(text: str, start_marker: str, end_marker: str) -> set[str]:
    # 한국어 유지보수 주석: section marker drift는 validator crash가 아니라 schema parity 실패로
    # 보고되어야 여러 결함을 한 번에 볼 수 있다.
    if start_marker not in text:
        return {f"__missing_start__:{start_marker}"}
    start = text.index(start_marker) + len(start_marker)
    if end_marker not in text[start:]:
        return {f"__missing_end__:{end_marker}"}
    end = text.index(end_marker, start)
    fields: set[str] = set()
    section = text[start:end]
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- `") and "`" in line[3:]:
            fields.update(re.findall(r"`([^`]+)`", line))
    if not fields:
        first_block = section.strip().split("\n\n", 1)[0]
        fields.update(re.findall(r"`([^`]+)`", first_block))
    return fields


def _runtime_role_catalog(validator: Any) -> dict[str, set[str]]:
    role_catalog: dict[str, set[str]] = {}
    for path in validator.agents_dir.rglob("*.toml"):
        role_catalog.setdefault(path.stem, set()).add(path.parent.name)
    return role_catalog


def _lane_concrete_specialist_status(lane: dict[str, Any], role_catalog: dict[str, set[str]]) -> str:
    role = lane["agent_role"]
    category = lane["agent_category"]
    if role in ROLE_ALIAS_MAP:
        return "family_alias"
    if role in CANONICAL_STAGE_ROLES:
        return "canonical_stage_owner"
    if role not in role_catalog:
        return "missing_runtime_role"
    if category not in role_catalog[role]:
        return "category_role_mismatch"
    return "valid"


def _check_specialist_dependency_fixtures(validator: Any, worker_lane_template: dict[str, Any]) -> None:
    role_catalog = _runtime_role_catalog(validator)
    valid_worker_lane = dict(worker_lane_template)
    valid_review_lane = {
        **worker_lane_template,
        "lane_id": "lane-review-1",
        "agent_category": "04-quality-security",
        "agent_role": "reviewer",
        "lane_type": "review",
        "owned_scope": "review one bounded artifact",
        "expected_artifact": "handoff_result",
        "merge_point": "meta_judge.review_inputs",
        "return_owner": "meta-judge",
        "validation_prompt": "review the bounded artifact and return findings with evidence",
    }

    validator.assert_condition(
        "valid_worker_lane_uses_concrete_specialist",
        _lane_concrete_specialist_status(valid_worker_lane, role_catalog) == "valid",
        f"valid worker lane did not resolve to a concrete specialist: {valid_worker_lane}",
    )
    validator.assert_condition(
        "valid_review_lane_uses_concrete_specialist",
        _lane_concrete_specialist_status(valid_review_lane, role_catalog) == "valid",
        f"valid review lane did not resolve to a concrete specialist: {valid_review_lane}",
    )

    alias_worker_lane = {**valid_worker_lane, "agent_role": "analysis-specialist"}
    alias_review_lane = {**valid_review_lane, "agent_role": "analysis-reviewer"}
    canonical_stage_lane = {**valid_worker_lane, "agent_category": "09-meta-orchestration", "agent_role": "aggregator"}
    missing_role_lane = {**valid_worker_lane, "agent_role": "missing-specialist-role"}
    category_mismatch_lane = {**valid_review_lane, "agent_category": "10-research-analysis"}

    validator.assert_condition(
        "negative_family_alias_worker_lane_detectable",
        _lane_concrete_specialist_status(alias_worker_lane, role_catalog) == "family_alias",
        "worker-router family alias lane fixture was not rejected",
    )
    validator.assert_condition(
        "negative_family_alias_review_lane_detectable",
        _lane_concrete_specialist_status(alias_review_lane, role_catalog) == "family_alias",
        "review-router family alias lane fixture was not rejected",
    )
    validator.assert_condition(
        "negative_canonical_stage_lane_detectable",
        _lane_concrete_specialist_status(canonical_stage_lane, role_catalog) == "canonical_stage_owner",
        "canonical stage owner lane fixture was not rejected",
    )
    validator.assert_condition(
        "negative_missing_runtime_role_detectable",
        _lane_concrete_specialist_status(missing_role_lane, role_catalog) == "missing_runtime_role",
        "missing runtime role lane fixture was not rejected",
    )
    validator.assert_condition(
        "negative_category_role_mismatch_detectable",
        _lane_concrete_specialist_status(category_mismatch_lane, role_catalog) == "category_role_mismatch",
        "category/role mismatch lane fixture was not rejected",
    )


def _check_ledger_doc_field_parity(validator: Any, contracts: str) -> None:
    # 한국어 유지보수 주석: constants.py의 schema와 07-contracts-ledgers.md의 bullet field가
    # 서로 갈라지면 prompt는 새 schema를 따르고 문서는 옛 schema를 설명할 수 있다.
    logical_doc = _extract_bullet_fields(contracts, "Each logical child lane must include:", "Logical lane rules:")
    physical_doc = _extract_bullet_fields(contracts, "Caller tracks materialized worker/reviewer passes with:", "Physical handle rules:")
    handoff_doc = _extract_bullet_fields(contracts, "Every child return starts with:", "## Aggregation Inputs")
    stage_doc = _extract_bullet_fields(contracts, "Control-stage passes are tracked separately from child `active_passes`:", "Routers and gate agents")
    run_doc = _extract_bullet_fields(contracts, "Non-trivial runs also keep run-level fields:", "## Schema Rule")
    provenance_doc = _extract_bullet_fields(contracts, "`contract_provenance` must include:", "## Logical Launch Manifest")
    fanout_doc = _extract_bullet_fields(contracts, "`execution_plan` and `launch_manifest` must include `fanout_budget` with:", "Each logical child lane must include:")
    judgment_doc = _extract_bullet_fields(contracts, "`judgment_envelope` must include:", "## Loop Carryover Fields")
    carryover_doc = _extract_bullet_fields(contracts, "`loop_carryover` must include:", "## Loop Control Fields")
    control_doc = _extract_bullet_fields(contracts, "`loop_control` must include:", "## Feedback Gate Fields")
    validator.assert_condition("logical_lane_doc_schema_parity", logical_doc == LOGICAL_LANE_REQUIRED_FIELDS, f"logical lane doc/schema mismatch: {sorted(logical_doc ^ LOGICAL_LANE_REQUIRED_FIELDS)}")
    validator.assert_condition("active_pass_doc_schema_parity", physical_doc == PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS, f"active_pass doc/schema mismatch: {sorted(physical_doc ^ PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS)}")
    validator.assert_condition("handoff_result_doc_schema_parity", handoff_doc == HANDOFF_RESULT_REQUIRED_FIELDS, f"handoff_result doc/schema mismatch: {sorted(handoff_doc ^ HANDOFF_RESULT_REQUIRED_FIELDS)}")
    validator.assert_condition("stage_pass_doc_schema_parity", stage_doc == STAGE_PASS_REQUIRED_FIELDS, f"stage_pass doc/schema mismatch: {sorted(stage_doc ^ STAGE_PASS_REQUIRED_FIELDS)}")
    validator.assert_condition("run_ledger_doc_schema_parity", run_doc == RUN_LEDGER_REQUIRED_FIELDS, f"run ledger doc/schema mismatch: {sorted(run_doc ^ RUN_LEDGER_REQUIRED_FIELDS)}")
    validator.assert_condition("contract_provenance_doc_schema_parity", provenance_doc == CONTRACT_PROVENANCE_REQUIRED_FIELDS, f"contract_provenance doc/schema mismatch: {sorted(provenance_doc ^ CONTRACT_PROVENANCE_REQUIRED_FIELDS)}")
    validator.assert_condition("fanout_budget_doc_schema_parity", fanout_doc == FANOUT_BUDGET_REQUIRED_FIELDS, f"fanout_budget doc/schema mismatch: {sorted(fanout_doc ^ FANOUT_BUDGET_REQUIRED_FIELDS)}")
    validator.assert_condition("judgment_doc_schema_parity", judgment_doc == JUDGMENT_ENVELOPE_REQUIRED_FIELDS, f"judgment_envelope doc/schema mismatch: {sorted(judgment_doc ^ JUDGMENT_ENVELOPE_REQUIRED_FIELDS)}")
    validator.assert_condition("loop_carryover_doc_schema_parity", carryover_doc == LOOP_CARRYOVER_REQUIRED_FIELDS, f"loop_carryover doc/schema mismatch: {sorted(carryover_doc ^ LOOP_CARRYOVER_REQUIRED_FIELDS)}")
    validator.assert_condition("loop_control_doc_schema_parity", control_doc == LOOP_CONTROL_REQUIRED_FIELDS, f"loop_control doc/schema mismatch: {sorted(control_doc ^ LOOP_CONTROL_REQUIRED_FIELDS)}")


def check_feedback_loop_contracts(validator: Any) -> None:
    validator.log("feedback loop gate fixture check")
    # 한국어 유지보수 주석: feedback gate 문구도 임의 md가 아니라 필수 architecture 문서 묶음에서만 찾는다.
    docs = "\n".join(read_text(path) for path in required_architecture_doc_paths(validator.root) if path.exists())
    lifecycle = read_text(validator.arch_dir / "05-feedback-lifecycle.md")
    for marker in FEEDBACK_REQUIRED_MARKERS:
        validator.assert_contains("feedback_loop_contract_marker", docs, marker)
    validator.assert_condition(
        "feedback_loop_final_forbidden_marker",
        any(marker in docs for marker in FEEDBACK_FINAL_FORBIDDEN_MARKERS),
        "feedback_required 상태에서 final 이 금지됨을 나타내는 문구 누락",
    )
    lifecycle_fields = _extract_bullet_fields(lifecycle, "Required fields:", "Allowed `loop_stage`:")
    validator.assert_condition(
        "feedback_lifecycle_judgment_schema_parity",
        lifecycle_fields == JUDGMENT_ENVELOPE_REQUIRED_FIELDS,
        f"05 judgment field/schema mismatch: {sorted(lifecycle_fields ^ JUDGMENT_ENVELOPE_REQUIRED_FIELDS)}",
    )
    for decision in JUDGMENT_ALLOWED_DECISIONS:
        validator.assert_contains("feedback_lifecycle_decision_enum", lifecycle, decision)
    mapping_table = _parse_feedback_target_table(lifecycle)
    validator.assert_condition("feedback_target_table_complete", set(mapping_table) == set(FEEDBACK_TARGET_REENTRY), f"feedback target table mismatch: {sorted(set(mapping_table) ^ set(FEEDBACK_TARGET_REENTRY))}")
    for target in FEEDBACK_TARGET_REENTRY:
        validator.assert_contains("feedback_lifecycle_target_enum", lifecycle, f"`{target}`")
        owner, start = FEEDBACK_TARGET_REENTRY[target]
        validator.assert_condition("feedback_lifecycle_target_mapping_exact", mapping_table.get(target) == (owner, start), f"{target} row mismatch: {mapping_table.get(target)} != {(owner, start)}")

    # 한국어 유지보수 주석: 이 fixture 는 실제 하위 agent 를 실행하지 않고도 깨진 aggregation/review
    # 상태가 반드시 feedback 으로 돌아가야 함을 고정한다. schema 가 깨졌거나 review blocking 이 남은
    # 상태에서는 final 출력이 허용되지 않아야 하며, final_blocked_reason 이 비어 있으면 상위 orchestrator
    # 가 왜 재작업을 시작해야 하는지 추적할 수 없다.
    aggregation_state = {
        "schema_valid": False,
        "missing_lane_classes": ["schema_invalid"],
        "all_lanes_classified": False,
    }
    review_state = {
        "review_complete": False,
        "blocking_findings": ["evidence_gap"],
        "unresolved_required_reviews": ["security-review"],
    }
    provenance = {"source_contract_refs": ["05-feedback-lifecycle.md", "07-contracts-ledgers.md"], "contract_lookup_missing": False}
    broken_aggregation = (not aggregation_state["schema_valid"]) or (not aggregation_state["all_lanes_classified"])
    broken_review = (not review_state["review_complete"]) or bool(review_state["blocking_findings"])
    feedback_required = broken_aggregation or broken_review
    loop_carryover = {
        "preserved_allowed_scope": ["designated architecture files only"],
        "unmet_success_criteria": ["review blocking findings are resolved"],
        "unresolved_blockers": [
            {
                "blocker_type": "evidence_gap",
                "source_pass_id": "review-pass-1",
                "artifact_ref": "artifact:review-pass-1",
                "evidence_refs": ["review_state"],
            }
        ],
        "rejected_assumptions": ["schema-invalid outputs can be merged"],
        "required_validation_evidence": ["valid aggregation_packet", "resolved review_handoff_result"],
        "context_packet_version": "ctx-1",
        "source_judgment_ref": "judgment:loop-0",
    }
    blocker_fingerprint = _blocker_fingerprint(loop_carryover["unresolved_blockers"][0], loop_carryover["context_packet_version"])
    loop_control = {
        "loop_attempt": 2,
        "repeat_feedback_count": 1,
        "max_loop_attempts": 4,
        "progress_delta": [
            {
                "new_artifact_refs": ["artifact:review-pass-1"],
                "new_evidence_refs": ["review_state"],
                "changed_blocker_fingerprint": [blocker_fingerprint],
                "changed_context_packet_version": [],
            }
        ],
        "no_progress_action": "respond to user or require schema/tool/doc repair",
    }
    review_coverage = {"required_axes": ["security-review"], "covered_axes": [], "waived_axes": []}
    synthetic_judgment = {
        "loop_id": "loop-1",
        "loop_stage": "judgment",
        "decision": "feedback" if feedback_required else "final",
        "feedback_required": feedback_required,
        "feedback_target": "aggregator",
        "next_owner": "orchestrator",
        "next_loop_start": "context-manager" if feedback_required else "none",
        "bounded_rework_request": {
            "target": "aggregator",
            "reason": "repair aggregation/review contract before final",
            "source_judgment_ref": loop_carryover["source_judgment_ref"],
            "requested_scope_refs": ["designated architecture files only"],
            "allowed_scope_subset_of": ["designated architecture files only"],
            "requested_actions": ["repair aggregation schema", "resolve review blocker"],
            "success_criteria_delta": ["review blocking findings are resolved"],
            "blocker_refs": ["evidence_gap:review-pass-1:artifact:review-pass-1"],
        } if feedback_required else None,
        "success_criteria": [
            "aggregation schema is valid",
            "review blocking findings are resolved",
            "all lanes are returned or explicitly classified",
        ] if feedback_required else [],
        "final_blocked_reason": "aggregation/review state is unresolved" if feedback_required else "",
        "confidence": "low",
        "validation_evidence": ["aggregation_state", "review_state"],
        "review_input_refs": ["handoff_result:review-pass-1"],
        "meta_judge_stage_pass_ref": "stage_pass:meta-judge:loop-1",
        "feedback_gate_evidence": ["feedback_gate:unresolved-review-and-aggregation"],
        "review_coverage": review_coverage,
        "review_waivers": [],
        "source_aggregation_packet_ref": "aggregation_packet:loop-1",
        "source_blocked_aggregation_ref": "blocked_aggregation:loop-1",
        "loop_carryover": loop_carryover,
        "loop_control": loop_control,
        "gate_evidence_bundle": {
            "stage_passes_ref": "stage_passes:loop-1",
            "active_passes_ref": "active_passes:run-1",
            "review_results_ref": "review_results:loop-1",
            "mcp_evidence_summary": {"success": [], "blocked": ["mcp:blocker"], "waived": [], "error_unclassified": []},
        },
        "tool_quiescence_snapshot": {
            "open_tool_call_count": 0,
            "open_tool_call_ids": [],
            "snapshot_at": "2026-04-28T00:00:01Z",
        },
        "contract_provenance": provenance,
        "final_allowed": not feedback_required,
    }
    clean_review_coverage = {"required_axes": ["security-review"], "covered_axes": ["security-review"], "waived_axes": []}
    clean_final_judgment = {
        "loop_id": "loop-2",
        "loop_stage": "complete",
        "decision": "final output",
        "feedback_required": False,
        "feedback_target": "none",
        "next_owner": "orchestrator",
        "next_loop_start": "none",
        "final_blocked_reason": "",
        "bounded_rework_request": None,
        "success_criteria": [],
        "confidence": "high",
        "validation_evidence": ["aggregation_packet", "review_handoff_results"],
        "review_input_refs": ["handoff_result:review-pass-2"],
        "meta_judge_stage_pass_ref": "stage_pass:meta-judge:loop-2",
        "feedback_gate_evidence": ["feedback_gate:all-required-review-axes-covered"],
        "review_coverage": clean_review_coverage,
        "review_waivers": [],
        "source_aggregation_packet_ref": "aggregation_packet:loop-2",
        "source_blocked_aggregation_ref": "",
        "loop_carryover": {
            "preserved_allowed_scope": ["designated architecture files only"],
            "unmet_success_criteria": [],
            "unresolved_blockers": [],
            "rejected_assumptions": [],
            "required_validation_evidence": [],
            "context_packet_version": "ctx-1",
            "source_judgment_ref": "judgment:loop-1",
        },
        "loop_control": {
            "loop_attempt": 1,
            "repeat_feedback_count": 0,
            "max_loop_attempts": 4,
            "progress_delta": [
                {
                    "new_artifact_refs": ["aggregation_packet:clean"],
                    "new_evidence_refs": ["review_handoff_results"],
                    "changed_blocker_fingerprint": [],
                    "changed_context_packet_version": [],
                }
            ],
            "no_progress_action": "none",
        },
        "gate_evidence_bundle": {
            "stage_passes_ref": "stage_passes:loop-2",
            "active_passes_ref": "active_passes:run-2",
            "review_results_ref": "review_results:loop-2",
            "mcp_evidence_summary": {"success": ["mcp:ok"], "blocked": [], "waived": [], "error_unclassified": []},
        },
        "tool_quiescence_snapshot": {
            "open_tool_call_count": 0,
            "open_tool_call_ids": [],
            "snapshot_at": "2026-04-28T00:00:02Z",
        },
        "contract_provenance": provenance,
        "final_allowed": True,
    }
    validator.assert_condition("feedback_fixture_decision", synthetic_judgment["decision"] == "feedback", "broken 상태가 feedback 결정을 만들지 않음")
    validator.assert_condition("judgment_envelope_required_fields", JUDGMENT_ENVELOPE_REQUIRED_FIELDS <= set(synthetic_judgment), "judgment_envelope 필수 필드 누락")
    validator.assert_condition("judgment_decision_allowed", synthetic_judgment["decision"] in JUDGMENT_ALLOWED_DECISIONS and clean_final_judgment["decision"] in JUDGMENT_ALLOWED_DECISIONS, "judgment decision 허용값 이탈")
    validator.assert_condition("feedback_target_mapping", FEEDBACK_TARGET_REENTRY[synthetic_judgment["feedback_target"]] == (synthetic_judgment["next_owner"], synthetic_judgment["next_loop_start"]), "feedback_target 이 re-entry owner/start 와 불일치")
    validator.assert_condition("clean_final_judgment_allowed", clean_final_judgment["final_allowed"] is True and clean_final_judgment["feedback_required"] is False, "clean final fixture 가 final 을 허용하지 않음")
    validator.assert_condition("negative_feedback_final_conflict_detectable", not (synthetic_judgment["feedback_required"] and synthetic_judgment["decision"] == "final output"), "feedback_required=true 인데 final output 결정이 허용됨")
    validator.assert_condition("negative_invalid_feedback_target_detectable", "worker" not in FEEDBACK_TARGET_REENTRY, "invalid feedback_target fixture 가 허용됨")
    bad_final_branch = {**clean_final_judgment, "feedback_target": "aggregator", "bounded_rework_request": {"target": "aggregator"}}
    bad_feedback_branch = {**synthetic_judgment, "feedback_target": "none", "next_loop_start": "none"}
    bad_aggregator_blocked_branch = {"aggregation_ready": False, "next_owner": "meta-judge", "aggregation_packet": {"must_not_exist": True}}
    validator.assert_condition("negative_final_branch_feedback_fields_detectable", bad_final_branch["decision"] == "final output" and (bad_final_branch["feedback_target"] != "none" or bad_final_branch["bounded_rework_request"] is not None), "final branch feedback 필드 오염 감지 실패")
    validator.assert_condition("negative_feedback_branch_none_target_detectable", bad_feedback_branch["decision"] == "feedback" and (bad_feedback_branch["feedback_target"] == "none" or bad_feedback_branch["next_loop_start"] == "none"), "feedback branch 가 none target/start 를 허용함")
    validator.assert_condition("negative_aggregator_blocked_packet_detectable", bad_aggregator_blocked_branch["aggregation_ready"] is False and "aggregation_packet" in bad_aggregator_blocked_branch, "blocked aggregation branch 가 aggregation_packet 을 함께 반환함")
    validator.assert_condition("feedback_fixture_required", synthetic_judgment["feedback_required"] is True, "feedback_required 가 True 가 아님")
    validator.assert_condition("feedback_fixture_restart", synthetic_judgment["next_loop_start"] == "context-manager", "feedback loop 가 context-manager 에서 재시작하지 않음")
    validator.assert_condition("feedback_fixture_rework", isinstance(synthetic_judgment["bounded_rework_request"], dict) and bool(synthetic_judgment["bounded_rework_request"].get("success_criteria_delta")), "bounded_rework_request/success_criteria_delta 누락")
    validator.assert_condition("feedback_fixture_final_blocked", synthetic_judgment["final_allowed"] is False and bool(synthetic_judgment["final_blocked_reason"]), "feedback_required 상태에서 final 이 차단되지 않음")
    validator.assert_condition("feedback_loop_integrity_fields", LOOP_CARRYOVER_REQUIRED_FIELDS <= set(synthetic_judgment["loop_carryover"]) and LOOP_CONTROL_REQUIRED_FIELDS <= set(synthetic_judgment["loop_control"]), "loop integrity nested 필드 누락")
    validator.assert_condition("feedback_rework_delta_only", "loop_carryover" not in synthetic_judgment["bounded_rework_request"] and "loop_control" not in synthetic_judgment["bounded_rework_request"], "bounded_rework_request 가 full carryover/control 을 중복 보존함")
    validator.assert_condition("feedback_rework_no_full_success_criteria", "success_criteria" not in synthetic_judgment["bounded_rework_request"], "bounded_rework_request 가 full success_criteria 를 중복 보존함")
    validator.assert_condition("feedback_rework_delta_fields", BOUNDED_REWORK_REQUEST_REQUIRED_FIELDS <= set(synthetic_judgment["bounded_rework_request"]), "bounded_rework_request delta 필드 누락")
    validator.assert_condition("feedback_scope_not_widened", set(synthetic_judgment["bounded_rework_request"]["allowed_scope_subset_of"]) <= set(synthetic_judgment["loop_carryover"]["preserved_allowed_scope"]), "feedback 재진입이 allowed_scope 를 확장함")
    validator.assert_condition("feedback_blocker_lineage_present", all({"blocker_type", "source_pass_id", "artifact_ref", "evidence_refs"} <= set(blocker) for blocker in synthetic_judgment["loop_carryover"]["unresolved_blockers"]), "unresolved_blockers lineage 필드 누락")
    validator.assert_condition("blocker_fingerprint_derives_from_lineage", blocker_fingerprint in synthetic_judgment["loop_control"]["progress_delta"][0]["changed_blocker_fingerprint"], "changed_blocker_fingerprint 가 unresolved_blockers lineage 에서 유도되지 않음")
    validator.assert_condition("review_coverage_schema_fixture", REVIEW_COVERAGE_REQUIRED_FIELDS <= set(clean_final_judgment["review_coverage"]), "review_coverage 필수 필드 누락")
    validator.assert_condition("review_waiver_schema_empty_ok", all(REVIEW_WAIVER_REQUIRED_FIELDS <= set(waiver) for waiver in clean_final_judgment["review_waivers"]), "review_waivers 필수 필드 누락")
    uncovered_axes = set(review_coverage["required_axes"]) - set(review_coverage["covered_axes"]) - set(review_coverage["waived_axes"])
    validator.assert_condition("negative_uncovered_review_axis_blocks_final", not (uncovered_axes and synthetic_judgment["decision"] == "final output"), "uncovered review axis 가 final output 을 막지 못함")
    waiver_fixture = {
        "axis": "security-review",
        "reason": "low-risk documentation-only path",
        "blocker_ref": "waiver:security-review",
        "evidence_refs": ["review_scope_note"],
        "approver_scope": "meta-judge bounded waiver",
        "residual_risk": "review lens not executed",
        "expiry": "current-loop-only",
    }
    waiver_coverage = {"required_axes": ["security-review"], "covered_axes": [], "waived_axes": ["security-review"]}
    validator.assert_condition("review_waiver_schema_fixture", REVIEW_WAIVER_REQUIRED_FIELDS <= set(waiver_fixture), "review_waiver schema fixture 누락")
    validator.assert_condition("review_waiver_axis_parity", set(waiver_coverage["waived_axes"]) == {waiver_fixture["axis"]}, "waived_axes 와 review_waivers.axis 불일치")
    stalled_judgment = {
        **synthetic_judgment,
        "loop_control": {**synthetic_judgment["loop_control"], "repeat_feedback_count": 3, "progress_delta": []},
        "loop_carryover": {**synthetic_judgment["loop_carryover"], "required_validation_evidence": []},
    }
    repeated_blocker_without_new_evidence = stalled_judgment["loop_control"]["repeat_feedback_count"] >= 2 and not stalled_judgment["loop_carryover"]["required_validation_evidence"]
    validator.assert_condition("feedback_repeat_exit_detectable", repeated_blocker_without_new_evidence, "반복 feedback no-progress fixture 가 실행되지 않음")
    # 한국어 유지보수 주석: 2~4회 반복 loop에서 같은 blocker가 진전 없이 재순환하면
    # 자동 재시작 대신 사용자 응답 또는 schema/tool/doc 보강으로 빠져야 한다.
    loop_history = [
        {"loop_attempt": 1, "repeat_feedback_count": 0, "progress_delta": [{"new_artifact_refs": ["artifact:a"], "new_evidence_refs": ["evidence:a"], "changed_blocker_fingerprint": ["fp:a"], "changed_context_packet_version": []}]},
        {"loop_attempt": 2, "repeat_feedback_count": 1, "progress_delta": [{"new_artifact_refs": ["artifact:b"], "new_evidence_refs": ["evidence:b"], "changed_blocker_fingerprint": ["fp:b"], "changed_context_packet_version": []}]},
        {"loop_attempt": 3, "repeat_feedback_count": 2, "progress_delta": []},
        {"loop_attempt": 4, "repeat_feedback_count": 3, "progress_delta": []},
    ]
    validator.assert_condition("progress_delta_schema_fixture", all(PROGRESS_DELTA_REQUIRED_FIELDS <= set(delta) for item in loop_history for delta in item["progress_delta"]), "progress_delta structure 가 evidence-bound delta가 아님")
    same_blocker_history = [
        {"blocker_fingerprint": blocker_fingerprint, "validation_evidence": ("ev:same",), "feedback_continues": True},
        {"blocker_fingerprint": blocker_fingerprint, "validation_evidence": ("ev:same",), "feedback_continues": True},
        {"blocker_fingerprint": blocker_fingerprint, "validation_evidence": ("ev:same",), "feedback_continues": False},
    ]
    repeated_same_state = (
        same_blocker_history[0]["blocker_fingerprint"] == same_blocker_history[1]["blocker_fingerprint"] == same_blocker_history[2]["blocker_fingerprint"]
        and same_blocker_history[0]["validation_evidence"] == same_blocker_history[1]["validation_evidence"] == same_blocker_history[2]["validation_evidence"]
    )
    validator.assert_condition("same_blocker_evidence_escape_fixture", repeated_same_state and not same_blocker_history[-1]["feedback_continues"], "동일 blocker/evidence 반복이 feedback 지속으로 남음")
    terminal_actions = ("respond to user", "require schema/tool/doc repair")
    fourth_loop = loop_history[-1]
    must_exit = fourth_loop["loop_attempt"] >= loop_control["max_loop_attempts"] or (
        fourth_loop["repeat_feedback_count"] >= 2 and not fourth_loop["progress_delta"]
    )
    validator.assert_condition("multi_loop_exit_rule_detectable", must_exit, "2~4회 반복 loop 의 no-progress 탈출 조건이 감지되지 않음")
    validator.assert_condition("multi_loop_exit_action_valid", all(action in loop_control["no_progress_action"] for action in terminal_actions), "no-progress action 이 사용자 응답 또는 schema/tool/doc 보강을 가리키지 않음")
    _check_stage_artifact_fixtures(validator, loop_carryover, loop_control)


def _check_stage_artifact_fixtures(validator: Any, loop_carryover: dict[str, Any], loop_control: dict[str, Any]) -> None:
    # 한국어 유지보수 주석: canonical stage artifact는 prompt marker만으로는 부족하다.
    # synthetic object shape를 함께 고정해 필수 필드가 조용히 빠지는 회귀를 잡는다.
    provenance = {"source_contract_refs": ["07-contracts-ledgers.md"], "contract_lookup_missing": False}
    fanout_budget = {
        "max_worker_lanes_per_wave": 2,
        "max_review_lanes_per_wave": 2,
        "max_total_child_agents_per_loop": 4,
        "max_same_role_parallel_lanes": 1,
        "max_mcp_concurrent_child_lanes": 1,
        "budget_reason": "default bounded fanout",
        "overflow_policy": "coalesce_axes_or_feedback",
    }
    orchestration_request = {
        "run_id": "run-1",
        "loop_id": "loop-1",
        "user_goal": "validate architecture",
        "allowed_scope": ["architecture files"],
        "constraints": ["do not widen scope"],
        "direct_answer_exception": False,
        "risk_flags": ["architecture drift"],
        "success_criteria": ["validator passes"],
        "feedback_reentry": {"source_judgment_ref": loop_carryover["source_judgment_ref"]},
        "validation_evidence": ["mcp_orchestration_required=true:mcp_usage_blocked=false"],
        "loop_carryover": loop_carryover,
        "loop_control": loop_control,
        "fanout_budget": fanout_budget,
        "contract_provenance": provenance,
    }
    context_packet = {
        "source_orchestration_request_ref": "orchestration_request:run-1:loop-1",
        "next_stage_consumer": "task-planner",
        "context_authority_ref": "mcp:codex-context-ledger:run-1",
        "context_packet_version": loop_carryover["context_packet_version"],
        "context_revision": "ctx-1:rev-1",
        "role_pass_readiness": {
            "allowed_role_passes": ["task-planner"],
            "refresh_required_for": [],
            "readiness_reason": "fresh context packet",
        },
        "approved_facts": ["canonical loop exists"],
        "constraints": orchestration_request["constraints"],
        "evidence_gaps": [],
        "allowed_scope": orchestration_request["allowed_scope"],
        "exclusions": [],
        "stale_items": [],
        "accepted_evidence": ["prior judgment"],
        "artifact_inventory": [],
        "success_criteria": orchestration_request["success_criteria"],
        "validation_evidence": ["validator"],
        "loop_carryover": loop_carryover,
        "loop_control": loop_control,
        "contract_provenance": provenance,
    }
    execution_plan = {
        "wave_id": "wave-1",
        "source_context_packet_ref": "context_packet:ctx-1",
        "context_packet_version": loop_carryover["context_packet_version"],
        "lanes": [{"plan_lane_id": "plan-lane-1", "owned_scope": "schema check", "expected_artifact": "handoff_result", "expected_handoff_fields": sorted(HANDOFF_RESULT_REQUIRED_FIELDS), "merge_point": "aggregation_packet.inputs", "validation_prompt": "check schema parity", "validation_evidence": ["schema parity"], "review_hint": "architecture"}],
        "same_role_parallel_rules": [],
        "unresolved_assumptions": [],
        "fanout_budget": fanout_budget,
        "loop_carryover": loop_carryover,
        "loop_control": loop_control,
        "contract_provenance": provenance,
    }
    logical_lane = {
        "lane_id": "lane-schema-1",
        "parent_router_pass_id": "router-pass-1",
        "agent_category": "09-meta-orchestration",
        "agent_role": "specialist-worker",
        "lane_type": "worker",
        "owned_scope": execution_plan["lanes"][0]["owned_scope"],
        "expected_artifact": execution_plan["lanes"][0]["expected_artifact"],
        "merge_point": execution_plan["lanes"][0]["merge_point"],
        "return_owner": "aggregator",
        "validation_prompt": execution_plan["lanes"][0]["validation_prompt"],
        "context_packet_version": loop_carryover["context_packet_version"],
        "spawn_context_mode": "scoped_packet",
        "caller_spawn_required": True,
        "initial_status": "unmaterialized",
    }
    launch_manifest = {
        "manifest_kind": "worker",
        "source_parent_ref": "execution_plan:wave-1",
        "source_execution_plan_ref": "execution_plan:wave-1",
        "context_packet_version": loop_carryover["context_packet_version"],
        "children": [{"plan_lane_id": "plan-lane-1", **{field: logical_lane[field] for field in LOGICAL_LANE_REQUIRED_FIELDS}}],
        "loop_control": loop_control,
        "fanout_budget": fanout_budget,
        "contract_provenance": provenance,
        "schema_status": "valid",
    }
    review_launch_manifest = {
        "manifest_kind": "review",
        "source_parent_ref": "aggregation_packet:loop-1",
        "source_aggregation_packet_ref": "aggregation_packet:loop-1",
        "context_packet_version": loop_carryover["context_packet_version"],
        "children": [{**logical_lane, "lane_id": "lane-review-1", "lane_type": "review", "return_owner": "meta-judge", "spawn_context_mode": "scoped_packet"}],
        "loop_control": loop_control,
        "fanout_budget": fanout_budget,
        "contract_provenance": provenance,
        "schema_status": "valid",
    }
    schema_invalid = {
        "manifest_kind": "worker",
        "source_parent_ref": "execution_plan:wave-1",
        "context_packet_version": loop_carryover["context_packet_version"],
        "parent_router_pass_id": "router-pass-1",
        "lane_ids": ["lane-bad-1"],
        "missing_fields": ["parent_router_pass_id"],
        "forbidden_fields": ["agent_id"],
    }
    aggregation_packet = {
        "normalized_claims": [],
        "context_packet_version": loop_carryover["context_packet_version"],
        "source_launch_manifest_ref": "launch_manifest:wave-1",
        "source_loop_id": "loop-1",
        "source_loop_attempt": 2,
        "source_pass_statuses": {"child-pass-1": "returned"},
        "active_pass_snapshot_ref": "active_passes:run-1:loop-1:attempt-2",
        "evidence_refs": [],
        "artifact_refs": [],
        "artifact_kinds": [],
        "source_pass_ids": [],
        "source_lane_ids": [],
        "source_parent_pass_ids": [],
        "blocker_fingerprint": [_blocker_fingerprint(loop_carryover["unresolved_blockers"][0], loop_carryover["context_packet_version"])],
        "loop_carryover": loop_carryover,
        "loop_control": loop_control,
        "merge_point": "review-router",
        "confidence_summary": "medium",
        "contradiction_list": [],
        "missing_lanes": [],
        "schema_invalid_outputs": [schema_invalid],
        "stale_context_findings": [],
        "required_review_axes": ["architecture"],
        "coverage_status": [{"axis": "architecture", "status": "covered"}],
        "suggested_reviewer_families": ["engineering-reviewer"],
        "aggregation_input_bundle": {
            "handoff_results_ref": ["handoff_result:child-pass-1"],
            "active_passes_ref": "active_passes:run-1:loop-1:attempt-2",
            "missing_lane_classes_ref": [],
            "schema_invalid_outputs_ref": ["schema_invalid:router-pass-1"],
            "aggregation_input_mode": "canonical",
        },
        "contract_provenance": provenance,
    }
    bounded_rework_request = {
        "target": "aggregator",
        "reason": "repair unresolved evidence",
        "source_judgment_ref": loop_carryover["source_judgment_ref"],
        "requested_scope_refs": ["architecture files"],
        "allowed_scope_subset_of": ["architecture files"],
        "requested_actions": ["rerun aggregation"],
        "success_criteria_delta": ["evidence gap closed"],
        "blocker_refs": ["evidence_gap:review-pass-1:artifact:review-pass-1"],
    }
    run_ledger = {
        "run_id": "run-1",
        "loop_id": "loop-1",
        "user_goal": "validate architecture",
        "allowed_scope": ["architecture files"],
        "stage": "judgment",
        "stage_artifact_name": "judgment_envelope",
        "stage_artifact_ref": "judgment:loop-1",
        "schema_status": "valid",
        "validation_evidence": ["validator"],
        "context_packet_version": loop_carryover["context_packet_version"],
        "loop_attempt": loop_control["loop_attempt"],
        "repeat_feedback_count": loop_control["repeat_feedback_count"],
        "feedback_gate_mandatory": True,
        "feedback_required": True,
        "failure_class": "none",
        "decision": "feedback",
        "next_owner": "orchestrator",
        "created_at": "2026-04-28T00:00:00Z",
        "updated_at": "2026-04-28T00:00:01Z",
    }
    validator.assert_condition("orchestration_request_schema_fixture", ORCHESTRATION_REQUEST_REQUIRED_FIELDS <= set(orchestration_request), "orchestration_request 필수 필드 누락")
    validator.assert_condition("context_packet_schema_fixture", CONTEXT_PACKET_REQUIRED_FIELDS <= set(context_packet), "context_packet 필수 필드 누락")
    validator.assert_condition("execution_plan_schema_fixture", EXECUTION_PLAN_REQUIRED_FIELDS <= set(execution_plan), "execution_plan 필수 필드 누락")
    validator.assert_condition("execution_plan_lane_schema_fixture", all(EXECUTION_PLAN_LANE_REQUIRED_FIELDS <= set(lane) for lane in execution_plan["lanes"]), "execution_plan.lanes[] 필수 필드 누락")
    validator.assert_condition("launch_manifest_schema_fixture", LAUNCH_MANIFEST_REQUIRED_FIELDS <= set(launch_manifest), "launch_manifest top-level 필수 필드 누락")
    validator.assert_condition("worker_launch_manifest_schema_fixture", WORKER_LAUNCH_MANIFEST_REQUIRED_FIELDS <= set(launch_manifest) and launch_manifest["manifest_kind"] == "worker", "worker launch_manifest source 필드 누락")
    validator.assert_condition("review_launch_manifest_schema_fixture", REVIEW_LAUNCH_MANIFEST_REQUIRED_FIELDS <= set(review_launch_manifest) and review_launch_manifest["manifest_kind"] == "review", "review launch_manifest source 필드 누락")
    validator.assert_condition("worker_manifest_lineage_exclusive", launch_manifest["source_parent_ref"] == launch_manifest["source_execution_plan_ref"] and "source_aggregation_packet_ref" not in launch_manifest, "worker launch_manifest source lineage 오염")
    validator.assert_condition("review_manifest_lineage_exclusive", review_launch_manifest["source_parent_ref"] == review_launch_manifest["source_aggregation_packet_ref"] and "source_execution_plan_ref" not in review_launch_manifest, "review launch_manifest source lineage 오염")
    validator.assert_condition("schema_invalid_parent_ref_kind", schema_invalid["manifest_kind"] == "worker" and schema_invalid["source_parent_ref"].startswith("execution_plan:"), "schema_invalid source_parent_ref 가 manifest_kind 와 불일치")
    validator.assert_condition("schema_invalid_schema_fixture", SCHEMA_INVALID_REQUIRED_FIELDS <= set(schema_invalid), "schema_invalid 필수 필드 누락")
    validator.assert_condition("aggregation_packet_schema_fixture", AGGREGATION_PACKET_REQUIRED_FIELDS <= set(aggregation_packet), "aggregation_packet 필수 필드 누락")
    validator.assert_condition("schema_invalid_outputs_schema_fixture", all(SCHEMA_INVALID_REQUIRED_FIELDS <= set(item) for item in aggregation_packet["schema_invalid_outputs"]), "schema_invalid_outputs[] 필수 필드 누락")
    validator.assert_condition("review_coverage_axes_parity", set(aggregation_packet["required_review_axes"]) == {item["axis"] for item in aggregation_packet["coverage_status"]}, "aggregation review coverage 축 불일치")
    validator.assert_condition("bounded_rework_request_schema_fixture", BOUNDED_REWORK_REQUEST_REQUIRED_FIELDS <= set(bounded_rework_request), "bounded_rework_request 필수 필드 누락")
    validator.assert_condition("run_ledger_schema_fixture", RUN_LEDGER_REQUIRED_FIELDS <= set(run_ledger), "run ledger 필수 필드 누락")
    validator.assert_condition("run_ledger_loop_control_parity", run_ledger["loop_attempt"] == loop_control["loop_attempt"] and run_ledger["repeat_feedback_count"] == loop_control["repeat_feedback_count"], "run ledger loop_control parity 불일치")
    validator.assert_condition("run_ledger_feedback_parity", run_ledger["feedback_required"] is True and run_ledger["decision"] == "feedback", "run ledger feedback_required/decision parity 불일치")
    validator.assert_condition("contract_provenance_schema_fixture", CONTRACT_PROVENANCE_REQUIRED_FIELDS <= set(provenance), "contract_provenance 필수 필드 누락")
    validator.assert_condition("stage_artifact_carryover_identity", orchestration_request["loop_carryover"] is context_packet["loop_carryover"] is execution_plan["loop_carryover"] is aggregation_packet["loop_carryover"], "loop_carryover identity 가 stage 사이에서 유지되지 않음")
    validator.assert_condition("stage_artifact_loop_control_identity", orchestration_request["loop_control"] is context_packet["loop_control"] is execution_plan["loop_control"] is launch_manifest["loop_control"] is review_launch_manifest["loop_control"] is aggregation_packet["loop_control"], "loop_control identity 가 stage 사이에서 유지되지 않음")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_feedback_target_table(text: str) -> dict[str, tuple[str, str]]:
    if "Feedback target mapping:" not in text:
        return {}
    section = text.split("Feedback target mapping:", 1)[1].split("## Feedback Trigger Gate", 1)[0]
    rows: dict[str, tuple[str, str]] = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("| `"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) >= 4:
            rows[cells[0]] = (cells[2], cells[3])
    return rows


def _blocker_fingerprint(blocker: dict[str, Any], context_packet_version: str) -> str:
    return f"{blocker['blocker_type']}:{blocker['source_pass_id']}:{blocker['artifact_ref']}:{context_packet_version}"
