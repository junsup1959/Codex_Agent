#!/usr/bin/env python3
"""Canonical entrypoint for the global Codex agent architecture validator."""
from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys
from pathlib import Path

from validators.contracts import check_feedback_loop_contracts, check_routing_collection_contracts
from validators.docs import check_docs
from validators.prompt_contracts import check_prompt_contracts
from validators.skill_contracts import check_skill_contracts


def configure_utf8_stdio() -> None:
    # Keep stdout/stderr deterministic on Windows terminals and sandboxed shells.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_utf8_stdio()


class Validator:
    def __init__(self, root: Path, source: str) -> None:
        self.root = root
        self.source = source
        self.arch_dir = root / "agent-architecture"
        self.agents_dir = root / "agents"
        self.failures: list[str] = []
        self.checks_run = 0

    def log(self, message: str) -> None:
        print(f"[architecture validation] {message}")

    def fail(self, message: str) -> None:
        self.failures.append(message)
        print(f"[architecture validation][FAIL] {message}")

    def assert_condition(self, name: str, condition: bool, failure_message: str) -> None:
        # The check count is a drift signal: sudden drops usually mean validator scope regressed.
        self.checks_run += 1
        if not condition:
            self.fail(f"{name} - {failure_message}")

    def assert_file_exists(self, path: Path) -> None:
        self.assert_condition("file_exists", path.is_file(), f"required file missing: {path}")

    def assert_contains(self, name: str, haystack: str, needle: str) -> None:
        self.assert_condition(name, needle in haystack, f"required text missing: {needle}")

    def assert_not_contains(self, name: str, haystack: str, needle: str) -> None:
        self.assert_condition(name, needle not in haystack, f"forbidden text found: {needle}")

    def assert_line_limit(self, path: Path, max_lines: int, label: str) -> None:
        count = len(read_text(path).splitlines())
        self.log(f"{label} line count: {count}")
        self.assert_condition("line_limit", count <= max_lines, f"{label} too long: {count} lines, limit {max_lines}")

    def required_files(self) -> list[Path]:
        names = [
            "AGENTS.md",
            "agent-architecture/AGENT-ARCHITECTURE.md",
            "agent-architecture/AGENT-ARCHITECTURE-MAPPER.md",
            "agent-architecture/AGENTS.local-template.md",
            "agent-architecture/apply-agents-inheritance.py",
            "agent-architecture/validate-runtime-artifact.py",
            "agent-architecture/validate-session-runtime.py",
            "agent-architecture/validate-skill-contracts.py",
            "agent-architecture/harness_gate.py",
            "agent-architecture/harness_handoff.py",
            "agent-architecture/validate-runtime-gate-smoke.py",
            "agent-architecture/00-canonical-map.md",
            "agent-architecture/01-harness-layer.md",
            "agent-architecture/02-context-planning.md",
            "agent-architecture/03-worker-routing.md",
            "agent-architecture/04-aggregation-review.md",
            "agent-architecture/05-feedback-lifecycle.md",
            "agent-architecture/06-agent-roster-models.md",
            "agent-architecture/07-contracts-ledgers.md",
            "agent-architecture/08-quality-evals.md",
            "agent-architecture/validators/__init__.py",
            "agent-architecture/validators/constants.py",
            "agent-architecture/validators/docs.py",
            "agent-architecture/validators/prompt_contracts.py",
            "agent-architecture/validators/contracts.py",
            "agent-architecture/validators/skill_contracts.py",
        ]
        return [self.root / name for name in names]

    def check_runtime_gate_scripts(self) -> None:
        self.log("runtime artifact validator and harness gate script check")
        scripts = [
            self.arch_dir / "validate-runtime-artifact.py",
            self.arch_dir / "validate-session-runtime.py",
            self.arch_dir / "validate-skill-contracts.py",
            self.arch_dir / "harness_gate.py",
            self.arch_dir / "harness_handoff.py",
            self.arch_dir / "validate-runtime-gate-smoke.py",
        ]
        for script in scripts:
            try:
                py_compile.compile(str(script), doraise=True)
                compiled = True
                detail = ""
            except py_compile.PyCompileError as exc:
                compiled = False
                detail = str(exc)
            self.assert_condition("runtime_gate_script_compiles", compiled, f"{script} compile failed: {detail}")

        runtime_text = read_text(self.arch_dir / "validate-runtime-artifact.py")
        session_text = read_text(self.arch_dir / "validate-session-runtime.py")
        gate_text = read_text(self.arch_dir / "harness_gate.py")
        handoff_text = read_text(self.arch_dir / "harness_handoff.py")
        smoke_text = read_text(self.arch_dir / "validate-runtime-gate-smoke.py")

        for marker in ("validate_payload", "STAGE_ARTIFACTS", "active_passes", "blocked_aggregation", "judgment_envelope"):
            self.assert_contains("runtime_artifact_validator_marker", runtime_text, marker)
        for marker in (
            "validate_session",
            "session.final_without_physical_bundle",
            "session.feedback_restart_skipped",
            "session.direct_specialist_without_worker_router",
            "session.spawned_child_not_waited",
            "session.wait_returned_empty",
            "session.local_stage_simulation",
            "architecture_triggered",
            "NONTRIVIAL_TRIGGER_MARKERS",
            "spawn_agent",
            "wait_agent",
        ):
            self.assert_contains("session_runtime_validator_marker", session_text, marker)
        for marker in ("gate_stage_output", "allow_next_stage", "validate-runtime-artifact.py", "previous_judgment", "DEFAULT_FAILURE_ROUTE"):
            self.assert_contains("harness_gate_marker", gate_text, marker)
        for marker in ("handoff_stage_output", "harness_gate.gate_stage_output", "previous_judgment", "next_input_payload", "ledger-out"):
            self.assert_contains("harness_handoff_marker", handoff_text, marker)
        for marker in (
            "runtime_valid_worker_manifest",
            "runtime_valid_review_manifest_dependency",
            "runtime_missing_specialist_blocks",
            "runtime_stage_owner_as_worker_blocks",
            "runtime_non_review_specialist_in_review_blocks",
            "materialization_active_pass_role_mismatch_blocks",
            "materialization_stray_active_pass_blocks",
            "runtime_specialist_fork_context_blocks",
            "runtime_missing_context_waiver_blocks",
            "gate_blocks_invalid_manifest",
            "feedback_judgment_preserves_feedback",
            "judgment_missing_physical_gate_evidence_blocks",
            "final_missing_feedback_gate_evidence_blocks",
            "feedback_string_only_judgment_blocks",
            "final_string_only_judgment_blocks",
            "active_passes_missing_spawn_receipt_blocks",
            "lineage_fourth_loop_with_progress_allows",
            "lineage_wrong_loop_id_blocks",
            "lineage_repeat_count_not_incremented_blocks",
            "lineage_repeated_no_progress_escape_blocks",
            "meta_judge_blocked_branch_source_ref_matches",
            "runtime_cli_malformed_json_exit_one",
            "handoff_cli_previous_judgment_lineage_blocks",
            "final_source_ref_mismatch_blocks",
            "materialization_active_pass_context_mismatch_blocks",
            "aggregation_missing_lane_item_shape_blocks",
            "blocked_aggregation_bad_input_shapes_block",
        ):
            self.assert_contains("runtime_gate_smoke_marker", smoke_text, marker)

        completed = subprocess.run(
            [sys.executable, str(self.arch_dir / "validate-runtime-gate-smoke.py")],
            cwd=str(self.arch_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assert_condition(
            "runtime_gate_smoke_executes",
            completed.returncode == 0,
            f"runtime gate smoke failed: stdout={completed.stdout} stderr={completed.stderr}",
        )

    def run(self) -> int:
        self.log("inventory check start")
        self.log(f"CODEX_HOME resolved from {self.source}: {self.root}")
        for file in self.required_files():
            self.assert_file_exists(file)
        self.check_runtime_gate_scripts()
        self.assert_condition(
            "root_arch_absent",
            not (self.root / "AGENT-ARCHITECTURE.md").exists(),
            "root AGENT-ARCHITECTURE.md must not exist; keep the index under agent-architecture/",
        )

        agents_path = self.root / "AGENTS.md"
        index_path = self.arch_dir / "AGENT-ARCHITECTURE.md"
        if agents_path.exists():
            self.assert_line_limit(agents_path, 80, "AGENTS.md")
        if index_path.exists():
            self.assert_line_limit(index_path, 80, "AGENT-ARCHITECTURE.md")
        for detail in sorted(self.arch_dir.glob("*.md")):
            if detail.name != "AGENT-ARCHITECTURE.md":
                self.assert_line_limit(detail, 180, detail.name)

        check_docs(self, agents_path, index_path, deprecated_contract_tokens)
        check_prompt_contracts(self, deprecated_contract_tokens)
        check_skill_contracts(self)
        check_routing_collection_contracts(self)
        check_feedback_loop_contracts(self)

        if self.failures:
            self.log(f"failure count: {len(self.failures)}")
            return 1
        self.log(f"PASS: global agent architecture invariants passed (checks={self.checks_run})")
        return 0


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def deprecated_contract_tokens() -> list[str]:
    # Block retired contract/schema names while allowing real paths and category folders.
    return [
        "${CODEX_HOME}/AGENT-ARCHITECTURE.md",
        "review_launch_manifest",
        "agent_id_or_submission_id",
        "adviser",
        "governor",
        "free-worker",
        "blocked -> adviser",
        "blocked->adviser",
        "risky -> governor",
        "risky->governor",
    ]


def show_explain() -> None:
    print("[architecture validation] validator maps files, runtime prompts, schemas, and handoff tools.")
    print("[architecture validation] validate-agent-architecture.py is the canonical entrypoint; validators/*.py hold scoped checks.")
    rows = [
        ("$Root", "CODEX_HOME(Process -> script/profile fallback)", "global agent settings root"),
        ("docs", "validators/docs.py", "map docs, canonical loop, deprecated doc tokens"),
        ("prompt_contracts", "validators/prompt_contracts.py", "TOML shape, runtime prompts, launch manifest gate"),
        ("skill_contracts", "validators/skill_contracts.py", "mandatory skill contract.json bindings"),
        ("skill_contract_hook", "validate-skill-contracts.py", "fast hook target for stage skill contract drift"),
        ("contracts", "validators/contracts.py", "routing/active_passes/feedback synthetic fixtures"),
        ("runtime_artifact", "validate-runtime-artifact.py", "actual stage output schema gate"),
        ("harness_gate", "harness_gate.py", "blocks next handoff when runtime validation fails"),
        ("harness_handoff", "harness_handoff.py", "caller wiring that must wrap every stage handoff"),
        ("runtime_gate_smoke", "validate-runtime-gate-smoke.py", "positive/negative runtime and CLI fixtures"),
        ("entrypoint", "validate-agent-architecture.py", "required inventory, line limit, final PASS/FAIL"),
    ]
    for check, source, contract in rows:
        print(f"- check={check} | source={source} | contract={contract}")


def resolve_codex_home() -> tuple[Path, str]:
    # Process env wins; script/profile fallbacks keep sandbox runs deterministic.
    script_fallback = Path(__file__).resolve().parents[1]
    profile_fallback = Path(os.environ.get("USERPROFILE", "")) / ".codex" if os.environ.get("USERPROFILE") else None
    candidates = [
        ("Process", os.environ.get("CODEX_HOME")),
        ("ScriptFallback", str(script_fallback)),
        ("ProfileFallback", str(profile_fallback) if profile_fallback else None),
    ]
    for source, value in candidates:
        if value and Path(value).is_dir():
            return Path(value).resolve(), source
    raise SystemExit("Cannot resolve CODEX_HOME from process, script fallback, or profile fallback.")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate global Codex agent architecture files.")
    parser.add_argument("--explain", "-Explain", action="store_true", help="show validator-to-agent mapping only")
    args = parser.parse_args(argv)
    if args.explain:
        show_explain()
        return 0
    root, source = resolve_codex_home()
    return Validator(root, source).run()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
