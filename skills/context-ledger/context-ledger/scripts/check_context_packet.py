#!/usr/bin/env python3
"""Preflight a context_packet before task planning."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    text = sys.stdin.read() if not argv or argv[0] == "-" else Path(argv[0]).read_text(encoding="utf-8-sig")
    payload = json.loads(text)
    packet = payload.get("context_packet", payload)
    required = ("context_packet_version", "context_revision", "context_authority_ref", "approved_facts", "role_pass_readiness")
    errors = [f"{field} is required" for field in required if field not in packet]
    if packet.get("next_owner") not in (None, "task-planner"):
        errors.append("next_owner must be task-planner")
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
