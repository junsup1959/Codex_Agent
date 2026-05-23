#!/usr/bin/env python3
"""Preflight a worker wave packet before specialist worker spawn."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_payload(path: str | None) -> dict:
    text = sys.stdin.read() if not path or path == "-" else Path(path).read_text(encoding="utf-8-sig")
    return json.loads(text)


def main(argv: list[str]) -> int:
    payload = load_payload(argv[0] if argv else None)
    plan = payload.get("execution_plan", payload)
    errors: list[str] = []
    lanes = plan.get("lanes")
    if not isinstance(lanes, list) or not lanes:
        errors.append("execution_plan.lanes must be a non-empty list")
    if not isinstance(plan.get("fanout_budget"), dict):
        errors.append("execution_plan.fanout_budget is required")
    if not isinstance(plan.get("context_packet_version"), str):
        errors.append("execution_plan.context_packet_version is required")
    if isinstance(lanes, list):
        for index, lane in enumerate(lanes):
            if not isinstance(lane, dict):
                errors.append(f"lanes[{index}] must be an object")
                continue
            for field in ("owned_scope", "expected_artifact", "validation_prompt"):
                if not lane.get(field):
                    errors.append(f"lanes[{index}].{field} is required")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
