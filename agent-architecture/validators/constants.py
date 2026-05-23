"""Shared schema and prompt constants for architecture validation."""

from __future__ import annotations

from pathlib import Path

# 한국어 주석: canonical loop는 docs.py와 문서 파일이 같은 문자열을 보도록 중앙에서 관리한다.
CANONICAL_LOOP = (
    "Orchestrator <-> Context Manager -> Task Planner -> Worker Router -> "
    "Specialist Worker Layer -> Aggregator -> Review Router -> Specialist Review Layer -> "
    "Meta Judge -> Feedback Trigger Gate -> Feedback to Orchestrator then Context Manager restart or Final Output"
)

DETAIL_DOC_NAMES = (
    "00-canonical-map.md",
    "01-harness-layer.md",
    "02-context-planning.md",
    "03-worker-routing.md",
    "04-aggregation-review.md",
    "05-feedback-lifecycle.md",
    "06-agent-roster-models.md",
    "07-contracts-ledgers.md",
    "08-quality-evals.md",
    "09-runtime-orchestration-steps.md",
)

POINTER_DOC_NAMES = (
    "AGENT-ARCHITECTURE.md",
    "AGENT-ARCHITECTURE-MAPPER.md",
    "AGENTS.local-template.md",
)

APPROVED_ARCHITECTURE_MD_NAMES = set(POINTER_DOC_NAMES) | set(DETAIL_DOC_NAMES)


def required_architecture_doc_paths(root: Path) -> list[Path]:
    """Return only schema/contract-approved architecture documents."""
    # 한국어 주석: validator는 임의 md를 훑지 않고, architecture schema가 요구하는 필수 문서만 읽는다.
    arch_dir = root / "agent-architecture"
    return [root / "AGENTS.md"] + [arch_dir / name for name in POINTER_DOC_NAMES] + [arch_dir / name for name in DETAIL_DOC_NAMES]

ARCHITECTURE_REQUIRED_TEXT = (
    "${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md",
    "${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md",
    "${CODEX_HOME}/agent-architecture/AGENTS.local-template.md",
    "${CODEX_HOME}/agent-architecture/apply-agents-inheritance.py",
    "${CODEX_HOME}/agent-architecture/08-quality-evals.md",
    "Obsidian",
    "personal record",
    "orchestration_request",
    "launch_manifest",
    "handoff_result",
    "aggregation_packet",
    "judgment_envelope",
    "contract_provenance",
    "active_passes",
    "architecture_validation_required=true",
    "architecture_required=true",
    "agent_fanout_budget_required=true",
    "fanout_budget",
    "stage_execution_mode=main_agent_role_pass",
    "physical_control_override_required=true",
    "context_ledger_mcp_required=true",
    "context_manager_authority_required=true",
    "orchestration_stage_skills_required=true",
    "$orchestrator",
    "$task-planner",
    "$worker-router",
    "$task-distributor",
    "$result-aggregator",
    "$review-router",
    "$feedback-synthesizer",
    "context_revision",
    "role_pass_readiness",
    "validate-agent-architecture.py",
    "validate-skill-contracts.py",
    "validate-runtime-artifact.py",
    "validate-session-runtime.py",
    "harness_gate.py",
    "harness_handoff.py",
    "validate-runtime-gate-smoke.py",
    "runtime_validation_required",
    "allow_next_stage",
    "route_kind",
    "expected_next_owner",
    "expected_source_ref",
    "expected_context_packet_version",
    "architecture_physical_execution_blocked=true",
)

