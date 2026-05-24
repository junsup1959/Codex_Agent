from __future__ import annotations

import unittest
import ast
from pathlib import Path

from context_ledger_mcp.ledger import ContextLedger
from context_ledger_mcp.validation import (
    REQUIRED_TOOL_SEQUENCE,
    validate_stage_completion,
    validate_stage_packet,
    validate_tool_sequence,
)


class ContextLedgerTests(unittest.TestCase):
    def test_context_revision_flow(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            ledger = ContextLedger(f"{temp_dir}/ledger.sqlite")

            ledger.initialize_run("run-1", "test goal", {"source": "unit"})
            empty = ledger.read_context_packet("run-1")
            self.assertEqual(empty["context_revision"], 0)

            first = ledger.write_context_packet(
                "run-1",
                {"approved_facts": ["fact"], "artifact_inventory": []},
                expected_revision=0,
            )
            self.assertEqual(first["context_revision"], 1)

            validation = ledger.validate_context_revision("run-1", 1)
            self.assertTrue(validation["valid"])

            stale_validation = ledger.validate_context_revision("run-1", 0)
            self.assertFalse(stale_validation["valid"])
            self.assertEqual(stale_validation["current_revision"], 1)

    def test_records_run_evidence(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            ledger = ContextLedger(f"{temp_dir}/ledger.sqlite")
            ledger.initialize_run("run-1", "test goal")
            ledger.write_context_packet("run-1", {"approved_facts": []}, expected_revision=0)

            ledger.record_artifact_ref(
                "run-1",
                "docs/plan.md",
                "plan",
                producer_stage="task-planner",
                metadata={"sha256": "abc"},
            )
            ledger.append_stage_pass(
                "run-1",
                "task-planner",
                "main_agent_role_pass",
                evidence={"plan_ref": "docs/plan.md"},
                context_revision=1,
            )
            ledger.set_role_pass_readiness("run-1", "worker", True, 1)
            ledger.mark_stale("run-1", "old-context", "superseded", 1)
            ledger.record_mcp_quiescence(
                "run-1",
                "task-planner",
                {"open_mcp_process_count": 0, "cleanup_status": "clean"},
            )

            snapshot = ledger.query_run_ledger("run-1")
            self.assertEqual(snapshot["current_revision"], 1)
            self.assertEqual(snapshot["artifact_refs"][0]["artifact_ref"], "docs/plan.md")
            self.assertEqual(snapshot["stage_passes"][0]["stage_name"], "task-planner")
            self.assertTrue(snapshot["readiness_flags"][0]["ready"])
            self.assertEqual(snapshot["stale_markers"][0]["target_ref"], "old-context")
            self.assertEqual(snapshot["tool_call_events"], [])

    def test_write_context_rejects_stale_expected_revision(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            ledger = ContextLedger(f"{temp_dir}/ledger.sqlite")
            ledger.initialize_run("run-1", "test goal")
            ledger.write_context_packet("run-1", {"approved_facts": []}, expected_revision=0)

            with self.assertRaisesRegex(ValueError, "stale context revision"):
                ledger.write_context_packet("run-1", {"approved_facts": ["late"]}, expected_revision=0)

    def test_validate_stage_packet_api_contract(self):
        packet = {
            "stage_name": "task-planner",
            "context_packet_version": 1,
            "consumed_context_revision": 2,
            "context_delta": {"approved_facts": ["planned"]},
            "new_artifact_refs": ["artifact:plan"],
            "new_evidence_refs": ["evidence:plan"],
            "stage_pass_ref": "stage_pass:task-planner:1",
            "next_owner": "worker",
            "execution_plan": {"lanes": []},
        }
        result = validate_stage_packet("task-planner", packet, current_revision=2)
        self.assertTrue(result["valid"], result)

        stale = validate_stage_packet("task-planner", packet, current_revision=3)
        self.assertFalse(stale["valid"])
        self.assertEqual(stale["errors"][0]["code"], "barrier.stale_revision")

    def test_minimal_packets_for_all_mandatory_stages(self):
        cases = {
            "orchestrator": {
                "next_owner": "context-ledger",
                "orchestration_request": {"scope": "unit"},
            },
            "context-ledger": {
                "next_owner": "task-planner",
                "context_packet": {"approved_facts": []},
            },
            "task-planner": {
                "next_owner": "worker",
                "execution_plan": {"lanes": []},
            },
            "worker": {
                "next_owner": "review-distributor",
                "worker_handoff_results": [],
            },
            "review-distributor": {
                "next_owner": "review",
                "review_plan": {"lanes": []},
            },
            "review": {
                "next_owner": "feedbackgate",
                "review_handoff_results": [],
            },
            "feedbackgate": {
                "next_owner": "final",
                "judgment_envelope": {"feedback_required": False},
            },
        }

        for stage_name, stage_fields in cases.items():
            with self.subTest(stage_name=stage_name):
                packet = {
                    "stage_name": stage_name,
                    "context_packet_version": 1,
                    "consumed_context_revision": 4,
                    "context_delta": {"approved_facts": [stage_name]},
                    "new_artifact_refs": [f"artifact:{stage_name}"],
                    "new_evidence_refs": [f"evidence:{stage_name}"],
                    "stage_pass_ref": f"stage_pass:{stage_name}:1",
                    **stage_fields,
                }
                result = validate_stage_packet(stage_name, packet, current_revision=4)
                self.assertTrue(result["valid"], result)

    def test_schema_only_allows_empty_materialized_handoffs(self):
        worker_packet = {
            "stage_name": "worker",
            "context_packet_version": 1,
            "consumed_context_revision": 4,
            "context_delta": {"approved_facts": ["worker"]},
            "new_artifact_refs": ["artifact:worker"],
            "new_evidence_refs": ["evidence:worker"],
            "stage_pass_ref": "stage_pass:worker:1",
            "next_owner": "review-distributor",
            "worker_handoff_results": [],
        }
        review_packet = {
            "stage_name": "review",
            "context_packet_version": 1,
            "consumed_context_revision": 4,
            "context_delta": {"approved_facts": ["review"]},
            "new_artifact_refs": ["artifact:review"],
            "new_evidence_refs": ["evidence:review"],
            "stage_pass_ref": "stage_pass:review:1",
            "next_owner": "feedbackgate",
            "review_handoff_results": [],
        }

        self.assertTrue(validate_stage_packet("worker", worker_packet, current_revision=4)["valid"])
        self.assertTrue(validate_stage_packet("review", review_packet, current_revision=4)["valid"])

    def test_completion_required_rejects_empty_materialized_handoffs(self):
        worker_packet = {"stage_name": "worker", "worker_handoff_results": []}
        review_packet = {"stage_name": "review", "review_handoff_results": []}

        worker_result = validate_stage_completion("worker", worker_packet)
        review_result = validate_stage_completion("review", review_packet)

        self.assertFalse(worker_result["valid"])
        self.assertEqual(worker_result["errors"][0]["code"], "completion.worker_lanes_missing")
        self.assertFalse(review_result["valid"])
        self.assertEqual(review_result["errors"][0]["code"], "completion.review_lanes_missing")

    def test_completion_required_accepts_classified_empty_lanes(self):
        worker_result = validate_stage_completion(
            "worker",
            {
                "stage_name": "worker",
                "worker_handoff_results": [],
                "missing_lane_classifications": [{"lane_id": "worker-1", "reason": "thread_limit_reached"}],
            },
        )
        review_result = validate_stage_completion(
            "review",
            {
                "stage_name": "review",
                "review_handoff_results": [],
                "review_waivers": [{"lane_id": "review-1", "reason": "covered_by_policy"}],
            },
        )

        self.assertTrue(worker_result["valid"], worker_result)
        self.assertTrue(review_result["valid"], review_result)

    def test_completion_required_rejects_malformed_classifications_and_waivers(self):
        worker_result = validate_stage_completion(
            "worker",
            {
                "stage_name": "worker",
                "worker_handoff_results": [],
                "missing_lane_classifications": [{"lane_id": "worker-1"}],
            },
        )
        review_result = validate_stage_completion(
            "review",
            {
                "stage_name": "review",
                "review_handoff_results": [],
                "review_waivers": ["not-an-object"],
            },
        )

        self.assertFalse(worker_result["valid"])
        self.assertEqual(
            {item["code"] for item in worker_result["errors"]},
            {
                "completion.missing_lane_classifications.reason",
                "completion.worker_lanes_missing",
            },
        )
        self.assertFalse(review_result["valid"])
        self.assertEqual(
            {item["code"] for item in review_result["errors"]},
            {
                "completion.review_waivers.item_shape",
                "completion.review_lanes_missing",
            },
        )

    def test_completion_required_blocks_feedbackgate_final_without_evidence(self):
        result = validate_stage_completion(
            "feedbackgate",
            {
                "stage_name": "feedbackgate",
                "judgment_envelope": {"feedback_required": False},
            },
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {
                "completion.feedback_gate_evidence_missing",
                "completion.review_inputs_missing",
                "completion.stage_passes_missing",
                "completion.active_passes_missing",
            },
        )

    def test_completion_required_rejects_malformed_feedbackgate_waivers(self):
        result = validate_stage_completion(
            "feedbackgate",
            {
                "stage_name": "feedbackgate",
                "judgment_envelope": {"feedback_required": False},
                "feedback_gate_evidence": {"review_inputs_present": True},
                "review_waivers": [{"reason": "covered elsewhere"}],
                "stage_passes": ["stage_pass:review:1"],
                "active_passes": ["stage_pass:worker:1"],
            },
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {
                "completion.review_waivers.lane_id",
                "completion.review_inputs_missing",
            },
        )

    def test_completion_required_rejects_malformed_feedbackgate_evidence_shapes(self):
        cases = [
            (
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": "not-a-dict",
                    "review_input_refs": ["review:1"],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
                {"completion.feedback_gate_evidence.shape"},
            ),
            (
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": {"review_inputs_present": True},
                    "review_input_refs": [None],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
                {"completion.review_input_refs.item", "completion.review_inputs_missing"},
            ),
            (
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": {"review_inputs_present": True},
                    "review_input_refs": ["review:1"],
                    "stage_passes": [None],
                    "active_passes": [None],
                },
                {
                    "completion.stage_passes.item",
                    "completion.stage_passes_missing",
                    "completion.active_passes.item",
                    "completion.active_passes_missing",
                },
            ),
        ]

        for packet, expected_codes in cases:
            with self.subTest(packet=packet):
                result = validate_stage_completion("feedbackgate", packet)
                self.assertFalse(result["valid"], result)
                self.assertEqual({item["code"] for item in result["errors"]}, expected_codes)

    def test_worker_handoff_requires_spawn_and_wait_evidence(self):
        valid_packet = {
            "stage_name": "worker",
            "context_packet_version": 1,
            "consumed_context_revision": 3,
            "context_delta": {"artifact_inventory": ["artifact:worker"]},
            "new_artifact_refs": ["artifact:worker"],
            "new_evidence_refs": ["evidence:worker"],
            "stage_pass_ref": "stage_pass:worker:1",
            "next_owner": "review-distributor",
            "worker_handoff_results": [
                {
                    "lane_id": "worker-1",
                    "status": "returned",
                    "spawn_receipt_ref": "spawn:worker-1",
                    "agent_id": "agent-1",
                    "wait_handle": "wait:worker-1",
                    "wait_agent_evidence": {"status": "completed"},
                }
            ],
        }
        self.assertTrue(validate_stage_packet("worker", valid_packet, current_revision=3)["valid"])

        invalid_packet = {
            **valid_packet,
            "worker_handoff_results": [{"lane_id": "worker-1", "status": "returned"}],
        }
        invalid = validate_stage_packet("worker", invalid_packet, current_revision=3)
        self.assertFalse(invalid["valid"])
        self.assertEqual(
            {item["code"] for item in invalid["errors"]},
            {"handoff.spawn_receipt_ref", "handoff.agent_id", "handoff.wait_handle", "handoff.wait_agent_evidence"},
        )

    def test_validates_tool_sequence(self):
        observed = [
            "read_context_packet",
            "validate_context_revision",
            "append_stage_pass",
            "validate_stage_packet",
            "write_context_packet",
            "record_mcp_quiescence",
            "validate_tool_sequence",
        ]
        valid = validate_tool_sequence("task-planner", observed)
        self.assertTrue(valid["valid"], valid)

        invalid = validate_tool_sequence("task-planner", ["read_context_packet", "write_context_packet"])
        self.assertFalse(invalid["valid"])
        self.assertEqual(invalid["errors"][0]["code"], "sequence.incomplete_or_out_of_order")

    def test_materialized_stages_require_completion_validation_in_sequence(self):
        valid = validate_tool_sequence(
            "worker",
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_packet",
                "validate_stage_completion",
                "write_context_packet",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
        )
        self.assertTrue(valid["valid"], valid)

        invalid = validate_tool_sequence(
            "worker",
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_packet",
                "write_context_packet",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
        )
        self.assertFalse(invalid["valid"])
        self.assertEqual(invalid["errors"][0]["code"], "sequence.incomplete_or_out_of_order")

    def test_context_ledger_sequence_requires_readiness_before_write(self):
        valid = validate_tool_sequence(
            "context-ledger",
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_packet",
                "set_role_pass_readiness",
                "write_context_packet",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
        )
        self.assertTrue(valid["valid"], valid)

        invalid = validate_tool_sequence(
            "context-ledger",
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_packet",
                "write_context_packet",
                "set_role_pass_readiness",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
        )
        self.assertFalse(invalid["valid"])
        self.assertEqual(invalid["errors"][0]["code"], "sequence.incomplete_or_out_of_order")

    def test_records_tool_calls(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            ledger = ContextLedger(f"{temp_dir}/ledger.sqlite")
            ledger.initialize_run("run-1", "test goal")
            ledger.record_tool_call("run-1", "task-planner", "read_context_packet")
            ledger.record_tool_call("run-1", "task-planner", "validate_context_revision")

            calls = ledger.list_tool_calls("run-1", "task-planner")
            self.assertEqual([item["tool_name"] for item in calls], ["read_context_packet", "validate_context_revision"])

    def test_required_tool_sequence_is_exposed_by_server(self):
        server_path = Path(__file__).resolve().parents[1] / "src" / "context_ledger_mcp" / "server.py"
        tree = ast.parse(server_path.read_text(encoding="utf-8"))
        server_tools = {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and any(
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "tool"
                for decorator in node.decorator_list
            )
        }
        required_tools = {
            tool_name
            for required_sequence in REQUIRED_TOOL_SEQUENCE.values()
            for tool_name in required_sequence
        }

        self.assertEqual(required_tools - server_tools, set())
        self.assertIn("validate_stage_completion", server_tools)


if __name__ == "__main__":
    unittest.main()
