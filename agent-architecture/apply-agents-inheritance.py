#!/usr/bin/env python3
# 한국어 주석: /init이 만든 repo-local AGENTS.md에 전역 architecture 상속과 검증 hook을 삽입한다.
from __future__ import annotations

import argparse
from pathlib import Path

INHERITANCE_BLOCK = """# Global Architecture Inheritance

This project inherits the global Codex architecture by reference:

- `${CODEX_HOME}/AGENTS.md`
- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md`
- `${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md`

Do not copy the global architecture body into this project file. Keep project-specific rules below.

## Validation Hook

If this area changes architecture docs, runtime prompts, validator logic, or detects architecture drift, emit `architecture_validation_required=true` and run `${CODEX_HOME}/agent-architecture/validate-agent-architecture.py` before final approval.

---
"""

REQUIRED_MARKERS = (
    "${CODEX_HOME}/AGENTS.md",
    "${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE.md",
    "${CODEX_HOME}/agent-architecture/AGENT-ARCHITECTURE-MAPPER.md",
    "architecture_validation_required=true",
    "${CODEX_HOME}/agent-architecture/validate-agent-architecture.py",
)
INHERITANCE_TITLE = "# Global Architecture Inheritance"


def has_complete_inheritance(text: str) -> bool:
    return all(marker in text.lstrip("\ufeff") for marker in REQUIRED_MARKERS)


def remove_existing_inheritance_block(text: str) -> str:
    # 한국어 주석: 기존 상속 블록이 불완전하면 첫 구분선까지 제거하고 최신 블록으로 교체한다.
    stripped = text.lstrip("\ufeff").lstrip()
    if not stripped.startswith(INHERITANCE_TITLE):
        return stripped
    marker = "\n---\n"
    index = stripped.find(marker)
    if index == -1:
        return stripped
    return stripped[index + len(marker):].lstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply global Codex architecture inheritance to a repo AGENTS.md")
    parser.add_argument("path", nargs="?", default="AGENTS.md", help="repo-local AGENTS.md path")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if target.exists():
        text = target.read_text(encoding="utf-8-sig")
    else:
        text = "# Repository Guidelines\n\n"

    if has_complete_inheritance(text):
        print(f"already_inherits\t{target}")
        return 0

    body = remove_existing_inheritance_block(text)
    if body.startswith("# "):
        updated = INHERITANCE_BLOCK + "\n" + body
    else:
        updated = INHERITANCE_BLOCK + "\n# Repository Guidelines\n\n" + body

    target.write_text(updated, encoding="utf-8", newline="\n")
    status = "inheritance_repaired" if INHERITANCE_TITLE in text else "inheritance_applied"
    print(f"{status}\t{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
