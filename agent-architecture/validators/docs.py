"""Documentation checks for the global Codex architecture validator."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from validators.constants import (
    APPROVED_ARCHITECTURE_MD_NAMES,
    ARCHITECTURE_REQUIRED_TEXT,
    CANONICAL_LOOP,
    DETAIL_CONTRACTS,
    DETAIL_DOC_NAMES,
    ROLE_ALIAS_MAP,
    STAGE_CHAIN_DOC_CONTRACTS,
    required_architecture_doc_paths,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _resolve_deprecated_tokens(deprecated_contract_tokens: Callable[[], Iterable[str]] | Iterable[str]) -> list[str]:
    if callable(deprecated_contract_tokens):
        return list(deprecated_contract_tokens())
    return list(deprecated_contract_tokens)


def check_docs(validator, agents_path: Path, index_path: Path, deprecated_contract_tokens) -> None:
    """Validate architecture markdown pointers, maps, and document contracts."""
    validator.log("index/map links and deprecated contract tokens check")

    # Obsidian is a personal record, not the runtime contract source of truth.
    # Read only schema-approved architecture docs so private notes never fail validation.
    mapper_path = validator.arch_dir / "AGENT-ARCHITECTURE-MAPPER.md"
    doc_files = required_architecture_doc_paths(validator.root)
    joined_docs = "\n".join(read_text(path) for path in doc_files if path.exists())
    actual_md_names = {path.name for path in validator.arch_dir.glob("*.md")}
    validator.assert_condition(
        "architecture_md_inventory_exact",
        actual_md_names == APPROVED_ARCHITECTURE_MD_NAMES,
        f"unexpected architecture md inventory: extra={sorted(actual_md_names - APPROVED_ARCHITECTURE_MD_NAMES)}, missing={sorted(APPROVED_ARCHITECTURE_MD_NAMES - actual_md_names)}",
    )

    for text in ARCHITECTURE_REQUIRED_TEXT:
        validator.assert_contains("required_text_docs", joined_docs, text)

    # Retired contract names are hard failures because mixed old/new schemas break handoff routing.
    for text in _resolve_deprecated_tokens(deprecated_contract_tokens):
        validator.assert_not_contains("forbidden_text_docs", joined_docs, text)

    # The canonical loop string is intentionally literal across index, mapper, and map docs.
    for file in [index_path, mapper_path, validator.arch_dir / "00-canonical-map.md"]:
        if file.exists():
            validator.assert_contains("canonical_loop_consistency", read_text(file), CANONICAL_LOOP)

    agents_map = read_text(agents_path) if agents_path.exists() else ""
    mapper_map = read_text(mapper_path) if mapper_path.exists() else ""
    index_map = read_text(index_path) if index_path.exists() else ""

    validator.assert_contains("agents_pointer_index", agents_map, "AGENT-ARCHITECTURE.md")
    validator.assert_contains("agents_pointer_mapper", agents_map, "AGENT-ARCHITECTURE-MAPPER.md")
    validator.assert_contains("agents_init_template", agents_map, "AGENTS.local-template.md")
    validator.assert_contains("agents_post_init_normalizer", joined_docs, "apply-agents-inheritance.py")

    normalizer_path = validator.arch_dir / "apply-agents-inheritance.py"
    normalizer_text = read_text(normalizer_path) if normalizer_path.exists() else ""
    validator.assert_contains("normalizer_validation_hook", normalizer_text, "architecture_validation_required=true")
    validator.assert_contains("normalizer_runs_validator", normalizer_text, "validate-agent-architecture.py")
    validator.assert_contains("normalizer_repair_status", normalizer_text, "inheritance_repaired")

    for name in DETAIL_DOC_NAMES:
        validator.assert_contains("mapper_detail_map", mapper_map, name)
        validator.assert_contains("index_detail_map", index_map, name)

    for file in doc_files:
        if file.exists():
            validator.assert_contains("architecture_validation_hook_docs", read_text(file), "architecture_validation_required=true")

    for file_name, need in DETAIL_CONTRACTS:
        path = validator.arch_dir / file_name
        if path.exists():
            validator.assert_contains("detail_contract", read_text(path), need)

    # Validate each canonical edge with concrete artifact or re-entry markers, not just the loop text.
    for edge_name, file_name, markers in STAGE_CHAIN_DOC_CONTRACTS:
        path = validator.arch_dir / file_name
        text = read_text(path) if path.exists() else ""
        for marker in markers:
            validator.assert_contains(f"stage_chain_contract:{edge_name}", text, marker)

    # Role aliases must resolve to real specialist TOML files so routers cannot emit phantom roles.
    runtime_roles = {path.stem for path in validator.agents_dir.rglob("*.toml")}
    for alias, concrete_roles in ROLE_ALIAS_MAP.items():
        validator.assert_contains("role_alias_documented", joined_docs, f"`{alias}`")
        missing_roles = [role for role in concrete_roles if role not in runtime_roles]
        validator.assert_condition("role_alias_resolves_to_toml", not missing_roles, f"{alias} alias target TOML missing: {missing_roles}")