DETAIL_CONTRACTS = (
    ("01-harness-layer.md", "Mandatory Physical Pass Rule"),
    ("01-harness-layer.md", "Enforcement Trigger"),
    ("01-harness-layer.md", "architecture_required=true"),
    ("01-harness-layer.md", "architecture_physical_execution_blocked=true"),
    ("01-harness-layer.md", "Orchestrator MCP Gate"),
    ("01-harness-layer.md", "mcp_orchestration_required=true"),
    ("01-harness-layer.md", "MCP_DOCKER/sequentialthinking:success"),
    ("01-harness-layer.md", "Fanout Budget Gate"),
    ("01-harness-layer.md", "agent_fanout_budget_required=true"),
    ("01-harness-layer.md", "stage_execution_mode=main_agent_role_pass"),
    ("01-harness-layer.md", "physical_control_override_required=true"),
    ("01-harness-layer.md", "context_ledger_mcp_required=true"),
    ("01-harness-layer.md", "context_manager_authority_required=true"),
    ("01-harness-layer.md", "orchestration_stage_skills_required=true"),
    ("01-harness-layer.md", "$orchestrator"),
    ("01-harness-layer.md", "$task-planner"),
    ("01-harness-layer.md", "$task-distributor"),
    ("01-harness-layer.md", "$result-aggregator"),
    ("01-harness-layer.md", "$feedback-synthesizer"),
    ("01-harness-layer.md", "Failure Classes"),
    ("01-harness-layer.md", "schema_invalid"),
    ("01-harness-layer.md", "Spawn And Wait Evidence Rule"),
    ("01-harness-layer.md", "fork_context=true"),
    ("01-harness-layer.md", "`close_agent` is cleanup only"),
    ("00-canonical-map.md", "MCP-critical stages"),
    ("00-canonical-map.md", "docker_mcp_sequentialthinking_required=true"),
    ("00-canonical-map.md", "MCP_DOCKER/sequentialthinking:success"),
    ("00-canonical-map.md", "MCP Broker Rule"),
    ("00-canonical-map.md", "per_agent_mcp_lifecycle_required=true"),
    ("00-canonical-map.md", "mcp_process_shutdown_required=true"),
    ("00-canonical-map.md", "mcp_process_residue_forbidden=true"),
    ("00-canonical-map.md", "Control Stage Execution Policy"),
    ("00-canonical-map.md", "stage_execution_mode=main_agent_role_pass"),
    ("00-canonical-map.md", "physical_control_override_required=true"),
    ("00-canonical-map.md", "context_ledger_mcp_required=true"),
    ("00-canonical-map.md", "context_manager_authority_required=true"),
    ("00-canonical-map.md", "orchestration_stage_skills_required=true"),
    ("00-canonical-map.md", "Fanout Budget Policy"),
    ("00-canonical-map.md", "agent_fanout_budget_required=true"),
    ("02-context-planning.md", "needs_context_manager"),
    ("02-context-planning.md", "execution_plan"),
    ("02-context-planning.md", "MCP Evidence Boundary"),
    ("02-context-planning.md", "per_agent_mcp_lifecycle_required=true"),
    ("02-context-planning.md", "mcp_process_shutdown_required=true"),
    ("02-context-planning.md", "Context Manager MCP Gate"),
    ("02-context-planning.md", "mcp_context_sync_required=true"),
    ("02-context-planning.md", "docker_mcp_sequentialthinking_required=true"),
    ("02-context-planning.md", "MCP_DOCKER/sequentialthinking:success"),
    ("02-context-planning.md", "context_ledger_mcp_required=true"),
    ("02-context-planning.md", "MCP Context Authority"),
    ("02-context-planning.md", "context_manager_authority_required=true"),
    ("02-context-planning.md", "context_revision"),
    ("02-context-planning.md", "role_pass_readiness"),
    ("09-runtime-orchestration-steps.md", "$orchestrator"),
    ("09-runtime-orchestration-steps.md", "$task-planner"),
    ("09-runtime-orchestration-steps.md", "$worker-router"),
    ("09-runtime-orchestration-steps.md", "$task-distributor"),
    ("09-runtime-orchestration-steps.md", "$result-aggregator"),
    ("09-runtime-orchestration-steps.md", "$review-router"),
    ("09-runtime-orchestration-steps.md", "$feedback-synthesizer"),
    ("09-runtime-orchestration-steps.md", "$docker-memory"),
    ("09-runtime-orchestration-steps.md", "validate-skill-contracts.py"),
    ("02-context-planning.md", "stage_execution_mode=main_agent_role_pass"),
    ("02-context-planning.md", "agent_fanout_budget_required=true"),
    ("02-context-planning.md", "fanout_budget"),
    ("03-worker-routing.md", "Single Router Rule"),
    ("03-worker-routing.md", "Caller Materialization"),
    ("03-worker-routing.md", "materialization_pending"),
    ("03-worker-routing.md", "Specialist Worker Layer"),
    ("03-worker-routing.md", "Specialist Coverage Contract"),
    ("03-worker-routing.md", "Skill names are not spawnable"),
    ("03-worker-routing.md", "Fanout Budget"),
    ("03-worker-routing.md", "agent_fanout_budget_required=true"),
    ("03-worker-routing.md", "stage_execution_mode=main_agent_role_pass"),
    ("03-worker-routing.md", "MCP Tool Request Boundary"),
    ("03-worker-routing.md", "mcp_quiescence_snapshot"),
    ("03-worker-routing.md", "open_mcp_process_count=0"),
    ("03-worker-routing.md", "cleanup_status=clean"),
    ("04-aggregation-review.md", "schema_invalid"),
    ("04-aggregation-review.md", "Specialist Review Layer"),
    ("04-aggregation-review.md", "context_packet_version"),
    ("04-aggregation-review.md", "MCP Evidence Handling"),
    ("04-aggregation-review.md", "Aggregator MCP Gate"),
    ("04-aggregation-review.md", "mcp_aggregation_required=true"),
    ("04-aggregation-review.md", "docker_mcp_sequentialthinking_required=true"),
    ("04-aggregation-review.md", "MCP_DOCKER/sequentialthinking:success"),
    ("04-aggregation-review.md", "Review Fanout Budget"),
    ("04-aggregation-review.md", "agent_fanout_budget_required=true"),
    ("04-aggregation-review.md", "stage_execution_mode=main_agent_role_pass"),
    ("04-aggregation-review.md", "MCP Review Request Boundary"),
    ("04-aggregation-review.md", "mcp_quiescence_snapshot"),
    ("04-aggregation-review.md", "open_mcp_process_count=0"),
    ("04-aggregation-review.md", "Aggregation Evidence Contract"),
    ("04-aggregation-review.md", "Review Coverage Contract"),
    ("05-feedback-lifecycle.md", "Feedback always returns to `orchestrator`"),
    ("05-feedback-lifecycle.md", "MCP-required evidence"),
    ("05-feedback-lifecycle.md", "docker_mcp_sequentialthinking_required=true"),
    ("05-feedback-lifecycle.md", "MCP_DOCKER/sequentialthinking:success"),
    ("05-feedback-lifecycle.md", "per_agent_mcp_lifecycle_required=true"),
    ("05-feedback-lifecycle.md", "mcp_process_shutdown_required=true"),
    ("05-feedback-lifecycle.md", "mcp_quiescence_snapshot"),
    ("05-feedback-lifecycle.md", "physical evidence bundle"),
    ("05-feedback-lifecycle.md", "preserved_allowed_scope"),
    ("06-agent-roster-models.md", "gpt-5.5"),
    ("06-agent-roster-models.md", "Canonical Stage Runtime Map"),
    ("06-agent-roster-models.md", "Skills are instructions, not agent types"),
    ("07-contracts-ledgers.md", "Logical Launch Manifest"),
    ("07-contracts-ledgers.md", "Physical Active Passes Ledger"),
    ("07-contracts-ledgers.md", "spawn_receipt_ref"),
    ("07-contracts-ledgers.md", "Completion Evidence Resolution"),
    ("07-contracts-ledgers.md", "Stage Passes Ledger"),
    ("07-contracts-ledgers.md", "Resident Context Fields"),
    ("07-contracts-ledgers.md", "context_revision"),
    ("07-contracts-ledgers.md", "role_pass_readiness"),
    ("07-contracts-ledgers.md", "Judgment Envelope Fields"),
    ("07-contracts-ledgers.md", "unresolved_blockers"),
    ("07-contracts-ledgers.md", "agent_id"),
    ("07-contracts-ledgers.md", "submission_id"),
    ("07-contracts-ledgers.md", "artifact_ref"),
    ("07-contracts-ledgers.md", "Runtime handoff rule"),
    ("07-contracts-ledgers.md", "Runtime spawn API constraint"),
    ("07-contracts-ledgers.md", "`close_agent` status may be recorded separately"),
    ("07-contracts-ledgers.md", "pass_closure_proof"),
    ("07-contracts-ledgers.md", "stage_spawn_contract"),
    ("07-contracts-ledgers.md", "spawn_packet_mode=main_agent_role_pass"),
    ("07-contracts-ledgers.md", "agent_fanout_budget_required=true"),
    ("07-contracts-ledgers.md", "fanout_budget"),
    ("07-contracts-ledgers.md", "aggregation_input_bundle"),
    ("07-contracts-ledgers.md", "tool_quiescence_snapshot"),
    ("07-contracts-ledgers.md", "MCP Lifecycle Contract"),
    ("07-contracts-ledgers.md", "per_agent_mcp_lifecycle_required=true"),
    ("07-contracts-ledgers.md", "mcp_process_shutdown_required=true"),
    ("07-contracts-ledgers.md", "mcp_process_residue_forbidden=true"),
    ("07-contracts-ledgers.md", "mcp_quiescence_snapshot"),
    ("07-contracts-ledgers.md", "gate_evidence_bundle"),
    ("08-quality-evals.md", "validate-agent-architecture.py"),
    ("08-quality-evals.md", "validate-skill-contracts.py"),
    ("08-quality-evals.md", "architecture_required=true"),
    ("08-quality-evals.md", "validate-runtime-artifact.py"),
    ("08-quality-evals.md", "validate-session-runtime.py"),
    ("08-quality-evals.md", "simulated stage chain"),
    ("08-quality-evals.md", "harness_gate.py"),
    ("08-quality-evals.md", "harness_handoff.py"),
    ("08-quality-evals.md", "validate-runtime-gate-smoke.py"),
    ("08-quality-evals.md", "physical_spawn_witness"),
    ("08-quality-evals.md", "closed-only child evidence"),
    ("08-quality-evals.md", "generic `worker` direct spawns"),
    ("08-quality-evals.md", "MCP calls with error-shaped results"),
)

