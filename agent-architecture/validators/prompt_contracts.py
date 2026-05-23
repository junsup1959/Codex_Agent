"""Prompt and TOML contract checks for the global Codex architecture validator."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
import tomllib

from validators.constants import (
    ALLOWED_MODELS,
    ALLOWED_REASONING_EFFORTS,
    ALLOWED_SANDBOXES,
    CANONICAL_STAGE_ROLE_MAP,
    CANONICAL_STAGE_ROLES,
    EXPECTED_AGENT_CATEGORIES,
    LAUNCH_MANIFEST_DOC_MARKERS,
    LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS,
    LOGICAL_LANE_REQUIRED_FIELDS,
    META_PROMPT_FEEDBACK_MARKERS,
    META_PROMPT_LAUNCH_MANIFEST_MARKERS,
    META_PROMPT_SOURCE_MARKERS,
    META_PROMPT_VALIDATION_MARKERS,
    PROMPT_CHECK_SECTION_MARKERS,
    REQUIRED_PROMPT_SECTIONS,
    REVIEW_LANE_ALLOWED_CATEGORIES,
    REVIEW_LANE_ALLOWED_ROLES,
    ROLE_ALIAS_MAP,
    RUNTIME_PROMPT_DOC_CHECKS,
    STAGE_FORBIDDEN_ARTIFACTS,
    STAGE_LEDGER_CONTRACTS,
    STAGE_META_LEDGER_MARKERS,
    STAGE_RETURN_CONTRACTS,
    SUPPORT_META_BOUNDARY_MARKERS,
    TOML_REQUIRED_KEYS,
    required_architecture_doc_paths,
)


def read_text(path: Path) -> str:
    """Read validator-owned text files with the same encoding contract as the caller."""
    return path.read_text(encoding="utf-8")


def _resolve_deprecated_tokens(
    deprecated_contract_tokens: Callable[[], Iterable[str]] | Iterable[str],
) -> list[str]:
    # 한국어 주석: 기존 validator는 함수 형태를 넘기지만, 향후 테스트 fixture가 list를 직접
    # 넘겨도 동일한 검사를 재사용할 수 있게 토큰 입력만 정규화한다.
    if callable(deprecated_contract_tokens):
        return list(deprecated_contract_tokens())
    return list(deprecated_contract_tokens)


def check_prompt_contracts(validator, deprecated_contract_tokens) -> None:
    """Run prompt/TOML/runtime prompt/launch-manifest prompt checks.

    The validator argument is intentionally duck-typed so the main validator can
    delegate here without introducing inheritance or import coupling.
    """
    tokens = _resolve_deprecated_tokens(deprecated_contract_tokens)
    _check_prompts(validator, tokens)
    _check_toml(validator)
    _check_agent_dependency_contracts(validator)
    _check_runtime_prompt_contracts(validator)
    _check_launch_manifest_prompt_validation(validator)
    _check_meta_prompt_chain_contracts(validator)
    _check_stage_return_contracts(validator)


def _check_prompts(validator, deprecated_tokens: list[str]) -> None:
    validator.log("runtime prompt 폐기 계약 토큰 확인")
    prompt_files = sorted(validator.agents_dir.rglob("*.toml"))
    joined = "\n".join(read_text(path) for path in prompt_files)

    # 한국어 주석: 폐기된 schema/token이 runtime prompt 전체에 다시 들어오면 새
    # launch_manifest/aggregation 계약과 섞여 router가 옛 handoff 방식을 되살릴 수 있다.
    for text in deprecated_tokens:
        validator.assert_not_contains("forbidden_text_prompts", joined, text)

    # 한국어 주석: prompt를 바꾼 agent가 검증 hook을 잃으면 architecture drift가 난 뒤에도
    # 최종 승인 전에 validator 실행을 강제할 근거가 사라진다.
    for prompt_file in prompt_files:
        validator.assert_contains(
            "architecture_validation_hook_prompts",
            read_text(prompt_file),
            "architecture_validation_required=true",
        )


def _check_toml(validator) -> None:
    validator.log("recursive category TOML catalog check")

    # 한국어 주석: category directory는 router의 1차 dispatch table이므로 폴더와 최소
    # TOML 존재를 고정해 category routing이 문서와 runtime 사이에서 비는 것을 막는다.
    for category in EXPECTED_AGENT_CATEGORIES:
        path = validator.agents_dir / category
        validator.assert_condition(
            "agent_category_exists",
            path.is_dir(),
            f"agent category folder missing: {category}",
        )
        validator.assert_condition(
            "agent_category_has_toml",
            any(path.glob("*.toml")),
            f"agent category has no TOML: {category}",
        )

    toml_failures: list[str] = []
    prompt_files = sorted(validator.agents_dir.rglob("*.toml"))

    # 한국어 주석: recursive TOML 검사는 nested category prompt까지 포함해 필수 key,
    # model tier, sandbox 정책, developer_instructions shape가 흐트러지는 것을 한 번에 잡는다.
    for path in prompt_files:
        try:
            data = tomllib.loads(read_text(path))
        except Exception as exc:
            toml_failures.append(f"{path}: TOML parse failed: {exc}")
            continue

        missing = sorted(TOML_REQUIRED_KEYS - set(data))
        if missing:
            toml_failures.append(f"{path}: required key missing: {', '.join(missing)}")
            continue

        if data["name"] != path.stem:
            toml_failures.append(f"{path}: name does not match file stem: {data['name']} != {path.stem}")
        if data["model"] not in ALLOWED_MODELS:
            toml_failures.append(f"{path}: unsupported model: {data['model']}")
        if data["model_reasoning_effort"] not in ALLOWED_REASONING_EFFORTS:
            toml_failures.append(f"{path}: unsupported model_reasoning_effort: {data['model_reasoning_effort']}")
        if data.get("sandbox_mode") not in ALLOWED_SANDBOXES:
            toml_failures.append(f"{path}: unsupported sandbox_mode: {data.get('sandbox_mode')}")

        instructions = data["developer_instructions"]
        for section in REQUIRED_PROMPT_SECTIONS:
            if section not in instructions:
                toml_failures.append(f"{path}: developer_instructions section missing: {section}")
        if not any(marker in instructions for marker in PROMPT_CHECK_SECTION_MARKERS):
            toml_failures.append(f"{path}: developer_instructions checks section missing")
        if "architecture_validation_required=true" not in instructions:
            toml_failures.append(f"{path}: architecture validation hook missing")

    validator.assert_condition(
        "toml_recursive_catalog_check",
        not toml_failures,
        "TOML catalog validation failed: " + " | ".join(toml_failures[:20]),
    )
    if not toml_failures:
        validator.log(f"TOML_OK {len(prompt_files)}")


def _check_agent_dependency_contracts(validator) -> None:
    validator.log("agent dependency catalog check")
    catalog: dict[str, set[str]] = {}
    role_locations: dict[str, list[str]] = {}
    prompt_files = sorted(validator.agents_dir.rglob("*.toml"))
    for category in EXPECTED_AGENT_CATEGORIES:
        category_path = validator.agents_dir / category
        roles = {path.stem for path in category_path.glob("*.toml")} if category_path.is_dir() else set()
        catalog[category] = roles
        for role in roles:
            role_locations.setdefault(role, []).append(category)

    duplicate_roles = {role: locations for role, locations in role_locations.items() if len(locations) > 1}
    validator.assert_condition("agent_dependency_unique_role_names", not duplicate_roles, f"duplicate role names across categories: {duplicate_roles}")
    validator.assert_condition(
        "agent_dependency_family_alias_not_runtime_role",
        not (set(ROLE_ALIAS_MAP) & set(role_locations)),
        f"family alias must not be a concrete runtime TOML role: {sorted(set(ROLE_ALIAS_MAP) & set(role_locations))}",
    )

    stage_category = "09-meta-orchestration"
    for role in CANONICAL_STAGE_ROLES:
        validator.assert_condition("agent_dependency_stage_role_present", role in catalog.get(stage_category, set()), f"canonical stage TOML missing: {role}")
        validator.assert_condition("agent_dependency_stage_role_scoped", role_locations.get(role) == [stage_category], f"canonical stage role must live only under {stage_category}: {role} -> {role_locations.get(role)}")

    for alias, concrete_roles in ROLE_ALIAS_MAP.items():
        missing = [role for role in concrete_roles if role not in role_locations]
        stage_targets = [role for role in concrete_roles if role in CANONICAL_STAGE_ROLES]
        validator.assert_condition("agent_dependency_alias_targets_exist", not missing, f"{alias} target TOML missing: {missing}")
        validator.assert_condition("agent_dependency_alias_not_stage_owner", not stage_targets, f"{alias} points to canonical stage role: {stage_targets}")

    explicit_review_roles_missing = [role for role in REVIEW_LANE_ALLOWED_ROLES if role not in role_locations]
    validator.assert_condition("agent_dependency_review_roles_exist", not explicit_review_roles_missing, f"review support TOML missing: {explicit_review_roles_missing}")
    validator.assert_condition("agent_dependency_review_categories_exist", REVIEW_LANE_ALLOWED_CATEGORIES <= set(catalog), f"review categories missing: {sorted(REVIEW_LANE_ALLOWED_CATEGORIES - set(catalog))}")

    worker_router = read_text(validator.agents_dir / stage_category / "worker-router.toml")
    review_router = read_text(validator.agents_dir / stage_category / "review-router.toml")
    meta_judge = read_text(validator.agents_dir / stage_category / "meta-judge.toml")
    validator.assert_contains("agent_dependency_worker_router_specialist_only", worker_router, "at least one concrete specialist role is selected for every executable lane")
    validator.assert_contains("agent_dependency_worker_router_concrete_role_resolution", worker_router, "every emitted `agent_role` resolves to one concrete TOML file and is not a family alias or canonical stage owner")
    validator.assert_contains("agent_dependency_worker_router_scoped_packet", worker_router, 'spawn_context_mode="scoped_packet"')
    validator.assert_contains("agent_dependency_review_router_concrete_role_resolution", review_router, "every emitted `agent_role` resolves to one concrete TOML file and is not a family alias or canonical stage owner")
    validator.assert_contains("agent_dependency_review_router_scoped_packet", review_router, 'spawn_context_mode="scoped_packet"')
    validator.assert_contains("agent_dependency_feedback_gate_meta_judge_internal", meta_judge, "not a separate long-lived worker")
    for path in prompt_files:
        text = read_text(path)
        if path.stem not in CANONICAL_STAGE_ROLES:
            validator.assert_not_contains("agent_dependency_specialist_not_stage_owner", text, "Own only the canonical ")
        if path.stem != "meta-judge":
            validator.assert_not_contains("agent_dependency_feedback_gate_only_meta_judge", text, "Feedback Trigger Gate")


def _check_runtime_prompt_contracts(validator) -> None:
    validator.log("category routing contract check")
    # 한국어 주석: prompt 계약은 schema가 승인한 필수 architecture 문서만 읽고 임의 md는 참조하지 않는다.
    docs = "\n".join(read_text(path) for path in required_architecture_doc_paths(validator.root) if path.exists())

    # 한국어 주석: 문서의 routing contract 문구가 빠지면 runtime prompt가 category router,
    # caller materialization, active_passes 경계를 잘못 해석해 장기 실행 router를 만들 수 있다.
    for name, need in RUNTIME_PROMPT_DOC_CHECKS:
        validator.assert_contains(f"runtime_prompt_contract:{name}", docs, need)


def _check_launch_manifest_prompt_validation(validator) -> None:
    validator.log("launch manifest prompt validation check")
    # 한국어 주석: launch manifest 문서 검증도 constants의 필수 문서 inventory에만 묶는다.
    docs = "\n".join(read_text(path) for path in required_architecture_doc_paths(validator.root) if path.exists())
    stage_dir = validator.agents_dir / "09-meta-orchestration"
    prompt_files = [stage_dir / "worker-router.toml", stage_dir / "review-router.toml"]
    prompt_text = "\n".join(read_text(path) for path in prompt_files if path.exists())

    # 한국어 주석: architecture docs가 logical lane과 physical wait handle을 구분하도록 고정해
    # launch_manifest.children[]가 곧바로 wait 가능한 child로 오해되는 회귀를 막는다.
    for marker in LAUNCH_MANIFEST_DOC_MARKERS:
        validator.assert_contains("launch_manifest_prompt_docs", docs, marker)

    # 한국어 주석: meta-orchestration prompt에는 materialization 전에 schema gate를 열고,
    # invalid lane을 handoff하지 않는 운영 문구가 모두 들어 있어야 한다.
    for marker in META_PROMPT_LAUNCH_MANIFEST_MARKERS:
        validator.assert_contains("launch_manifest_prompt_toml", prompt_text, marker)
    for path in prompt_files:
        text = read_text(path)
        validator.assert_contains("launch_manifest_prompt_each_meta", text, "Launch manifest validation:")
        validator.assert_contains("launch_manifest_prompt_each_meta", text, "launch_manifest_schema_gate")

    # 한국어 주석: synthetic invalid lane fixture는 누락 field와 금지된 physical handle을 동시에
    # 넣어 prompt gate가 schema_invalid로 막아야 하는 실제 실패 모양을 고정한다.
    invalid_lane = {
        "lane_id": "lane-bad-1",
        "agent_category": "09-meta-orchestration",
        "agent_role": "workflow-orchestrator",
        "lane_type": "worker",
        "owned_scope": "bad manifest fixture",
        "expected_artifact": "handoff_result",
        "merge_point": "aggregation_packet.inputs",
        "return_owner": "aggregator",
        "validation_prompt": "invalid fixture should still carry work prompt",
        "context_packet_version": "ctx-1",
        "caller_spawn_required": True,
        "initial_status": "unmaterialized",
        "agent_id": "must-not-be-here",
    }
    missing = LOGICAL_LANE_REQUIRED_FIELDS - set(invalid_lane)
    forbidden = LOGICAL_LANE_FORBIDDEN_WAIT_FIELDS & set(invalid_lane)
    schema_status = "schema_invalid" if missing or forbidden else "valid"
    validator.assert_condition(
        "launch_manifest_fixture_invalid",
        schema_status == "schema_invalid",
        "invalid launch_manifest lane 이 schema_invalid 로 차단되지 않음",
    )
    validator.assert_condition(
        "launch_manifest_fixture_missing_detected",
        "parent_router_pass_id" in missing,
        "logical lane 누락 필드 감지 실패",
    )
    validator.assert_condition(
        "launch_manifest_fixture_forbidden_detected",
        "agent_id" in forbidden,
        "logical lane 의 waitable handle 금지 감지 실패",
    )


def _check_meta_prompt_chain_contracts(validator) -> None:
    validator.log("meta prompt chain contract check")
    prompt_files = sorted((validator.agents_dir / "09-meta-orchestration").glob("*.toml"))
    stage_role_names = set(CANONICAL_STAGE_ROLE_MAP.values())
    support_files = [path for path in prompt_files if path.stem not in stage_role_names]
    # 한국어 주석: 모든 meta prompt는 source/validation hook을 가져야 하지만, stage artifact
    # 산출 책임은 canonical stage TOML에만 둔다. support prompt가 judgment/router 책임을 훔치면
    # Context Manager 같은 보조 역할이 final 판단까지 수행하는 회귀가 생긴다.
    for path in prompt_files:
        text = read_text(path)
        for marker in META_PROMPT_SOURCE_MARKERS:
            validator.assert_contains("meta_prompt_source_map", text, marker)
        for marker in META_PROMPT_VALIDATION_MARKERS:
            validator.assert_contains("meta_prompt_validation_status", text, marker)
        if path.stem in STAGE_META_LEDGER_MARKERS:
            for marker in STAGE_META_LEDGER_MARKERS[path.stem]:
                validator.assert_contains("meta_prompt_ledger_markers", text, marker)
    for path in support_files:
        text = read_text(path)
        for marker in SUPPORT_META_BOUNDARY_MARKERS:
            validator.assert_contains("support_meta_boundary", text, marker)
    meta_judge_path = validator.agents_dir / "09-meta-orchestration" / "meta-judge.toml"
    validator.assert_condition("meta_judge_toml_exists_for_feedback", meta_judge_path.is_file(), f"meta-judge TOML missing: {meta_judge_path}")
    meta_judge_text = read_text(meta_judge_path) if meta_judge_path.exists() else ""
    for marker in META_PROMPT_FEEDBACK_MARKERS:
        validator.assert_contains("meta_judge_feedback_gate", meta_judge_text, marker)
    validator.assert_not_contains(
        "meta_judge_no_rework_restate_contradiction",
        meta_judge_text,
        "bounded_rework_request restates `loop_carryover` and `loop_control`",
    )


def _check_stage_return_contracts(validator) -> None:
    validator.log("canonical stage return contract check")
    stage_dir = validator.agents_dir / "09-meta-orchestration"
    # 한국어 주석: canonical stage 이름이 실제 TOML 파일로 존재하고 각 파일이 자기 stage artifact만
    # 반환하도록 강제한다. marker-only 공통 prompt가 모든 stage 책임을 섞는 회귀를 막는다.
    for stage_name, role_name in CANONICAL_STAGE_ROLE_MAP.items():
        path = stage_dir / f"{role_name}.toml"
        validator.assert_condition("canonical_stage_toml_exists", path.is_file(), f"{stage_name} stage TOML missing: {path}")
        text = read_text(path) if path.exists() else ""
        validator.assert_contains("stage_json_only_return", text, "Return exactly one RFC 8259 JSON object.")
        validator.assert_contains("stage_json_native_types", text, "String-typed fields use JSON strings; booleans, numbers, arrays, and objects use native JSON types.")
        validator.assert_contains(
            "stage_validation_fields_in_return_contract",
            text,
            "Every branch also includes top-level validation fields `architecture_validation_required`, `validation_owner`, and `validation_status`",
        )
        for marker in STAGE_RETURN_CONTRACTS[role_name]:
            validator.assert_contains(f"stage_return_contract:{role_name}", text, marker)
        for marker in STAGE_FORBIDDEN_ARTIFACTS[role_name]:
            validator.assert_not_contains(f"stage_forbidden_artifact:{role_name}", text, marker)
        for marker in STAGE_LEDGER_CONTRACTS.get(role_name, ()):
            validator.assert_contains(f"stage_ledger_contract:{role_name}", text, marker)
