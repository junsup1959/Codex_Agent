from __future__ import annotations

import unittest

from context_ledger_mcp.ledger import ContextLedger
from context_ledger_mcp.validation import validate_stage_packet, validate_tool_sequence


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
            {"handoff.spawn_receipt_ref", "handoff.agent_id", "handoff.wait_agent_evidence"},
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


if __name__ == "__main__":
    unittest.main()