STAGE_CHAIN_DOC_CONTRACTS = (
    ("orchestrator_to_context", "01-harness-layer.md", ("Orchestrator -> Context Manager", "orchestration_request")),
    ("context_to_planner", "01-harness-layer.md", ("Context Manager -> Task Planner", "context_packet")),
    ("planner_to_router", "02-context-planning.md", ("execution_plan", "worker-router")),
    ("router_to_worker", "03-worker-routing.md", ("launch_manifest", "caller materializes")),
    ("worker_to_aggregator", "07-contracts-ledgers.md", ("handoff_result", "artifact_ref", "Aggregator consumes")),
    ("aggregator_to_review_router", "04-aggregation-review.md", ("aggregation_packet", "Review Router")),
    ("blocked_aggregator_to_meta_judge", "01-harness-layer.md", ("Aggregator -> Meta Judge", "aggregation_ready=false", "judgment_envelope")),
    ("review_router_to_review_layer", "04-aggregation-review.md", ("review-router", "launch_manifest")),
    ("review_layer_to_meta_judge", "01-harness-layer.md", ("Review Layer -> Meta Judge", "handoff_result")),
    ("meta_judge_to_feedback_gate", "05-feedback-lifecycle.md", ("Feedback Trigger Gate", "judgment_envelope")),
    ("feedback_gate_to_orchestrator", "05-feedback-lifecycle.md", ("Feedback always returns to `orchestrator`", "next_loop_start=context-manager", "preserved_allowed_scope")),
)

