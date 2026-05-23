#!/usr/bin/env python3
"""Validate the concise global Codex orchestration architecture."""
from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
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

CANONICAL_FLOW = (
    "orchestrator -> context-ledger -> task-planner -> worker -> "
    "review-distributor -> review -> feedbackgate"
)

REQUIRED_DOCS = (
    "AGENTS.md",
    "agent-architecture/AGENT-ARCHITECTURE.md",
    "agent-architecture/AGENT-ARCHITECTURE-MAPPER.md",
    "agent-architecture/AGENTS.local-template.md",
    "agent-architecture/09-runtime-orchestration-steps.md",
)


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def resolve_root() -> tuple[Path, str]:
    script_root = Path(__file__).resolve().parents[1]
    profile_root = Path(os.environ.get("USERPROFILE", "")) / ".codex" if os.environ.get("USERPROFILE") else None
    for source, value in (
        ("Process", os.environ.get("CODEX_HOME")),
        ("ScriptFallback", str(script_root)),
        ("ProfileFallback", str(profile_root) if profile_root else None),
    ):
        if value and Path(value).is_dir():
            return Path(value).resolve(), source
    raise SystemExit("Cannot resolve CODEX_HOME from process, script fallback, or profile fallback.")


class Validator:
    def __init__(self, root: Path, source: str) -> None:
        self.root = root
        self.source = source
        self.arch_dir = root / "agent-architecture"
        self.failures: list[str] = []
        self.checks = 0

    def log(self, message: str) -> None:
        print(f"[architecture validation] {message}")

    def check(self, name: str, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(f"{name} - {message}")
            print(f"[architecture validation][FAIL] {name} - {message}")

    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def validate_docs(self) -> None:
        self.log("document flow check")
        joined_parts = []
        for rel in REQUIRED_DOCS:
            path = self.root / rel
            self.check("required_doc_exists", path.is_file(), f"missing {path}")
            if path.is_file():
                text = self.read(path)
                joined_parts.append(text)
                self.check("line_limit", len(text.splitlines()) <= 220, f"{path} is too long")
        joined = "\n".join(joined_parts)
        self.check("canonical_flow_documented", CANONICAL_FLOW in joined, "canonical flow missing")
        for skill in MANDATORY_SKILLS:
            self.check("mandatory_skill_documented", f"${skill}" in joined, f"${skill} missing from docs")
        for marker in (
            "context_ledger_mcp_required=true",
            "feedback_gate_mandatory=true",
            "spawn_agent",
            "wait_agent",
            "specialist workers",
            "specialist reviews",
        ):
            self.check("required_marker_documented", marker in joined, f"{marker} missing from docs")

    def validate_skills(self) -> None:
        self.log("mandatory skill and script check")
        for skill in MANDATORY_SKILLS:
            skill_dir = self.root / "skills" / skill
            skill_md = skill_dir / "SKILL.md"
            contract_path = skill_dir / "contract.json"
            scripts_dir = skill_dir / "scripts"
            self.check("skill_md_exists", skill_md.is_file(), f"missing {skill_md}")
            self.check("skill_contract_exists", contract_path.is_file(), f"missing {contract_path}")
            self.check("skill_scripts_dir_exists", scripts_dir.is_dir(), f"missing {scripts_dir}")
            if contract_path.is_file():
                try:
                    contract = json.loads(self.read(contract_path))
                except json.JSONDecodeError as exc:
                    self.check("skill_contract_json", False, f"{contract_path}: {exc}")
                    continue
                self.check("skill_contract_name", contract.get("skill_name") == skill, f"{contract_path} skill_name mismatch")
                self.check("skill_contract_activation", contract.get("activation_ref") == f"${skill}", f"{contract_path} activation_ref mismatch")
                self.check("skill_contract_mandatory", contract.get("mandatory_for_architecture_required") is True, f"{contract_path} must be mandatory")
                self.check("skill_contract_mode", contract.get("stage_execution_mode") == "main_agent_role_pass", f"{contract_path} must be main_agent_role_pass")
            for script in scripts_dir.glob("*.py"):
                try:
                    py_compile.compile(str(script), doraise=True)
                    compiled = True
                    detail = ""
                except py_compile.PyCompileError as exc:
                    compiled = False
                    detail = str(exc)
                self.check("skill_script_compiles", compiled, f"{script} compile failed: {detail}")

    def validate_global_scripts(self) -> None:
        self.log("global script boundary check")
        for name in (
            "validate-agent-architecture.py",
            "validate-skill-contracts.py",
            "validate-runtime-artifact.py",
            "harness_gate.py",
            "harness_handoff.py",
            "validate-session-runtime.py",
            "validate-runtime-gate-smoke.py",
        ):
            path = self.arch_dir / name
            self.check("global_script_exists", path.is_file(), f"missing {path}")
            if path.is_file() and path.suffix == ".py":
                try:
                    py_compile.compile(str(path), doraise=True)
                    compiled = True
                    detail = ""
                except py_compile.PyCompileError as exc:
                    compiled = False
                    detail = str(exc)
                self.check("global_script_compiles", compiled, f"{path} compile failed: {detail}")
        self.check("no_stage_scripts_in_arch_root", not list(self.arch_dir.glob("check_*_stage.py")), "stage-specific scripts belong under skills/<name>/scripts")

    def validate_skill_contract_hook(self) -> None:
        self.log("skill contract hook check")
        hook = self.arch_dir / "validate-skill-contracts.py"
        completed = subprocess.run([sys.executable, str(hook)], cwd=str(self.root), capture_output=True, text=True, encoding="utf-8")
        self.check("skill_contract_hook_passes", completed.returncode == 0, f"stdout={completed.stdout} stderr={completed.stderr}")

    def run(self) -> int:
        self.log(f"CODEX_HOME resolved from {self.source}: {self.root}")
        self.validate_docs()
        self.validate_skills()
        self.validate_global_scripts()
        self.validate_skill_contract_hook()
        if self.failures:
            self.log(f"failure count: {len(self.failures)}")
            return 1
        self.log(f"PASS: concise architecture invariants passed (checks={self.checks})")
        return 0


def main() -> int:
    configure_utf8_stdio()
    root, source = resolve_root()
    return Validator(root, source).run()


if __name__ == "__main__":
    raise SystemExit(main())
