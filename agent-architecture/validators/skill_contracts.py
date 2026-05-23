"""Skill contract checks for mandatory architecture stage skills."""

from __future__ import annotations

import json
from pathlib import Path


MANDATORY_SKILLS = (
    "orchestrator",
    "context-ledger",
    "task-planner",
    "worker",
    "review-distributor",
    "review",
    "feedbackgate",
)

OPTIONAL_SKILLS = ("docker-memory",)

REQUIRED_FIELDS = (
    "schema_version",
    "skill_name",
    "activation_ref",
    "mandatory_for_architecture_required",
    "stage_owner",
    "stage_execution_mode",
    "purpose",
    "input_artifacts",
    "output_artifacts",
    "forbidden_outputs",
    "required_evidence",
    "source_docs",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _skill_frontmatter_name(skill_text: str) -> str | None:
    for line in skill_text.splitlines()[:12]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def _assert_list_field(validator, contract_path: Path, contract: dict, field: str) -> None:
    value = contract.get(field)
    validator.assert_condition(
        "skill_contract_list_field",
        isinstance(value, list) and all(isinstance(item, str) and item for item in value),
        f"{contract_path} field must be a non-empty string list: {field}",
    )


def check_skill_contracts(validator) -> None:
    """Validate stage skill contracts and their documentation bindings."""
    validator.log("stage skill contract check")
    skills_dir = validator.root / "skills"
    runtime_steps = validator.arch_dir / "09-runtime-orchestration-steps.md"
    runtime_text = runtime_steps.read_text(encoding="utf-8") if runtime_steps.exists() else ""

    for skill_name in MANDATORY_SKILLS + OPTIONAL_SKILLS:
        skill_dir = skills_dir / skill_name
        skill_md = skill_dir / "SKILL.md"
        contract_path = skill_dir / "contract.json"
        scripts_dir = skill_dir / "scripts"
        validator.assert_file_exists(skill_md)
        validator.assert_file_exists(contract_path)
        if not skill_md.exists() or not contract_path.exists():
            continue

        try:
            contract = _read_json(contract_path)
        except json.JSONDecodeError as exc:
            validator.fail(f"skill_contract_json - {contract_path} is invalid JSON: {exc}")
            continue

        for field in REQUIRED_FIELDS:
            validator.assert_condition(
                "skill_contract_required_field",
                field in contract,
                f"{contract_path} missing field: {field}",
            )

        skill_text = skill_md.read_text(encoding="utf-8")
        frontmatter_name = _skill_frontmatter_name(skill_text)
        validator.assert_condition(
            "skill_contract_name_matches_skill_md",
            contract.get("skill_name") == frontmatter_name == skill_name,
            f"{contract_path} skill_name must match SKILL.md name and folder: {skill_name}",
        )
        validator.assert_condition(
            "skill_contract_activation_ref",
            contract.get("activation_ref") == f"${skill_name}",
            f"{contract_path} activation_ref must be ${skill_name}",
        )
        validator.assert_condition(
            "skill_contract_schema_version",
            contract.get("schema_version") == 1,
            f"{contract_path} schema_version must be 1",
        )

        for field in ("input_artifacts", "output_artifacts", "forbidden_outputs", "required_evidence", "source_docs"):
            _assert_list_field(validator, contract_path, contract, field)

        is_mandatory = skill_name in MANDATORY_SKILLS
        validator.assert_condition(
            "skill_contract_mandatory_flag",
            contract.get("mandatory_for_architecture_required") is is_mandatory,
            f"{contract_path} mandatory_for_architecture_required must be {is_mandatory}",
        )

        if is_mandatory:
            validator.assert_contains("mandatory_skill_documented_runtime_steps", runtime_text, f"${skill_name}")
            validator.assert_condition(
                "mandatory_skill_scripts_dir",
                scripts_dir.is_dir() and any(scripts_dir.glob("*.py")),
                f"{skill_dir} must include scripts/*.py for stage-local preflight",
            )
            validator.assert_condition(
                "mandatory_skill_main_agent_role_pass",
                contract.get("stage_execution_mode") == "main_agent_role_pass",
                f"{contract_path} mandatory stages must run as main_agent_role_pass unless separately overridden",
            )
        else:
            validator.assert_condition(
                "optional_skill_not_mandatory",
                contract.get("mandatory_for_architecture_required") is False,
                f"{contract_path} optional helper must not become mandatory",
            )