EXPECTED_AGENT_CATEGORIES = (
    "01-core-development",
    "02-language-specialists",
    "03-infrastructure",
    "04-quality-security",
    "05-data-ai",
    "06-developer-experience",
    "07-specialized-domains",
    "08-business-product",
    "09-meta-orchestration",
    "10-research-analysis",
)

TOML_REQUIRED_KEYS = {"name", "description", "model", "model_reasoning_effort", "sandbox_mode", "developer_instructions"}
ALLOWED_MODELS = {"gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex-spark"}
ALLOWED_REASONING_EFFORTS = {"medium", "high"}
ALLOWED_SANDBOXES = {"read-only", "workspace-write"}
REQUIRED_PROMPT_SECTIONS = ("Working mode:", "Focus on:", "Return:")
PROMPT_CHECK_SECTION_MARKERS = ("Quality checks:", "Mapping checks:", "Design checks:")

RUNTIME_PROMPT_DOC_CHECKS = (
    ("category catalog recursive", "${CODEX_HOME}/agents/<category>/*.toml"),
    ("category router layer", "Category Router Layer"),
    ("category caller materialization", "caller materializes physical child agents"),
    ("physical spawn witness", "spawn_receipt_ref"),
    ("category router closes", "close the router pass after handoff"),
    ("wait agent evidence", "wait_agent"),
    ("close not wait evidence", "`close_agent` cleanup is not wait evidence"),
    ("spawn fork agent type constraint", "Do not call `spawn_agent` with both `fork_context=true` and an explicit `agent_type`"),
    ("mcp critical stages", "MCP-critical stages"),
    ("docker mcp sequentialthinking required", "docker_mcp_sequentialthinking_required=true"),
    ("docker mcp sequentialthinking evidence", "MCP_DOCKER/sequentialthinking:success"),
    ("per agent mcp lifecycle required", "per_agent_mcp_lifecycle_required=true"),
    ("mcp process shutdown required", "mcp_process_shutdown_required=true"),
    ("mcp process residue forbidden", "mcp_process_residue_forbidden=true"),
    ("mcp quiescence snapshot", "mcp_quiescence_snapshot"),
    ("agent fanout budget required", "agent_fanout_budget_required=true"),
    ("fanout budget", "fanout_budget"),
    ("main agent role-pass control stage", "stage_execution_mode=main_agent_role_pass"),
    ("MCP context ledger", "context_ledger_mcp_required=true"),
    ("resident context authority", "context_manager_authority_required=true"),
    ("context revision", "context_revision"),
    ("role pass readiness", "role_pass_readiness"),
    ("orchestrator mcp gate", "mcp_orchestration_required=true"),
    ("context manager mcp gate", "mcp_context_sync_required=true"),
    ("aggregator mcp gate", "mcp_aggregation_required=true"),
    ("logical lane id", "launch_manifest.children[].lane_id"),
    ("physical active passes", "active_passes"),
    ("stage passes", "stage_passes"),
    ("specialist worker layer", "Specialist Worker Layer"),
    ("specialist review layer", "Specialist Review Layer"),
    ("aggregation lane gate", "all lanes are either returned or explicitly classified"),
    ("artifact references", "artifact_ref"),
    ("loop integrity carryover", "preserved_allowed_scope"),
)

# 한국어 주석: logical lane schema는 docs/prompt/contract fixture가 모두 같은 필드 집합을 참조한다.
LOGICAL_LANE_REQUIRED_FIELDS = {
    "lane_id",
    "parent_router_pass_id",
    "agent_category",
    "agent_role",
    "lane_type",
    "owned_scope",
    "expected_artifact",
    "merge_point",
    "return_owner",
    "validation_prompt",
    "context_packet_version",
    "spawn_context_mode",
    "caller_spawn_required",
    "initial_status",
}

SPAWN_CONTEXT_MODES = {"fork_context", "scoped_packet", "scoped_packet_with_waiver"}

LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS = {"agent_id", "submission_id", "wait_handle"}

PHYSICAL_ACTIVE_PASS_REQUIRED_FIELDS = {
    "run_id",
    "loop_id",
    "loop_attempt",
    "lane_id",
    "pass_id",
    "role",
    "agent_category",
    "agent_role",
    "agent_id",
    "submission_id",
    "wait_handle_type",
    "wait_handle",
    "source_launch_manifest_ref",
    "spawn_tool",
    "spawn_receipt_ref",
    "spawned_at",
    "wait_registered_at",
    "owned_scope",
    "merge_point",
    "context_packet_version",
    "status",
}

ACTIVE_PASSES_REQUIRED_FIELDS = {
    "active_passes",
}

STAGE_PASS_REQUIRED_FIELDS = {
    "run_id",
    "loop_id",
    "loop_attempt",
    "stage_pass_id",
    "stage_owner",
    "stage_status",
    "artifact_name",
    "artifact_ref",
    "context_packet_version",
    "schema_status",
    "created_at",
    "closed_at",
    "next_owner",
    "stage_spawn_contract",
}

HANDOFF_RESULT_REQUIRED_FIELDS = {
    "sender",
    "lane_id",
    "pass_id",
    "parent_pass_id",
    "pass_status",
    "owned_scope",
    "artifact_summary",
    "artifact_ref",
    "artifact_kind",
    "evidence_refs",
    "findings",
    "confidence",
    "merge_point",
    "context_packet_version",
    "caller_signals",
}

