from __future__ import annotations

import os
import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from context_ledger_mcp.ledger import ContextLedger, LedgerError
from context_ledger_mcp.validation import (
    build_next_stage_guidance,
    validate_execution_plan as validate_execution_plan_payload,
    validate_review_plan as validate_review_plan_payload,
    validate_stage_completion as validate_stage_completion_payload,
    validate_stage_packet as validate_stage_packet_payload,
    validate_task_design as validate_task_design_payload,
    validate_tool_sequence as validate_tool_sequence_payload,
)


DEFAULT_DB_PATH = Path.cwd() / "data" / "context-ledger.sqlite"

mcp = FastMCP("codex-context-ledger")


def _ledger() -> ContextLedger:
    db_path = os.environ.get("CODEX_CONTEXT_LEDGER_DB")
    return ContextLedger(Path(db_path) if db_path else DEFAULT_DB_PATH)


def _ok(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **payload}


def _error(error: Exception) -> dict[str, Any]:
    return {"ok": False, "error": type(error).__name__, "message": str(error)}


def _record_tool(
    run_id: str,
    stage_name: str | None,
    tool_name: str,
    payload: dict[str, Any] | None,
    result: dict[str, Any],
    context_revision: int | None = None,
) -> None:
    if not stage_name:
        return
    try:
        _ledger().record_tool_call(run_id, stage_name, tool_name, payload, result, context_revision)
    except Exception:
        pass


