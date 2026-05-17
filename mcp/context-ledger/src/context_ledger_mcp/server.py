from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from context_ledger_mcp.ledger import ContextLedger, LedgerError


DEFAULT_DB_PATH = Path.cwd() / "data" / "context-ledger.sqlite"

mcp = FastMCP("codex-context-ledger")


def _ledger() -> ContextLedger:
    db_path = os.environ.get("CODEX_CONTEXT_LEDGER_DB")
    return ContextLedger(Path(db_path) if db_path else DEFAULT_DB_PATH)


def _ok(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **payload}


def _error(error: Exception) -> dict[str, Any]:
    return {"ok": False, "error": type(error).__name__, "message": str(error)}


@mcp.tool()
def initialize_run(run_id: str, goal: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create or reopen a run ledger."""
    try:
        return _ok({"ledger": _ledger().initialize_run(run_id, goal, metadata)})
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def read_context_packet(run_id: str, revision: int | None = None) -> dict[str, Any]:
    """Read the latest or requested context packet revision."""
    try:
        return _ok(_ledger().read_context_packet(run_id, revision))
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def write_context_packet(
    run_id: str,
    packet: dict[str, Any],
    expected_revision: int | None = None,
) -> dict[str, Any]:
    """Append a context packet revision, optionally guarded by the current revision."""
    try:
        return _ok(_ledger().write_context_packet(run_id, packet, expected_revision))
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def record_artifact_ref(
    run_id: str,
    artifact_ref: str,
    artifact_type: str,
    producer_stage: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach an artifact reference to a run."""
    try:
        return _ok(
            _ledger().record_artifact_ref(
                run_id,
                artifact_ref,
                artifact_type,
                producer_stage,
                metadata,
            )
        )
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
        return _ok(
            _ledger().append_stage_pass(
                run_id,
                stage_name,
                stage_execution_mode,
                evidence,
                context_revision,
            )
        )
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def set_role_pass_readiness(
    run_id: str,
    role_name: str,
    ready: bool,
    context_revision: int,
    reason: str | None = None,
) -> dict[str, Any]:
    """Set readiness for a downstream role pass at the current context revision."""
    try:
        return _ok(
            _ledger().set_role_pass_readiness(
                run_id,
                role_name,
                ready,
                context_revision,
                reason,
            )
        )
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def mark_stale(
    run_id: str,
    target_ref: str,
    reason: str,
    context_revision: int | None = None,
) -> dict[str, Any]:
    """Mark a context item, artifact, or stage reference as stale."""
    try:
        return _ok(_ledger().mark_stale(run_id, target_ref, reason, context_revision))
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
        return _ok(_ledger().record_mcp_quiescence(run_id, stage_name, snapshot))
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def validate_context_revision(run_id: str, context_revision: int) -> dict[str, Any]:
    """Check whether a caller is using the latest context revision."""
    try:
        return _ok(_ledger().validate_context_revision(run_id, context_revision))
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
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