PASS_STATUSES = {"returned", "superseded", "closed", "timed_out", "schema_invalid"}

CONTRACT_PROVENANCE_REQUIRED_FIELDS = {
    "source_contract_refs",
    "contract_lookup_missing",
}

ORCHESTRATION_REQUEST_REQUIRED_FIELDS = {
    "run_id",
    "loop_id",
    "user_goal",
    "allowed_scope",
    "constraints",
    "direct_answer_exception",
    "risk_flags",
    "success_criteria",
    "feedback_reentry",
    "validation_evidence",
    "loop_carryover",
    "loop_control",
    "contract_provenance",
}

CONTEXT_PACKET_REQUIRED_FIELDS = {
    "source_orchestration_request_ref",
    "next_stage_consumer",
    "context_authority_ref",
    "context_packet_version",
    "context_revision",
    "role_pass_readiness",
    "approved_facts",
    "constraints",
    "evidence_gaps",
    "allowed_scope",
    "exclusions",
    "stale_items",
    "accepted_evidence",
    "artifact_inventory",
    "success_criteria",
    "validation_evidence",
    "loop_carryover",
    "loop_control",
    "contract_provenance",
}

EXECUTION_PLAN_REQUIRED_FIELDS = {
    "wave_id",
    "source_context_packet_ref",
    "context_packet_version",
    "lanes",
    "same_role_parallel_rules",
    "unresolved_assumptions",
    "loop_carryover",
    "loop_control",
    "fanout_budget",
    "contract_provenance",
}

EXECUTION_PLAN_LANE_REQUIRED_FIELDS = {
    "plan_lane_id",
    "owned_scope",
    "expected_artifact",
    "expected_handoff_fields",
    "merge_point",
    "validation_prompt",
    "validation_evidence",
    "review_hint",
}

LAUNCH_MANIFEST_REQUIRED_FIELDS = {
    "manifest_kind",
    "source_parent_ref",
    "context_packet_version",
    "children",
    "loop_control",
    "fanout_budget",
    "contract_provenance",
    "schema_status",
}

WORKER_LAUNCH_MANIFEST_REQUIRED_FIELDS = LAUNCH_MANIFEST_REQUIRED_FIELDS | {"source_execution_plan_ref"}

REVIEW_LAUNCH_MANIFEST_REQUIRED_FIELDS = LAUNCH_MANIFEST_REQUIRED_FIELDS | {"source_aggregation_packet_ref"}

SCHEMA_INVALID_REQUIRED_FIELDS = {
    "manifest_kind",
    "source_parent_ref",
    "context_packet_version",
    "parent_router_pass_id",
    "lane_ids",
    "missing_fields",
    "forbidden_fields",
}

AGGREGATION_PACKET_REQUIRED_FIELDS = {
    "normalized_claims",
    "context_packet_version",
    "source_launch_manifest_ref",
    "source_loop_id",
    "source_loop_attempt",
    "source_pass_statuses",
    "active_pass_snapshot_ref",
    "evidence_refs",
    "artifact_refs",
    "artifact_kinds",
    "source_pass_ids",
    "source_lane_ids",
    "source_parent_pass_ids",
    "blocker_fingerprint",
    "loop_carryover",
    "loop_control",
    "merge_point",
    "confidence_summary",
    "contradiction_list",
    "missing_lanes",
    "schema_invalid_outputs",
    "stale_context_findings",
    "required_review_axes",
    "coverage_status",
    "suggested_reviewer_families",
    "aggregation_input_bundle",
    "contract_provenance",
}

RUN_LEDGER_REQUIRED_FIELDS = {
    "run_id",
    "loop_id",
    "user_goal",
    "allowed_scope",
    "stage",
    "stage_artifact_name",
    "stage_artifact_ref",
    "schema_status",
    "validation_evidence",
    "context_packet_version",
    "loop_attempt",
    "repeat_feedback_count",
    "feedback_gate_mandatory",
    "feedback_required",
    "failure_class",
    "decision",
    "next_owner",
    "created_at",
    "updated_at",
}

BOUNDED_REWORK_REQUEST_REQUIRED_FIELDS = {
    "target",
    "reason",
    "source_judgment_ref",
    "requested_scope_refs",
    "allowed_scope_subset_of",
    "requested_actions",
    "success_criteria_delta",
    "blocker_refs",
}

MISSING_LANE_CLASSES = {
    "unmaterialized_lane",
    "spawn_failed",
    "thread_limit_reached",
    "no_wait_handle",
    "timed_out",
    "superseded",
    "schema_invalid",
}

JUDGMENT_ENVELOPE_REQUIRED_FIELDS = {
    "loop_id",
    "loop_stage",
    "decision",
    "feedback_required",
    "feedback_target",
    "next_owner",
    "next_loop_start",
    "final_blocked_reason",
    "bounded_rework_request",
    "success_criteria",
    "confidence",
    "validation_evidence",
    "review_input_refs",
    "meta_judge_stage_pass_ref",
    "feedback_gate_evidence",
    "review_coverage",
    "review_waivers",
    "source_aggregation_packet_ref",
    "source_blocked_aggregation_ref",
    "loop_carryover",
    "loop_control",
    "gate_evidence_bundle",
    "tool_quiescence_snapshot",
    "contract_provenance",
}

