#!/usr/bin/env python3
"""Preflight an execution_plan before worker materialization."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    text = sys.stdin.read() if not argv or argv[0] == "-" else Path(argv[0]).read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    plan = payload.get("execution_plan", payload)
    errors: list[str] = []
    for field in ("wave_id", "context_packet_version", "lanes", "fanout_budget"):
        if field not in plan:
            errors.append(f"{field} is required")
    if not isinstance(plan.get("lanes"), list) or not plan.get("lanes"):
        errors.append("lanes must be a non-empty list")
    if payload.get("next_owner") not in (None, "worker"):
        errors.append("next_owner must be worker")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
