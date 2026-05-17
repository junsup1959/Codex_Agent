#!/usr/bin/env python3
"""Caller-side handoff wiring for the Codex architecture.

All non-trivial stage transitions should pass through this script. It calls
`harness_gate.py`, records the decision, and writes either the original payload
for the next stage or a blocked feedback envelope for orchestrator re-entry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import harness_gate


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_json(path: str | None) -> Any:
    if path in (None, "-"):
        return json.loads(sys.stdin.read())
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path: str | None, payload: Any) -> None:
    if not path:
        return
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: str | None, payload: Any) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def error_gate_decision(
    args: argparse.Namespace,
    *,
    failure_class: str,
    code: str,
    message: str,
    path: str = "output",
) -> dict[str, Any]:
    return {
        "gate_status": "blocked",
        "runtime_validation_required": True,
        "stage_owner": args.stage_owner,
        "artifact_type": args.artifact,
        "expected_next_owner": args.expected_next_owner,
        "expected_source_ref": args.expected_source_ref,
        "expected_context_packet_version": args.expected_context_packet_version,
        "previous_judgment_checked": bool(getattr(args, "previous_judgment_json", None)),
        "schema_status": "invalid",
        "failure_class": failure_class,
        "allow_next_stage": False,
        "next_owner": None,
        "next_loop_start": None,
        "feedback_required": False,
        "route_kind": "retry_same_stage",
        "validation_result": {
            "validation_status": "failed",
            "schema_status": "invalid",
            "failure_class": failure_class,
            "errors": [{"code": code, "path": path, "message": message}],
        },
    }


def io_error_decision(args: argparse.Namespace, exc: Exception) -> dict[str, Any]:
    gate_decision = error_gate_decision(args, failure_class="io_error", code="io.write", message=str(exc), path="output")
    return {
        "handoff_status": "blocked",
        "runtime_validation_required": True,
        "stage_owner": args.stage_owner,
        "artifact_type": args.artifact,
        "schema_status": "invalid",
        "failure_class": "io_error",
        "allow_next_stage": False,
        "next_owner": None,
        "next_loop_start": None,
        "feedback_required": False,
        "route_kind": "retry_same_stage",
        "expected_next_owner": args.expected_next_owner,
        "expected_source_ref": args.expected_source_ref,
        "expected_context_packet_version": args.expected_context_packet_version,
        "previous_judgment_checked": bool(getattr(args, "previous_judgment_json", None)),
        "gate_decision": gate_decision,
    }


def cli_exception_decision(args: argparse.Namespace, failure_class: str, code: str, exc: Exception) -> dict[str, Any]:
    gate_decision = error_gate_decision(args, failure_class=failure_class, code=code, message=str(exc), path=args.input or "stdin")
    return {
        "handoff_status": "blocked",
        "runtime_validation_required": True,
        "stage_owner": args.stage_owner,
        "artifact_type": args.artifact,
        "schema_status": "invalid",
        "failure_class": failure_class,
        "allow_next_stage": False,
        "next_owner": None,
        "next_loop_start": None,
        "feedback_required": False,
        "route_kind": "retry_same_stage",
        "expected_next_owner": args.expected_next_owner,
        "expected_source_ref": args.expected_source_ref,
        "expected_context_packet_version": args.expected_context_packet_version,
        "previous_judgment_checked": bool(getattr(args, "previous_judgment_json", None)),
        "gate_decision": gate_decision,
    }


def handoff_stage_output(
    payload: Any,
    *,
    stage_owner: str,
    artifact: str = "auto",
    expected_next_owner: str | None = None,
    expected_source_ref: str | None = None,
    expected_context_packet_version: str | None = None,
    active_passes: Any | None = None,
    stage_passes: Any | None = None,
    review_results: Any | None = None,
    previous_judgment: Any | None = None,
) -> dict[str, Any]:
    gate_decision = harness_gate.gate_stage_output(
        payload,
        stage_owner=stage_owner,
        artifact=artifact,
        expected_next_owner=expected_next_owner,
        expected_source_ref=expected_source_ref,
        expected_context_packet_version=expected_context_packet_version,
        active_passes=active_passes,
        stage_passes=stage_passes,
        review_results=review_results,
        previous_judgment=previous_judgment,
    )
    allowed = gate_decision["gate_status"] == "passed" and gate_decision["allow_next_stage"] is True
    return {
        "handoff_status": "allowed" if allowed else "blocked",
        "runtime_validation_required": True,
        "stage_owner": stage_owner,
        "artifact_type": gate_decision["artifact_type"],
        "schema_status": gate_decision["schema_status"],
        "failure_class": gate_decision["failure_class"],
        "allow_next_stage": allowed,
        "next_owner": gate_decision["next_owner"],
        "next_loop_start": gate_decision["next_loop_start"],
        "feedback_required": gate_decision["feedback_required"],
        "route_kind": gate_decision["route_kind"],
        "expected_next_owner": expected_next_owner,
        "expected_source_ref": expected_source_ref,
        "expected_context_packet_version": expected_context_packet_version,
        "previous_judgment_checked": previous_judgment is not None,
        "gate_decision": gate_decision,
    }


def extract_contract_provenance(original_payload: Any) -> dict[str, Any]:
    if isinstance(original_payload, dict):
        if isinstance(original_payload.get("contract_provenance"), dict):
            return original_payload["contract_provenance"]
        for value in original_payload.values():
            if isinstance(value, dict) and isinstance(value.get("contract_provenance"), dict):
                return value["contract_provenance"]
    return {
        "source_contract_refs": [
            "01-harness-layer.md",
            "07-contracts-ledgers.md",
            "08-quality-evals.md",
        ],
        "contract_lookup_missing": False,
    }


def next_input_payload(original_payload: Any, handoff_decision: dict[str, Any]) -> Any:
    if handoff_decision["allow_next_stage"]:
        return original_payload
    return {
        "transport_wrapper": "blocked_handoff",
        "handoff_status": "blocked",
        "runtime_validation_required": True,
        "feedback_required": handoff_decision["feedback_required"],
        "next_owner": handoff_decision["next_owner"],
        "next_loop_start": handoff_decision["next_loop_start"],
        "route_kind": handoff_decision["route_kind"],
        "failure_class": handoff_decision["failure_class"],
        "blocked_stage_owner": handoff_decision["stage_owner"],
        "blocked_artifact_type": handoff_decision["artifact_type"],
        "contract_provenance": extract_contract_provenance(original_payload),
        "validation_result": handoff_decision["gate_decision"]["validation_result"],
    }


def main(argv: list[str]) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Validate and route one Codex stage handoff.")
    parser.add_argument("--stage-owner", required=True, choices=sorted(harness_gate.STAGE_HANDOFF_POLICY), help="stage that emitted the JSON")
    parser.add_argument("--input", "-i", help="stage output JSON path; omit or use - for stdin")
    parser.add_argument("--artifact", default="auto", help="artifact override for validate-runtime-artifact.py")
    parser.add_argument("--expected-next-owner", help="block if derived next owner does not match")
    parser.add_argument("--expected-source-ref", help="block if source lineage ref does not match")
    parser.add_argument("--expected-context-packet-version", help="block if context packet version does not match")
    parser.add_argument("--active-passes-json", help="active_passes JSON for router materialization and completion checks")
    parser.add_argument("--stage-passes-json", help="stage_passes JSON for meta-judge completion evidence")
    parser.add_argument("--review-results-json", help="review handoff_result JSON bundle for meta-judge completion evidence")
    parser.add_argument("--previous-judgment-json", help="previous judgment_envelope JSON for feedback lineage checks")
    parser.add_argument("--decision-out", help="write full handoff decision JSON")
    parser.add_argument("--next-input-out", help="write payload to feed the next owner")
    parser.add_argument("--ledger-out", help="append compact handoff decision JSONL")
    args = parser.parse_args(argv)

    try:
        payload = load_json(args.input)
        active_passes = load_json(args.active_passes_json) if args.active_passes_json else None
        stage_passes = load_json(args.stage_passes_json) if args.stage_passes_json else None
        review_results = load_json(args.review_results_json) if args.review_results_json else None
        previous_judgment = load_json(args.previous_judgment_json) if args.previous_judgment_json else None
        decision = handoff_stage_output(
            payload,
            stage_owner=args.stage_owner,
            artifact=args.artifact,
            expected_next_owner=args.expected_next_owner,
            expected_source_ref=args.expected_source_ref,
            expected_context_packet_version=args.expected_context_packet_version,
            active_passes=active_passes,
            stage_passes=stage_passes,
            review_results=review_results,
            previous_judgment=previous_judgment,
        )
    except json.JSONDecodeError as exc:
        decision = cli_exception_decision(args, "input_invalid", "json.decode", exc)
    except OSError as exc:
        decision = cli_exception_decision(args, "io_error", "io.read", exc)
    except Exception as exc:  # Keep the caller contract machine-readable even for loader failures.
        decision = cli_exception_decision(args, "validator_bug", "harness_handoff.exception", exc)

    try:
        write_json(args.decision_out, decision)
        write_json(args.next_input_out, next_input_payload(payload if "payload" in locals() else {}, decision))
        append_jsonl(args.ledger_out, decision)
    except OSError as exc:
        decision = io_error_decision(args, exc)
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0 if decision["allow_next_stage"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