# 한국어 주석: feedback loop가 반복될 때 scope/evidence/blocker가 자유서술로 희석되지 않도록
# 여러 artifact가 같은 nested carryover/control 객체를 공유한다.
LOOP_CARRYOVER_REQUIRED_FIELDS = {
    "preserved_allowed_scope",
    "unmet_success_criteria",
    "unresolved_blockers",
    "rejected_assumptions",
    "required_validation_evidence",
    "context_packet_version",
    "source_judgment_ref",
}

LOOP_CONTROL_REQUIRED_FIELDS = {
    "loop_attempt",
    "repeat_feedback_count",
    "max_loop_attempts",
    "progress_delta",
    "no_progress_action",
}

LOOP_INTEGRITY_REQUIRED_FIELDS = LOOP_CARRYOVER_REQUIRED_FIELDS | LOOP_CONTROL_REQUIRED_FIELDS

FANOUT_BUDGET_REQUIRED_FIELDS = {
    "max_worker_lanes_per_wave",
    "max_review_lanes_per_wave",
    "max_total_child_agents_per_loop",
    "max_same_role_parallel_lanes",
    "max_mcp_concurrent_child_lanes",
    "budget_reason",
    "overflow_policy",
}

DEFAULT_FANOUT_BUDGET = {
    "max_worker_lanes_per_wave": 2,
    "max_review_lanes_per_wave": 2,
    "max_total_child_agents_per_loop": 4,
    "max_same_role_parallel_lanes": 1,
    "max_mcp_concurrent_child_lanes": 1,
}

JUDGMENT_ALLOWED_DECISIONS = {
    "feedback",
    "final output",
}

JUDGMENT_ALLOWED_LOOP_STAGES = {
    "context-sync",
    "planning",
    "execution",
    "aggregation",
    "review",
    "judgment",
    "refinement",
    "complete",
}

CONFIDENCE_LEVELS = {"low", "medium", "high"}

REVIEW_WAIVER_REQUIRED_FIELDS = {
    "axis",
    "reason",
    "blocker_ref",
    "evidence_refs",
    "approver_scope",
    "residual_risk",
    "expiry",
}

REVIEW_COVERAGE_REQUIRED_FIELDS = {
    "required_axes",
    "covered_axes",
    "waived_axes",
}

PROGRESS_DELTA_REQUIRED_FIELDS = {
    "new_artifact_refs",
    "new_evidence_refs",
    "changed_blocker_fingerprint",
    "changed_context_packet_version",
}

FEEDBACK_TARGET_REENTRY = {
    "context-manager": ("orchestrator", "context-manager"),
    "task-planner": ("orchestrator", "context-manager"),
    "worker-layer": ("orchestrator", "context-manager"),
    "aggregator": ("orchestrator", "context-manager"),
    "review-router": ("orchestrator", "context-manager"),
    "review-layer": ("orchestrator", "context-manager"),
    "orchestrator": ("orchestrator", "context-manager"),
    "user": ("orchestrator", "context-manager"),
    "none": ("orchestrator", "none"),
}

ROLE_ALIAS_MAP = {
    "analysis-specialist": ("debugger", "error-detective", "performance-monitor", "data-researcher", "search-specialist"),
    "engineering-specialist": ("python-pro", "build-engineer", "test-automator", "refactoring-specialist", "documentation-engineer"),
    "analysis-reviewer": ("reviewer", "debugger", "error-detective", "performance-monitor"),
    "engineering-reviewer": ("code-reviewer", "architect-reviewer", "test-automator", "reviewer"),
    "search-reviewer": ("docs-researcher", "research-analyst", "competitive-analyst"),
    "policy-safety-reviewer": ("security-auditor", "compliance-auditor", "legal-advisor", "risk-manager"),
}

CANONICAL_STAGE_ROLE_MAP = {
    "orchestrator": "orchestrator",
    "context-manager": "context-manager",
    "task-planner": "task-planner",
    "worker-router": "worker-router",
    "aggregator": "aggregator",
    "review-router": "review-router",
    "meta-judge": "meta-judge",
}

CANONICAL_STAGE_ROLES = set(CANONICAL_STAGE_ROLE_MAP.values())

REVIEW_LANE_ALLOWED_CATEGORIES = {
    "04-quality-security",
    "10-research-analysis",
}

REVIEW_LANE_ALLOWED_ROLES = {
    "legal-advisor",
    "risk-manager",
    "llm-architect",
    "architect-reviewer",
    "chaos-engineer",
    "code-reviewer",
    "compliance-auditor",
    "debugger",
    "error-detective",
    "performance-monitor",
    "reviewer",
    "security-auditor",
    "test-automator",
    "docs-researcher",
    "research-analyst",
    "competitive-analyst",
}

