from __future__ import annotations

import unittest

from context_ledger_mcp.ledger import ContextLedger


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
            ledger.set_role_pass_readiness("run-1", "worker-router", True, 1)
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

    def test_write_context_rejects_stale_expected_revision(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            ledger = ContextLedger(f"{temp_dir}/ledger.sqlite")
            ledger.initialize_run("run-1", "test goal")
            ledger.write_context_packet("run-1", {"approved_facts": []}, expected_revision=0)

            with self.assertRaisesRegex(ValueError, "stale context revision"):
                ledger.write_context_packet("run-1", {"approved_facts": ["late"]}, expected_revision=0)


if __name__ == "__main__":
    unittest.main()
