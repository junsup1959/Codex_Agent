#!/usr/bin/env python3
"""Preflight an orchestration_request before context-ledger sync."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    text = sys.stdin.read() if not argv or argv[0] == "-" else Path(argv[0]).read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    req = payload.get("orchestration_request", payload)
    required = ("run_id", "loop_id", "user_goal", "allowed_scope", "success_criteria")
    errors = [f"{field} is required" for field in required if not req.get(field)]
    if payload.get("next_owner") not in (None, "context-ledger"):
        errors.append("next_owner must be context-ledger")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
