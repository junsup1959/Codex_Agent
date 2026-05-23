#!/usr/bin/env python3
"""Preflight a review wave packet before specialist reviewer spawn."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_payload(path: str | None) -> dict:
    text = sys.stdin.read() if not path or path == "-" else Path(path).read_text(encoding="utf-8-sig")
    return json.loads(text)


def main(argv: list[str]) -> int:
    payload = load_payload(argv[0] if argv else None)
    plan = payload.get("review_plan", payload.get("launch_manifest", payload))
    errors: list[str] = []
    axes = plan.get("required_review_axes", plan.get("review_axes"))
    if not isinstance(axes, list) or not axes:
        errors.append("review axes must be a non-empty list")
    if not isinstance(plan.get("fanout_budget"), dict):
        errors.append("fanout_budget is required")
    if not isinstance(plan.get("context_packet_version"), str):
        errors.append("context_packet_version is required")
    lanes = plan.get("children", plan.get("review_lanes", []))
    if not isinstance(lanes, list):
        errors.append("review lanes must be a list")
    else:
        for index, lane in enumerate(lanes):
            if not isinstance(lane, dict):
                errors.append(f"review_lanes[{index}] must be an object")
                continue
            if lane.get("lane_type") not in (None, "review"):
                errors.append(f"review_lanes[{index}].lane_type must be review")
            if not lane.get("validation_prompt"):
                errors.append(f"review_lanes[{index}].validation_prompt is required")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
