#!/usr/bin/env python3
"""Preflight review_distribution output before reviewer materialization."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    text = sys.stdin.read() if not argv or argv[0] == "-" else Path(argv[0]).read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    plan = payload.get("review_plan", payload.get("review_launch_manifest", payload))
    errors: list[str] = []
    for field in ("context_packet_version", "required_review_axes", "fanout_budget"):
        if field not in plan:
            errors.append(f"{field} is required")
    if not isinstance(plan.get("required_review_axes"), list) or not plan.get("required_review_axes"):
        errors.append("required_review_axes must be a non-empty list")
    if payload.get("next_owner") not in (None, "review"):
        errors.append("next_owner must be review")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
