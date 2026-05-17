#!/usr/bin/env python3
"""Hook-friendly validator for global Codex stage skill contracts."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from validators.skill_contracts import check_skill_contracts


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


configure_utf8_stdio()


class ContractValidator:
    def __init__(self, root: Path, source: str) -> None:
        self.root = root
        self.source = source
        self.arch_dir = root / "agent-architecture"
        self.failures: list[str] = []
        self.checks_run = 0

    def log(self, message: str) -> None:
        print(f"[skill contract validation] {message}")

    def fail(self, message: str) -> None:
        self.failures.append(message)
        print(f"[skill contract validation][FAIL] {message}")

    def assert_condition(self, name: str, condition: bool, failure_message: str) -> None:
        self.checks_run += 1
        if not condition:
            self.fail(f"{name} - {failure_message}")

    def assert_file_exists(self, path: Path) -> None:
        self.assert_condition("file_exists", path.is_file(), f"required file missing: {path}")

    def assert_contains(self, name: str, haystack: str, needle: str) -> None:
        self.assert_condition(name, needle in haystack, f"required text missing: {needle}")

    def run(self) -> int:
        self.log(f"CODEX_HOME resolved from {self.source}: {self.root}")
        check_skill_contracts(self)
        if self.failures:
            self.log(f"failure count: {len(self.failures)}")
            return 1
        self.log(f"PASS: stage skill contracts valid (checks={self.checks_run})")
        return 0


def resolve_codex_home() -> tuple[Path, str]:
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
    parser = argparse.ArgumentParser(description="Validate global Codex stage skill contract.json files.")
    parser.parse_args(argv)
    root, source = resolve_codex_home()
    return ContractValidator(root, source).run()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
