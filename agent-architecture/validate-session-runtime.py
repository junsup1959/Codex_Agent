#!/usr/bin/env python3
"""Replay a Codex session JSONL and check orchestration runtime evidence.

This validator is intentionally session-log oriented. The artifact validators
can reject bad JSON contracts, but they cannot prove the parent actually called
or avoided `spawn_agent` in the thread. This script closes that gap by reading
Codex session JSONL and checking resident context, main-agent role pass, fanout,
spawn/wait, and physical override evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from validators.constants import REVIEW_LANE_ALLOWED_ROLES, ROLE_ALIAS_MAP


CONTROL_STAGE_ROLES = {
    "context-manager",
    "task-planner",
    "worker-router",
    "aggregator",
    "review-router",
    "meta-judge",
}

RESIDENT_CONTROL_STAGE_ROLES: set[str] = set()

MAIN_AGENT_ROLE_PASS_CONTROL_ROLES = CONTROL_STAGE_ROLES - RESIDENT_CONTROL_STAGE_ROLES

PHYSICAL_CONTROL_OVERRIDE_MARKERS = (
    "stage_execution_mode=physical",
    "physical_override_reason",
)

MAX_CONTEXT_MANAGER_SPAWNS = 0
MAX_PHYSICAL_SPAWN_BURST = 4
MAX_SAME_ROLE_SPAWN_BURST = 1

DIRECT_SPECIALIST_ALLOWLIST = {
    "context-manager",
    "task-planner",
    "worker-router",
    "aggregator",
    "review-router",
    "meta-judge",
}

REQUIRED_RESIDENT_PHYSICAL_ROLES: set[str] = set()

REVIEW_SESSION_ROLES = set(REVIEW_LANE_ALLOWED_ROLES) | {
    alias for alias in ROLE_ALIAS_MAP if alias.endswith("reviewer")
}

ARCHITECTURE_REQUEST_MARKERS = (
    "오케스트레이션 하네스",
    "오케스트레이션 하네스구조",
    "아키텍처",
    "에이전트 구조",
    "하네스",
    "agent architecture",
    "agent structure",
    "orchestration harness",
    "Feedback Trigger Gate",
)

NONTRIVIAL_TRIGGER_MARKERS = (
    "구현",
    "수정",
    "보강",
    "검증",
    "분석",
    "조사",
    "리뷰",
    "감사",
    "비교",
    "크롤링",
    "다운로드",
    "테스트",
    "파서",
    "parser",
    "implement",
    "fix",
    "review",
    "audit",
    "analyze",
    "research",
    "compare",
    "crawl",
    "download",
    "test",
)

FINAL_CLAIM_MARKERS = (
    "하네스 흐름까지 끝까지",
    "완료했습니다",
    "FINAL_OK",
    "final output",
)

PHYSICAL_BUNDLE_MARKERS = (
    "stage_passes",
    "review_results",
    "active_passes",
    "spawn_receipt_ref",
    "wait_registered_at",
)

SPAWN_THREAD_LIMIT_MARKERS = (
    "agent thread limit reached",
    "thread limit reached",
    "thread count",
    "thread quota",
    "too many threads",
    "too many agents",
    "concurrent agent limit",
    "concurrency limit",
    "maximum active",
    "maximum number of threads",
)

SPAWN_INVALID_CONTEXT_MARKERS = (
    "full-history forked agents inherit",
    "omit agent_type",
    "spawn without a full-history fork",
)

LOCAL_SIMULATION_MARKERS = (
    "로컬로 적용",
    "로컬로 진행",
    "로컬 감사 절차",
    "동일한 단계 산출물",
    "same stages locally",
    "simulate",
)

LOCAL_SIMULATION_NEGATION_MARKERS = (
    "do not simulate",
    "must not be simulated",
    "cannot be simulated",
    "not simulated",
    "instead of claiming the architecture was followed",
)


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def read_session(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            events.append({"line": line_number, "decode_error": True, "raw": line[:300]})
            continue
        item["_line"] = line_number
        events.append(item)
    return events


def message_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict):
            parts.append(str(item.get("text") or item.get("input_text") or ""))
    return "\n".join(parts)


def parse_tool_args(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, str):
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}
    return parsed if isinstance(parsed, dict) else {}


def compact_text(raw: Any, limit: int = 500) -> str:
    if isinstance(raw, str):
        text = raw
    else:
        try:
            text = json.dumps(raw, ensure_ascii=False)
        except TypeError:
            text = str(raw)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def classify_spawn_failure(text: str) -> str:
    lowered = text.lower()
    if has_any(lowered, SPAWN_THREAD_LIMIT_MARKERS):
        return "thread_limit"
    if has_any(lowered, SPAWN_INVALID_CONTEXT_MARKERS):
        return "invalid_spawn_context"
    if "collab spawn failed" in lowered or "spawn failed" in lowered:
        return "spawn_failed"
    if "not_found" in lowered or "not found" in lowered:
        return "spawn_not_found"
    return "unknown_spawn_failure"


def failed_spawn_summary(failed_spawns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "line": spawn.get("line"),
            "failure_line": spawn.get("failure_line"),
            "agent_type": spawn.get("agent_type"),
            "fork_context": spawn.get("fork_context"),
            "failure_category": spawn.get("failure_category"),
            "failure_output": spawn.get("failure_output"),
        }
        for spawn in failed_spawns
    ]


def extract_session(events: list[dict[str, Any]]) -> dict[str, Any]:
    spawns: list[dict[str, Any]] = []
    waits: list[dict[str, Any]] = []
    wait_call_targets: dict[str, list[str]] = {}
    materialized_spawns: list[dict[str, Any]] = []
    close_results: list[dict[str, Any]] = []
    wait_results: list[dict[str, Any]] = []
    successful_spawn_call_ids: set[str] = set()
    failed_spawn_call_ids: set[str] = set()
    spawn_failure_details: dict[str, dict[str, Any]] = {}
    tool_calls: dict[str, dict[str, Any]] = {}
    ended_tool_call_ids: set[str] = set()
    mcp_tool_error_lines: list[int] = []
    messages: list[dict[str, Any]] = []
    notifications: list[dict[str, Any]] = []

    for item in events:
        payload = item.get("payload")
        if not isinstance(payload, dict):
            continue
        if item.get("type") == "response_item" and payload.get("type") in {"function_call", "tool_search_call", "custom_tool_call"}:
            call_id = payload.get("call_id")
            if isinstance(call_id, str) and call_id:
                tool_calls[call_id] = {
                    "line": item["_line"],
                    "type": payload.get("type"),
                    "name": payload.get("name"),
                    "namespace": payload.get("namespace"),
                }
                if payload.get("type") == "custom_tool_call" and payload.get("status") == "completed":
                    ended_tool_call_ids.add(call_id)
        if item.get("type") == "response_item" and payload.get("type") in {"function_call_output", "tool_search_output"}:
            call_id = payload.get("call_id")
            if isinstance(call_id, str) and call_id:
                ended_tool_call_ids.add(call_id)
        if item.get("type") == "response_item" and payload.get("type") == "function_call":
            name = payload.get("name")
            args = parse_tool_args(payload.get("arguments"))
            if name == "spawn_agent":
                spawns.append(
                    {
                        "line": item["_line"],
                        "call_id": payload.get("call_id"),
                        "agent_type": args.get("agent_type") or args.get("agent_role"),
                        "fork_context": args.get("fork_context"),
                        "message": args.get("message", ""),
                    }
                )
            if name == "wait_agent":
                targets = args.get("targets", [])
                call_id = payload.get("call_id")
                waits.append({"line": item["_line"], "call_id": call_id, "targets": targets})
                if isinstance(call_id, str):
                    wait_call_targets[call_id] = [target for target in targets if isinstance(target, str)]
        if item.get("type") == "response_item" and payload.get("type") == "function_call_output":
            call_id = payload.get("call_id")
            output = payload.get("output")
            parsed_output: Any = None
            if isinstance(output, str):
                try:
                    parsed_output = json.loads(output)
                except json.JSONDecodeError:
                    parsed_output = None
            is_spawn_call = isinstance(call_id, str) and tool_calls.get(call_id, {}).get("name") == "spawn_agent"
            if isinstance(parsed_output, dict) and isinstance(parsed_output.get("agent_id"), str) and parsed_output["agent_id"]:
                successful_spawn_call_ids.add(str(call_id))
            elif isinstance(call_id, str) and call_id in wait_call_targets and isinstance(parsed_output, dict):
                wait_results.append(
                    {
                        "line": item["_line"],
                        "call_id": call_id,
                        "targets": wait_call_targets.get(call_id, []),
                        "statuses": normalize_wait_statuses(parsed_output.get("status", {})),
                        "timed_out": parsed_output.get("timed_out") is True,
                    }
                )
            elif isinstance(call_id, str) and is_spawn_call:
                failed_spawn_call_ids.add(call_id)
                output_text = compact_text(output)
                spawn_failure_details[call_id] = {
                    "line": item["_line"],
                    "category": classify_spawn_failure(output_text),
                    "output": output_text,
                }
        if item.get("type") == "response_item" and payload.get("type") == "message":
            text = message_text(payload)
            messages.append({"line": item["_line"], "role": payload.get("role"), "phase": payload.get("phase"), "text": text})
            if "<subagent_notification>" in text:
                notifications.append({"line": item["_line"], "text": text})
        if item.get("type") == "event_msg" and payload.get("type") == "collab_agent_spawn_end":
            call_id = payload.get("call_id")
            if isinstance(call_id, str) and call_id:
                ended_tool_call_ids.add(call_id)
            thread_id = payload.get("new_thread_id")
            if isinstance(thread_id, str) and thread_id:
                successful_spawn_call_ids.add(str(call_id))
                materialized_spawns.append(
                    {
                        "line": item["_line"],
                        "call_id": call_id,
                        "thread_id": thread_id,
                        "role": payload.get("new_agent_role"),
                        "nickname": payload.get("new_agent_nickname"),
                    }
                )
            elif isinstance(call_id, str):
                failed_spawn_call_ids.add(call_id)
                output_text = compact_text(payload)
                spawn_failure_details[call_id] = {
                    "line": item["_line"],
                    "category": classify_spawn_failure(output_text),
                    "output": output_text,
                }
            notifications.append({"line": item["_line"], "text": json.dumps(payload, ensure_ascii=False)})
        if item.get("type") == "event_msg" and payload.get("type") == "collab_waiting_end":
            call_id = payload.get("call_id")
            if isinstance(call_id, str) and call_id:
                ended_tool_call_ids.add(call_id)
            raw_statuses = payload.get("agent_statuses", payload.get("statuses", []))
            wait_results.append(
                {
                    "line": item["_line"],
                    "call_id": call_id,
                    "targets": wait_call_targets.get(str(call_id), []) if isinstance(call_id, str) else [],
                    "statuses": normalize_wait_statuses(raw_statuses),
                    "timed_out": None,
                }
            )
            notifications.append({"line": item["_line"], "text": json.dumps(payload, ensure_ascii=False)})
        if item.get("type") == "event_msg" and payload.get("type") == "collab_close_end":
            call_id = payload.get("call_id")
            if isinstance(call_id, str) and call_id:
                ended_tool_call_ids.add(call_id)
            close_results.append(
                {
                    "line": item["_line"],
                    "call_id": call_id,
                    "thread_id": payload.get("receiver_thread_id"),
                    "role": payload.get("receiver_agent_role"),
                    "status": payload.get("status"),
                }
            )
            notifications.append({"line": item["_line"], "text": json.dumps(payload, ensure_ascii=False)})
        if item.get("type") == "event_msg" and payload.get("type") in {"exec_command_end", "mcp_tool_call_end", "patch_apply_end"}:
            call_id = payload.get("call_id")
            if isinstance(call_id, str) and call_id:
                ended_tool_call_ids.add(call_id)
            if payload.get("type") == "mcp_tool_call_end" and mcp_result_contains_error(payload.get("result")):
                mcp_tool_error_lines.append(int(item["_line"]))

    successful_spawns = [spawn for spawn in spawns if isinstance(spawn.get("call_id"), str) and spawn["call_id"] in successful_spawn_call_ids]
    failed_spawns = []
    for spawn in spawns:
        call_id = spawn.get("call_id")
        if not isinstance(call_id, str) or call_id not in failed_spawn_call_ids or call_id in successful_spawn_call_ids:
            continue
        details = spawn_failure_details.get(call_id, {})
        failed_spawns.append(
            {
                **spawn,
                "failure_line": details.get("line"),
                "failure_category": details.get("category", "unknown_spawn_failure"),
                "failure_output": details.get("output", ""),
            }
        )

    return {
        "spawns": successful_spawns,
        "raw_spawns": spawns,
        "failed_spawns": failed_spawns,
        "waits": waits,
        "materialized_spawns": materialized_spawns,
        "close_results": close_results,
        "wait_results": wait_results,
        "tool_calls": tool_calls,
        "ended_tool_call_ids": ended_tool_call_ids,
        "mcp_tool_error_lines": mcp_tool_error_lines,
        "messages": messages,
        "notifications": notifications,
    }


def mcp_result_contains_error(result: Any) -> bool:
    if result is None:
        return False
    try:
        text = json.dumps(result, ensure_ascii=False)
    except TypeError:
        text = str(result)
    lowered = text.lower()
    return '"error"' in lowered or "analysis failed" in lowered or "initialize: eof" in lowered


def has_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def normalize_wait_statuses(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [value for value in raw.values() if value]
    return []


def local_simulation_lines(messages: list[dict[str, Any]]) -> list[int]:
    lines: list[int] = []
    for item in messages:
        if item.get("role") != "assistant":
            continue
        text = str(item.get("text") or "")
        lowered = text.lower()
        marker_hits = [marker for marker in LOCAL_SIMULATION_MARKERS if marker.lower() in lowered]
        if not marker_hits:
            continue
        if has_any(lowered, LOCAL_SIMULATION_NEGATION_MARKERS):
            continue
        if marker_hits == ["simulate"] and not has_any(
            lowered,
            (
                "same stages locally",
                "simulate required",
                "simulating required",
                "simulated stage",
                "simulate control",
                "simulate the architecture",
            ),
        ):
            continue
        lines.append(int(item["line"]))
    return lines


def architecture_triggered(messages: list[dict[str, Any]]) -> bool:
    user_text = "\n".join(item["text"] for item in messages if item.get("role") == "user")
    assistant_text = "\n".join(item["text"] for item in messages if item.get("role") == "assistant")
    if has_any(user_text, ARCHITECTURE_REQUEST_MARKERS):
        return True
    # 한국어 유지보수 주석: architecture를 명시하지 않아도 비단순 구현/검증/조사 요청이면
    # 실행 전에 architecture_required=true로 승격해야 직접 specialist 호출을 막을 수 있다.
    if has_any(user_text, NONTRIVIAL_TRIGGER_MARKERS):
        return True
    return "architecture_required=true" in assistant_text


def role_counts(spawns: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for spawn in spawns:
        role = str(spawn.get("agent_type") or "")
        counts[role] = counts.get(role, 0) + 1
    return counts


def first_line(items: list[dict[str, Any]], predicate) -> int | None:
    for item in items:
        if predicate(item):
            return int(item["line"])
    return None


def physical_control_override_missing(spawn: dict[str, Any]) -> bool:
    prompt = str(spawn.get("message") or "")
    return not all(marker in prompt for marker in PHYSICAL_CONTROL_OVERRIDE_MARKERS)


def spawn_burst_violations(raw_spawns: list[dict[str, Any]], waits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[tuple[int, str, dict[str, Any]]] = []
    for spawn in raw_spawns:
        if isinstance(spawn.get("line"), int):
            events.append((int(spawn["line"]), "spawn", spawn))
    for wait in waits:
        if isinstance(wait.get("line"), int):
            events.append((int(wait["line"]), "wait", wait))
    events.sort(key=lambda item: (item[0], 0 if item[1] == "spawn" else 1))

    violations: list[dict[str, Any]] = []
    burst: list[dict[str, Any]] = []

    def flush(until_line: int | None) -> None:
        nonlocal burst
        if not burst:
            return
        role_counts = role_counts_from_raw(burst)
        duplicate_roles = {
            role: count
            for role, count in role_counts.items()
            if role and count > MAX_SAME_ROLE_SPAWN_BURST
        }
        if len(burst) > MAX_PHYSICAL_SPAWN_BURST or duplicate_roles:
            violations.append(
                {
                    "start_line": burst[0]["line"],
                    "end_line": until_line if until_line is not None else burst[-1]["line"],
                    "spawn_count": len(burst),
                    "roles": role_counts,
                    "duplicate_roles": duplicate_roles,
                }
            )
        burst = []

    for line, kind, item in events:
        if kind == "spawn":
            burst.append(item)
        else:
            flush(line)
    flush(None)
    return violations


def role_counts_from_raw(spawns: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for spawn in spawns:
        role = str(spawn.get("agent_type") or "default/unspecified")
        counts[role] = counts.get(role, 0) + 1
    return counts


def validate_session(session: dict[str, Any]) -> dict[str, Any]:
    spawns = session["spawns"]
    failed_spawns = session.get("failed_spawns", [])
    waits = session["waits"]
    materialized_spawns = session["materialized_spawns"]
    close_results = session.get("close_results", [])
    wait_results = session["wait_results"]
    tool_calls = session.get("tool_calls", {})
    ended_tool_call_ids = session.get("ended_tool_call_ids", set())
    mcp_tool_error_lines = session.get("mcp_tool_error_lines", [])
    messages = session["messages"]
    notifications = session["notifications"]
    counts = role_counts(spawns)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    thread_limit_failed_spawns = [
        spawn for spawn in failed_spawns if spawn.get("failure_category") == "thread_limit"
    ]
    other_failed_spawns = [
        spawn for spawn in failed_spawns if spawn.get("failure_category") != "thread_limit"
    ]

    invalid_fork_spawn_lines = [
        spawn.get("line")
        for spawn in session.get("raw_spawns", [])
        if spawn.get("fork_context") is True and spawn.get("agent_type")
    ]
    if invalid_fork_spawn_lines:
        errors.append(
            {
                "code": "session.invalid_fork_agent_type_spawn",
                "lines": invalid_fork_spawn_lines,
                "message": "spawn_agent cannot combine fork_context=true with an explicit agent_type; dedicated stage owners need scoped packets or fork without agent_type.",
            }
        )

    all_text = "\n".join(item["text"] for item in messages + notifications)
    architecture_requested = architecture_triggered(messages)
    final_claimed = any(
        item["role"] == "assistant"
        and item.get("phase") == "final_answer"
        and has_any(item["text"], FINAL_CLAIM_MARKERS)
        for item in messages
    )
    local_simulation_evidence_lines = local_simulation_lines(messages)
    compact_text = re.sub(r"\s+", "", all_text)
    feedback_required_seen = "FEEDBACK_REQUIRED" in all_text or '"feedback_required":true' in compact_text
    worker_router_evidence_seen = counts.get("worker-router", 0) > 0 or (
        "worker-router" in all_text and "launch_manifest" in all_text
    )
    review_router_evidence_seen = counts.get("review-router", 0) > 0 or (
        "review-router" in all_text and "launch_manifest" in all_text
    )

    if not architecture_requested and not final_claimed:
        if failed_spawns:
            warnings.append(
                {
                    "code": "session.failed_spawn_observed",
                    "count": len(failed_spawns),
                    "failures": failed_spawn_summary(failed_spawns),
                    "message": "spawn_agent failures were observed, but no architecture/final claim triggered strict physical-chain validation.",
                }
            )
        warnings.append(
            {
                "code": "session.no_architecture_claim",
                "message": "No architecture/harness claim found; strict physical chain check skipped.",
            }
        )
        return result(errors, warnings, counts, spawns, waits)

    if thread_limit_failed_spawns:
        errors.append(
            {
                "code": "session.spawn_thread_limit_reached",
                "count": len(thread_limit_failed_spawns),
                "failures": failed_spawn_summary(thread_limit_failed_spawns),
                "message": "spawn_agent hit the agent thread limit; the affected lanes/stages were not materialized and aggregation/final judgment must fail closed until retried or explicitly classified.",
            }
        )
    if other_failed_spawns:
        errors.append(
            {
                "code": "session.spawn_failed",
                "count": len(other_failed_spawns),
                "failures": failed_spawn_summary(other_failed_spawns),
                "message": "spawn_agent failures are physical materialization failures; they cannot be counted as stage or lane execution evidence.",
            }
        )

    if local_simulation_evidence_lines:
        errors.append(
            {
                "code": "session.local_stage_simulation",
                "lines": local_simulation_evidence_lines,
                "message": "Architecture-claimed non-trivial work used local/simulated stage wording instead of validated main-agent role passes or physical override passes.",
            }
        )

    context_manager_count = counts.get("context-manager", 0)
    if context_manager_count:
        errors.append(
            {
                "code": "session.physical_context_manager_spawned",
                "count": context_manager_count,
                "max_allowed": 0,
                "message": "context-manager is now a main-agent role pass backed by codex-context-ledger MCP; do not spawn it as a physical resident agent.",
            }
        )

    context_manager_close_lines = [
        item.get("line")
        for item in close_results
        if item.get("role") == "context-manager"
    ]
    if context_manager_close_lines:
        errors.append(
            {
                "code": "session.physical_context_manager_closed",
                "lines": context_manager_close_lines,
                "message": "context-manager should not be physically spawned or closed; context state belongs to codex-context-ledger MCP.",
            }
        )

    control_stage_spawns_without_override = [
        {
            "line": spawn.get("line"),
            "agent_type": spawn.get("agent_type"),
        }
        for spawn in spawns
        if spawn.get("agent_type") in MAIN_AGENT_ROLE_PASS_CONTROL_ROLES
        and physical_control_override_missing(spawn)
    ]
    if control_stage_spawns_without_override:
        errors.append(
            {
                "code": "session.control_stage_physical_spawn_without_override",
                "spawns": control_stage_spawns_without_override[:50],
                "message": "task-planner, worker-router, aggregator, review-router, and meta-judge default to main-agent role passes; physical spawn requires stage_execution_mode=physical and physical_override_reason.",
            }
        )

    fanout_violations = spawn_burst_violations(session.get("raw_spawns", []), waits)
    if fanout_violations:
        errors.append(
            {
                "code": "session.physical_fanout_budget_exceeded",
                "max_spawn_burst": MAX_PHYSICAL_SPAWN_BURST,
                "max_same_role_spawn_burst": MAX_SAME_ROLE_SPAWN_BURST,
                "violations": fanout_violations[:20],
                "message": "Physical spawn bursts exceeded the conservative fanout budget; coalesce lanes or use main-agent role passes instead of over-spawning.",
            }
        )

    if len(materialized_spawns) < len(spawns):
        errors.append(
            {
                "code": "session.spawn_not_materialized",
                "message": f"spawn_agent calls={len(spawns)} but materialized child threads={len(materialized_spawns)}.",
            }
        )

    materialized_ids = {
        item.get("thread_id")
        for item in materialized_spawns
        if isinstance(item.get("thread_id"), str) and item.get("thread_id")
    }
    waited_ids = {
        target
        for wait in waits
        for target in wait.get("targets", [])
        if isinstance(target, str) and target
    }
    unawaited = sorted(materialized_ids - waited_ids)
    if unawaited:
        closed_ids = {
            item.get("thread_id")
            for item in close_results
            if isinstance(item.get("thread_id"), str) and item.get("thread_id")
        }
        close_only = sorted(set(unawaited) & closed_ids)
        errors.append(
            {
                "code": "session.spawned_child_not_waited",
                "targets": unawaited,
                "close_only_targets": close_only,
                "message": "Materialized child agents exist without matching wait_agent targets; close_agent cleanup is not wait evidence.",
            }
        )

    open_tool_calls = [
        {"call_id": call_id, **details}
        for call_id, details in tool_calls.items()
        if call_id not in ended_tool_call_ids
    ]
    if open_tool_calls:
        errors.append(
            {
                "code": "session.open_tool_calls",
                "calls": open_tool_calls[:20],
                "message": "Tool calls were started without a matching completion event before the session ended.",
            }
        )

    if mcp_tool_error_lines:
        warnings.append(
            {
                "code": "session.mcp_tool_error_not_success_evidence",
                "lines": mcp_tool_error_lines,
                "message": "MCP tool calls returned error-shaped results; these calls must be classified as blocked or waived, not counted as successful MCP evidence.",
            }
        )

    empty_wait_lines: list[int] = []
    timeout_wait_lines: list[int] = []
    for item in wait_results:
        if not isinstance(item.get("statuses"), list) or item["statuses"]:
            continue
        call_id = item.get("call_id")
        matching_call_result = any(
            other is not item
            and other.get("call_id") == call_id
            and (other.get("timed_out") is True or bool(other.get("statuses")))
            for other in wait_results
        )
        targets = {target for target in item.get("targets", []) if isinstance(target, str)}
        later_success_for_targets = bool(
            targets
            and any(
                other.get("line", 0) > item.get("line", 0)
                and bool(other.get("statuses"))
                and targets.intersection({target for target in other.get("targets", []) if isinstance(target, str)})
                for other in wait_results
            )
        )
        if item.get("timed_out") is True or matching_call_result or later_success_for_targets:
            timeout_wait_lines.append(int(item["line"]))
            continue
        empty_wait_lines.append(int(item["line"]))
    if empty_wait_lines:
        errors.append(
            {
                "code": "session.wait_returned_empty",
                "lines": empty_wait_lines,
                "message": "wait_agent returned no completed/timeout status; caller continued without a child result.",
            }
        )
    if timeout_wait_lines:
        warnings.append(
            {
                "code": "session.wait_timeout_retried",
                "lines": timeout_wait_lines,
                "message": "wait_agent timed out or returned an empty event result, but the child result was later observed or represented by the paired tool output.",
            }
        )

    direct_specialists = sorted(
        {
            str(spawn.get("agent_type"))
            for spawn in spawns
            if str(spawn.get("agent_type")) not in DIRECT_SPECIALIST_ALLOWLIST
        }
    )
    if counts.get("worker", 0):
        errors.append(
            {
                "code": "session.generic_worker_role_used",
                "count": counts.get("worker", 0),
                "message": "Architecture-required runs must route executable work to concrete specialist roles, not generic worker agents.",
            }
        )
    if direct_specialists and not worker_router_evidence_seen:
        errors.append(
            {
                "code": "session.direct_specialist_without_worker_router",
                "roles": direct_specialists,
                "message": "Specialist/explorer agents were spawned directly without worker-router launch_manifest evidence.",
            }
        )

    first_final = first_line(
        messages,
        lambda item: item.get("role") == "assistant"
        and item.get("phase") == "final_answer"
        and has_any(item.get("text", ""), FINAL_CLAIM_MARKERS),
    )
    first_spawn = first_line(spawns, lambda _item: True)
    if first_final is not None and (first_spawn is None or first_final < first_spawn):
        errors.append(
            {
                "code": "session.final_before_gate_chain",
                "line": first_final,
                "message": "Assistant claimed completion/final before any physical gate or review agent was spawned.",
            }
        )

    if feedback_required_seen:
        first_feedback = first_line(
            messages + notifications,
            lambda item: "FEEDBACK_REQUIRED" in item.get("text", "") or '"feedback_required":true' in re.sub(r"\s+", "", item.get("text", "")),
        )
        context_after_feedback = first_line(
            spawns,
            lambda item: item.get("agent_type") == "context-manager" and first_feedback is not None and item["line"] > first_feedback,
        )
        context_update_after_feedback = first_line(
            messages + notifications,
            lambda item: first_feedback is not None
            and int(item.get("line", 0)) > first_feedback
            and "context_authority_ref" in item.get("text", "")
            and "context_revision" in item.get("text", ""),
        )
        if context_after_feedback is None and context_update_after_feedback is None:
            errors.append(
                {
                    "code": "session.feedback_restart_skipped",
                    "message": "FEEDBACK_REQUIRED appeared, but no later MCP-backed context packet update was observed.",
                }
            )

    spawned_review_roles = sorted(
        {
            str(spawn.get("agent_type"))
            for spawn in spawns
            if str(spawn.get("agent_type")) in REVIEW_SESSION_ROLES
            and has_any(str(spawn.get("message") or ""), ("review", "reviewer", "review lane"))
        }
    )
    if spawned_review_roles and not review_router_evidence_seen:
        errors.append(
            {
                "code": "session.review_without_review_router",
                "roles": spawned_review_roles,
                "message": "Reviewer or review-support specialist was spawned directly without review-router launch_manifest evidence.",
            }
        )

    aggregator_spawns = [spawn for spawn in spawns if spawn.get("agent_type") == "aggregator"]
    for spawn in aggregator_spawns:
        prompt = str(spawn.get("message") or "")
        if "handoff_result" not in prompt or "active_passes" not in prompt:
            errors.append(
                {
                    "code": "session.aggregator_prose_only",
                    "line": spawn["line"],
                    "message": "Aggregator prompt did not include handoff_result/active_passes evidence; aggregation was prose-shaped.",
                }
            )

    router_completion_statuses = [
        status
        for result in wait_results
        for status in result.get("statuses", [])
        if isinstance(status, dict) and status.get("agent_role") in {"worker-router", "review-router"}
    ]
    for status in router_completion_statuses:
        completed = status.get("status", {}).get("completed") if isinstance(status.get("status"), dict) else ""
        if isinstance(completed, str) and completed and not any(marker in completed for marker in ('"launch_manifest"', '"schema_invalid"', "launch_manifest", "schema_invalid")):
            errors.append(
                {
                    "code": "session.router_non_manifest_output",
                    "role": status.get("agent_role"),
                    "message": "Router completed without a launch_manifest or schema_invalid artifact.",
                }
            )

    meta_gate_spawns = [
        spawn for spawn in spawns
        if spawn.get("agent_type") == "meta-judge"
        and has_any(str(spawn.get("message") or ""), ("FINAL_OK", "final judgment", "final output", "feedback_required", "Feedback Trigger Gate", "judgment_envelope"))
    ]
    latest_meta_gate_spawn = meta_gate_spawns[-1:] if meta_gate_spawns else []
    for spawn in latest_meta_gate_spawn:
        prompt = str(spawn.get("message") or "")
        if not all(marker in prompt for marker in ("aggregation", "review", "feedback_gate")) and "Feedback Trigger Gate" not in prompt:
            errors.append(
                {
                    "code": "session.meta_prompt_incomplete",
                    "line": spawn["line"],
                    "message": "Meta-judge final prompt lacks aggregation/review/gate evidence markers.",
                }
            )
        if not all(marker in prompt for marker in ("stage_passes", "active_passes")) or not any(marker in prompt for marker in ("review_results", "review_input_refs", "review_waivers")):
            errors.append(
                {
                    "code": "session.final_without_physical_bundle",
                    "line": spawn["line"],
                    "message": "Meta-judge final prompt did not carry stage_passes/review_results/active_passes physical evidence bundle.",
                }
            )
        if "feedback_gate_evidence" not in prompt:
            errors.append(
                {
                    "code": "session.final_without_feedback_gate_evidence",
                    "line": spawn["line"],
                    "message": "Meta-judge final prompt did not carry explicit feedback_gate_evidence.",
                }
            )

    spawned_wait_targets = {target for wait in waits for target in wait.get("targets", []) if isinstance(target, str)}
    # The session log's spawn function-call arguments do not include the new child id;
    # unresolved wait checking is therefore advisory and based on notification text only.
    if spawns and not spawned_wait_targets:
        errors.append(
            {
                "code": "session.no_wait_targets",
                "message": "Physical agents were spawned, but no wait_agent targets were recorded.",
            }
        )

    return result(errors, warnings, counts, spawns, waits)


def result(
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    counts: dict[str, int],
    spawns: list[dict[str, Any]],
    waits: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "validation_status": "passed" if not errors else "failed",
        "failure_class": "none" if not errors else "physical_orchestration_invalid",
        "spawn_role_counts": counts,
        "spawn_count": len(spawns),
        "wait_count": len(waits),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str]) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate physical agent execution from a Codex session JSONL.")
    parser.add_argument("--input", "-i", required=True, help="Codex session JSONL path")
    args = parser.parse_args(argv)
    try:
        events = read_session(Path(args.input))
        report = validate_session(extract_session(events))
    except OSError as exc:
        report = {
            "validation_status": "failed",
            "failure_class": "io_error",
            "errors": [{"code": "io.read", "path": args.input, "message": str(exc)}],
            "warnings": [],
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["validation_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
