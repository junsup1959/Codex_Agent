#!/usr/bin/env python3
"""Preflight a feedbackgate judgment envelope."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    text = sys.stdin.read() if not argv or argv[0] == "-" else Path(argv[0]).read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    judgment = payload.get("judgment_envelope", payload)
    errors: list[str] = []
    for field in ("decision", "feedback_required", "feedback_target", "feedback_gate_evidence", "review_input_refs"):
        if field not in judgment:
            errors.append(f"{field} is required")
    if judgment.get("feedback_required") is True and judgment.get("next_owner") != "orchestrator":
        errors.append("feedback_required=true requires next_owner=orchestrator")
    if judgment.get("feedback_required") is False and judgment.get("feedback_target") != "none":
        errors.append("final output requires feedback_target=none")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