@mcp.tool()
def initialize_run(run_id: str, goal: str, metadata: dict[str, Any] | None = None, stage_name: str | None = None) -> dict[str, Any]:
    """Create or reopen a run ledger."""
    try:
        result = _ok({"ledger": _ledger().initialize_run(run_id, goal, metadata)})
        _record_tool(run_id, stage_name, "initialize_run", {"goal": goal, "metadata": metadata}, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def read_context_packet(run_id: str, revision: int | None = None, stage_name: str | None = None) -> dict[str, Any]:
    """Read the latest or requested context packet revision."""
    try:
        result = _ok(_ledger().read_context_packet(run_id, revision))
        context_packet = result.get("context_packet")
        if isinstance(context_packet, dict) and context_packet.get("next_owner"):
            result["next_stage"] = build_next_stage_guidance(context_packet["next_owner"])
        _record_tool(run_id, stage_name, "read_context_packet", {"revision": revision}, result, result.get("context_revision"))
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def write_context_packet(
    run_id: str,
    packet: dict[str, Any],
    expected_revision: int | None = None,
    stage_name: str | None = None,
) -> dict[str, Any]:
    """Append a context packet revision, optionally guarded by the current revision."""
    try:
        result = _ok(_ledger().write_context_packet(run_id, packet, expected_revision))
        context_packet = result.get("context_packet")
        if isinstance(context_packet, dict) and context_packet.get("next_owner"):
            result["next_stage"] = build_next_stage_guidance(context_packet["next_owner"])
        _record_tool(run_id, stage_name, "write_context_packet", {"expected_revision": expected_revision}, result, result.get("context_revision"))
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def record_artifact_ref(
    run_id: str,
    artifact_ref: str,
    artifact_type: str,
    producer_stage: str | None = None,
    metadata: dict[str, Any] | None = None,
    stage_name: str | None = None,
) -> dict[str, Any]:
    """Attach an artifact reference to a run."""
    try:
        result = _ok(
            _ledger().record_artifact_ref(
                run_id,
                artifact_ref,
                artifact_type,
                producer_stage,
                metadata,
            )
        )
        _record_tool(run_id, stage_name or producer_stage, "record_artifact_ref", {"artifact_ref": artifact_ref, "artifact_type": artifact_type}, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def append_stage_pass(
    run_id: str,
    stage_name: str,
    stage_execution_mode: str,
    evidence: dict[str, Any] | None = None,
    context_revision: int | None = None,
) -> dict[str, Any]:
    """Append stage pass evidence for a control or specialist stage."""
    try:
        result = _ok(
            _ledger().append_stage_pass(
                run_id,
                stage_name,
                stage_execution_mode,
                evidence,
                context_revision,
            )
        )
        _record_tool(run_id, stage_name, "append_stage_pass", {"stage_execution_mode": stage_execution_mode, "context_revision": context_revision}, result, context_revision)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def set_role_pass_readiness(
    run_id: str,
    role_name: str,
    ready: bool,
    context_revision: int,
    reason: str | None = None,
    stage_name: str | None = None,
) -> dict[str, Any]:
    """Set readiness for a downstream role pass at the current context revision."""
    try:
        result = _ok(
            _ledger().set_role_pass_readiness(
                run_id,
                role_name,
                ready,
                context_revision,
                reason,
            )
        )
        _record_tool(run_id, stage_name or "context-ledger", "set_role_pass_readiness", {"role_name": role_name, "ready": ready}, result, context_revision)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def mark_stale(
    run_id: str,
    target_ref: str,
    reason: str,
    context_revision: int | None = None,
    stage_name: str | None = None,
) -> dict[str, Any]:
    """Mark a context item, artifact, or stage reference as stale."""
    try:
        result = _ok(_ledger().mark_stale(run_id, target_ref, reason, context_revision))
        _record_tool(run_id, stage_name, "mark_stale", {"target_ref": target_ref, "reason": reason}, result, context_revision)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def record_mcp_quiescence(
    run_id: str,
    stage_name: str,
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Record MCP cleanup evidence for a stage."""
    try:
        result = _ok(_ledger().record_mcp_quiescence(run_id, stage_name, snapshot))
        _record_tool(run_id, stage_name, "record_mcp_quiescence", {"snapshot": snapshot}, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_context_revision(run_id: str, context_revision: int, stage_name: str | None = None) -> dict[str, Any]:
    """Check whether a caller is using the latest context revision."""
    try:
        result = _ok(_ledger().validate_context_revision(run_id, context_revision))
        _record_tool(run_id, stage_name, "validate_context_revision", {"context_revision": context_revision}, result, context_revision)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_stage_packet(
    run_id: str,
    stage_name: str,
    packet: dict[str, Any],
    require_current_revision: bool = True,
) -> dict[str, Any]:
    """Validate a stage packet against ledger barrier and handoff rules."""
    try:
        current_revision = None
        completed_stages = None
        if require_current_revision:
            ledger = _ledger()
            current_revision = ledger.read_context_packet(run_id)["context_revision"]
            completed_stages = [item["stage_name"] for item in ledger.query_run_ledger(run_id)["stage_passes"]]
        result = _ok(validate_stage_packet_payload(stage_name, packet, current_revision=current_revision, completed_stages=completed_stages))
        _record_tool(run_id, stage_name, "validate_stage_packet", {"require_current_revision": require_current_revision}, result, current_revision)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_stage_completion(
    run_id: str,
    stage_name: str,
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Validate completion readiness separately from stage packet shape."""
    try:
        result = _ok(validate_stage_completion_payload(stage_name, packet))
        _record_tool(run_id, stage_name, "validate_stage_completion", None, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_task_design(
    run_id: str,
    packet: dict[str, Any],
    stage_name: str = "task-designer",
) -> dict[str, Any]:
    """Validate task_design option comparison, selected option, and distribution boundaries."""
    try:
        result = _ok(validate_task_design_payload(packet))
        _record_tool(run_id, stage_name, "validate_task_design", None, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_execution_plan(
    run_id: str,
    packet: dict[str, Any],
    stage_name: str = "task-distributor",
) -> dict[str, Any]:
    """Validate execution_plan against distribution criteria, lane, dependency, and fanout rules."""
    try:
        result = _ok(validate_execution_plan_payload(packet))
        _record_tool(run_id, stage_name, "validate_execution_plan", None, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_review_plan(
    run_id: str,
    packet: dict[str, Any],
    stage_name: str = "review-distributor",
) -> dict[str, Any]:
    """Validate review_plan against review distribution criteria, coverage, and reviewer lane rules."""
    try:
        result = _ok(validate_review_plan_payload(packet))
        _record_tool(run_id, stage_name, "validate_review_plan", None, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_tool_sequence(run_id: str, stage_name: str) -> dict[str, Any]:
    """Validate that required MCP tools were called in the stage order."""
    try:
        events = _ledger().list_tool_calls(run_id, stage_name)
        observed_tools = [event["tool_name"] for event in events] + ["validate_tool_sequence"]
        result = _ok(validate_tool_sequence_payload(stage_name, observed_tools))
        _record_tool(run_id, stage_name, "validate_tool_sequence", None, result)
        return result
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def query_run_ledger(run_id: str) -> dict[str, Any]:
    """Return a compact run ledger snapshot."""
    try:
        return _ok({"ledger": _ledger().query_run_ledger(run_id)})
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def close_run(run_id: str, status: str = "closed") -> dict[str, Any]:
    """Close a run ledger."""
    try:
        return _ok({"ledger": _ledger().close_run(run_id, status)})
    except Exception as exc:
        return _error(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Codex Context Ledger MCP server.")
    parser.add_argument(
        "--transport",
        choices=("streamable-http",),
        default=os.environ.get("CODEX_CONTEXT_LEDGER_TRANSPORT", "streamable-http"),
    )
    parser.add_argument("--host", default=os.environ.get("CODEX_CONTEXT_LEDGER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("CODEX_CONTEXT_LEDGER_PORT", "8765")))
    parser.add_argument("--path", default=os.environ.get("CODEX_CONTEXT_LEDGER_PATH", "/mcp"))
    args = parser.parse_args()

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.streamable_http_path = args.path
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