STAGE_RETURN_CONTRACTS = {
    "orchestrator": (
        "JSON branch schema:",
        '"orchestration_request"',
        '"next_owner": "context-manager"',
        "contract_provenance",
        "mcp_orchestration_required=true",
        "docker_mcp_sequentialthinking_required=true",
        "MCP_DOCKER/sequentialthinking:success",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "mcp_quiescence_snapshot",
        "validation_evidence",
        "feedback_reentry",
        "loop_carryover",
        "loop_control",
    ),
    "context-manager": (
        "JSON branch schema:",
        '"context_packet"',
        '"context_packet_version": "<id>"',
        '"next_owner": "task-planner"',
        "context_ledger_mcp_required=true",
        "context_manager_authority_required=true",
        "context_authority_ref",
        "context_revision",
        "role_pass_readiness",
        "accepted_evidence",
        "artifact_inventory",
        "MCP usage evidence",
        "mcp_context_sync_required=true",
        "docker_mcp_sequentialthinking_required=true",
        "MCP_DOCKER/sequentialthinking:success",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "mcp_quiescence_snapshot",
        "loop_carryover",
        "contract_provenance",
        "Do not emit `launch_manifest`, `aggregation_packet`, or `judgment_envelope`.",
    ),
    "task-planner": (
        "JSON branch schema:",
        '"execution_plan"',
        '"next_owner": "worker-router"',
        '"needs_context_manager": true',
        "MCP-required context",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "agent_fanout_budget_required=true",
        "fanout_budget",
        "mcp_quiescence_snapshot",
        "validation_prompt",
        "loop_carryover",
        "loop_control",
        "contract_provenance",
        "Do not emit `launch_manifest`, `aggregation_packet`, or `judgment_envelope`.",
    ),
    "worker-router": (
        "JSON branch schemas:",
        '"launch_manifest"',
        '"manifest_kind": "worker"',
        '"schema_invalid"',
        '"schema_status": "valid"',
        "validation_prompt",
        "contract_provenance",
        "specialist_coverage",
        "agent_fanout_budget_required=true",
        "fanout_budget",
        "stage_execution_mode=main_agent_role_pass",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "mcp_quiescence_snapshot",
        "Return a logical `launch_manifest` and close; never spawn or wait.",
        "Do not return workflow prose after emitting `launch_manifest`.",
    ),
    "aggregator": (
        "Blocked JSON branch schema:",
        '"aggregation_ready": false',
        '"aggregation_inputs"',
        '"next_owner": "meta-judge"',
        "Ready JSON branch schema:",
        '"aggregation_packet"',
        "normalized_claims",
        "MCP evidence",
        "mcp_aggregation_required=true",
        "docker_mcp_sequentialthinking_required=true",
        "MCP_DOCKER/sequentialthinking:success",
        "stage_execution_mode=main_agent_role_pass",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "mcp_quiescence_snapshot",
        "context_packet_version",
        "source_launch_manifest_ref",
        "source_pass_statuses",
        "aggregation_input_bundle",
        "loop_carryover",
        "loop_control",
        "contract_provenance",
        '"next_owner": "review-router"',
        "Mutual exclusion:",
    ),
    "review-router": (
        "JSON branch schemas:",
        '"launch_manifest"',
        '"manifest_kind": "review"',
        '"source_aggregation_packet_ref"',
        '"schema_invalid"',
        '"schema_status": "valid"',
        "MCP/tool evidence gaps",
        "docker_mcp_sequentialthinking_required=true",
        "MCP_DOCKER/sequentialthinking:success",
        "agent_fanout_budget_required=true",
        "fanout_budget",
        "stage_execution_mode=main_agent_role_pass",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "mcp_quiescence_snapshot",
        "required_review_axes",
        "validation_prompt",
        "contract_provenance",
        "Return a logical review `launch_manifest` and close; never spawn or wait.",
        "Do not return workflow prose after emitting review `launch_manifest`.",
    ),
    "meta-judge": (
        "Feedback gate:",
        "JSON branch schema:",
        '"judgment_envelope"',
        "decision=feedback",
        "next_owner=orchestrator",
        "loop_carryover",
        "loop_control",
        "source_aggregation_packet_ref",
        "MCP-required evidence",
        "docker_mcp_sequentialthinking_required=true",
        "MCP_DOCKER/sequentialthinking:success",
        "per_agent_mcp_lifecycle_required=true",
        "mcp_process_shutdown_required=true",
        "mcp_quiescence_snapshot",
        "stage_passes",
        "active_passes",
        "gate_evidence_bundle",
        "tool_quiescence_snapshot",
        "contract_provenance",
        "Final output is forbidden while `feedback_required=true`.",
        "bounded_rework_request={target, reason, source_judgment_ref, requested_scope_refs, allowed_scope_subset_of, requested_actions, success_criteria_delta, blocker_refs}",
        "Feedback target mapping:",
        "Mutual exclusion:",
    ),
}

STAGE_FORBIDDEN_ARTIFACTS = {
    "orchestrator": ("context_packet=", "execution_plan=", "launch_manifest=", "aggregation_packet=", "judgment_envelope="),
    "context-manager": ("execution_plan=", "launch_manifest=", "aggregation_packet=", "judgment_envelope="),
    "task-planner": ("launch_manifest=", "aggregation_packet=", "judgment_envelope="),
    "worker-router": ("context_packet=", "execution_plan=", "aggregation_packet=", "judgment_envelope="),
    "aggregator": ("context_packet=", "execution_plan=", "launch_manifest=", "judgment_envelope="),
    "review-router": ("context_packet=", "execution_plan=", "aggregation_packet=", "judgment_envelope="),
    "meta-judge": ("context_packet=", "execution_plan=", "launch_manifest=", "aggregation_packet="),
}

STAGE_LEDGER_CONTRACTS = {
    "aggregator": ("active_passes", "handoff_result", "aggregation_inputs", "aggregation_input_bundle", "aggregation_ready=false", "close_agent"),
    "review-router": ("launch_manifest.children[]", "agent_id", "submission_id", "wait_handle"),
    "meta-judge": ("active pass summaries", "handoff_result", "failure classifications", "judgment_envelope", "gate_evidence_bundle", "tool_quiescence_snapshot", "close_agent"),
}

SUPPORT_META_BOUNDARY_MARKERS = (
    "This file is a support/meta helper, not a canonical stage owner.",
    "needs_stage_owner=<orchestrator|context-manager|task-planner|worker-router|aggregator|review-router|meta-judge>",
    "Do not compute final readiness",
)

ROUTING_COLLECTION_MARKERS = (
    "Logical Launch Manifest",
    "Physical Active Passes Ledger",
    "Stage Passes Ledger",
    "Judgment Envelope Fields",
    "`launch_manifest.children[]` is not a waitable child handle",
    "agent_category",
    "agent_role",
    "lane_id",
    "all lanes are either returned or explicitly classified",
)

LAUNCH_MANIFEST_DOC_MARKERS = (
    "Launch Manifest Prompt Validation",
    "launch_manifest_schema_gate",
    "caller_spawn_required=true",
    "initial_status=unmaterialized",
    "agent_id",
    "submission_id",
    "wait_handle",
    "wait_agent",
    "schema_invalid",
)

META_PROMPT_LAUNCH_MANIFEST_MARKERS = (
    "Launch manifest validation:",
    "launch_manifest_schema_gate",
    "launch_manifest.children[]",
    "spawn_context_mode",
    "caller_spawn_required",
    "initial_status",
    "wait_agent",
    "source_parent_ref",
    "source_aggregation_packet_ref",
    '"launch_manifest"',
    '"manifest_kind": "worker"',
    '"manifest_kind": "review"',
    '"source_aggregation_packet_ref"',
    '"schema_status": "valid"',
    "parent_router_pass_id",
    "lane_ids",
    "missing_fields",
    "forbidden_fields",
    "Prose-only lane recommendations are invalid.",
    "Logical lanes must not contain `agent_id`, `submission_id`, or `wait_handle`",
    "do not hand off for materialization",
)

META_PROMPT_SOURCE_MARKERS = (
    "Architecture source map:",
    "${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md",
    "${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md",
    "00-canonical-map.md",
    "08-quality-evals.md",
    "source_contract_refs",
    "contract_lookup_missing",
)

META_PROMPT_LEDGER_MARKERS = (
    "Chain ledger validation:",
    "active_passes",
    "pass_id",
    "wait_handle_type",
    "stage_passes",
    "stage_pass_id",
    "handoff_result",
    "artifact_ref",
    "artifact_kind",
    "parent_pass_id",
    "pass_status",
    "Never describe a lane as",
    "aggregation_inputs",
    "aggregation_ready=false",
    "Aggregation consumes returned `handoff_result` values",
)

STAGE_META_LEDGER_MARKERS = {
    "aggregator": (
        "Chain ledger validation:",
        "active_passes",
        "handoff_result",
        "pass_status",
        "artifact_ref",
        "artifact_kind",
        "aggregation_inputs",
        "aggregation_input_bundle",
        "aggregation_ready=false",
        "context_packet_version",
        "close_agent",
    ),
    "review-router": (
        "Chain ledger validation:",
        "aggregation_packet",
        "launch_manifest.children[]",
        "validation_prompt",
        "context_packet_version",
    ),
    "meta-judge": (
        "Chain ledger validation:",
        "active_passes",
        "handoff_result",
        "artifact_ref",
        "artifact_kind",
        "pass_status",
        "judgment_envelope",
        "gate_evidence_bundle",
        "tool_quiescence_snapshot",
        "loop_carryover",
        "close_agent",
    ),
}

META_PROMPT_FEEDBACK_MARKERS = (
    "ready/final/approve/safe-to-proceed",
    "judgment_envelope",
    "decision=feedback",
    "feedback_required=true",
    "final_blocked_reason",
    "next_loop_start=context-manager",
    "bounded_rework_request",
    "success_criteria",
    "loop_carryover",
    "loop_control",
    "Final output is forbidden while `feedback_required=true`.",
)

META_PROMPT_VALIDATION_MARKERS = (
    "validation_owner=top-level caller|harness owner",
    "validation_status=not_run|passed|failed",
    "Never delegate validator execution",
)

FEEDBACK_REQUIRED_MARKERS = (
    "Feedback Trigger Gate",
    "feedback_required",
    "final_blocked_reason",
    "next_loop_start=context-manager",
    "bounded_rework_request",
    "success_criteria",
    "loop_carryover",
    "loop_control",
)

FEEDBACK_FINAL_FORBIDDEN_MARKERS = (
    "feedback_required=true`, final output is forbidden",
    "feedback_required=true`; final output is forbidden",
    "final forbidden when feedback is required",
    "final is forbidden when feedback is required",
    "final output is forbidden when feedback_required",
)
