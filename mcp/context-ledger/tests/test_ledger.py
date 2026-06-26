from __future__ import annotations

import unittest
import ast
import os
from pathlib import Path

from context_ledger_mcp.ledger import ContextLedger
from context_ledger_mcp.validation import (
    REQUIRED_TOOL_SEQUENCE,
    build_next_stage_guidance,
    validate_execution_plan,
    validate_review_plan,
    validate_stage_completion,
    validate_stage_packet,
    validate_task_design,
    validate_tool_sequence,
)


def _artifact_profile(source_stage: str) -> dict:
    return {
        "version": 1,
        "source_stage": source_stage,
        "reuse_policy": "reuse_if_inputs_unchanged",
        "invalidated_by": ["input_change"],
    }


def _sequential_thinking_waiver() -> dict:
    return {
        "status": "tool_error",
        "reason": "MCP_DOCKER sequentialthinking returned an error",
        "fallback_summary": "Used explicit fallback reasoning and preserved decision evidence.",
    }


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
                producer_stage="task-distributor",
                metadata={"sha256": "abc"},
            )
            ledger.append_stage_pass(
                "run-1",
                "task-distributor",
                "main_agent_role_pass",
                evidence={"plan_ref": "docs/plan.md"},
                context_revision=1,
            )
            ledger.set_role_pass_readiness("run-1", "task-designer", True, 1)
            ledger.mark_stale("run-1", "old-context", "superseded", 1)
            ledger.record_mcp_quiescence(
                "run-1",
                "task-distributor",
                {"open_mcp_process_count": 0, "cleanup_status": "clean"},
            )

            snapshot = ledger.query_run_ledger("run-1")
            self.assertEqual(snapshot["current_revision"], 1)
            self.assertEqual(snapshot["artifact_refs"][0]["artifact_ref"], "docs/plan.md")
            self.assertEqual(snapshot["stage_passes"][0]["stage_name"], "task-distributor")
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
            "stage_name": "task-distributor",
            "context_packet_version": 1,
            "consumed_context_revision": 2,
            "context_delta": {"approved_facts": ["planned"]},
            "new_artifact_refs": ["artifact:plan"],
            "new_evidence_refs": ["evidence:plan"],
            "stage_pass_ref": "stage_pass:task-distributor:1",
            "next_owner": "worker",
            "execution_plan": {
                "selected_task_design_ref": "artifact:task_design.md",
                "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
                "artifact_profile": _artifact_profile("task-distributor"),
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:task-distributor",
                "distribution_principles": ["bounded fanout"],
                "fanout_budget": {"max_worker_lanes": 2},
                "worker_lanes": [
                    {
                        "lane_id": "worker-1",
                        "purpose": "unit worker",
                        "specialist_category": "test-automator",
                        "input_artifacts": ["artifact:task_design.md"],
                        "expected_outputs": ["tests"],
                        "handoff_evidence": ["wait_agent_evidence"],
                    }
                ],
                "dependencies": [],
            },
        }
        result = validate_stage_packet("task-distributor", packet, current_revision=2)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["next_stage"]["owner"], "worker")
        self.assertEqual(result["next_stage"]["activation_ref"], "$worker")
        self.assertEqual(result["next_stage"]["contract_ref"], "skills/worker/contract.json")
        self.assertEqual(
            result["next_stage"]["source_docs"],
            ["03-worker-materialization.md", "06-agent-roster-models.md"],
        )
        self.assertEqual(
            result["next_stage"]["required_input_artifacts"],
            ["execution_plan", "task_distribution_criteria_ref", "context_packet", "fanout_budget"],
        )
        self.assertEqual(result["next_stage"]["required_mcp_tools"], list(REQUIRED_TOOL_SEQUENCE["worker"]))

        stale = validate_stage_packet("task-distributor", packet, current_revision=3)
        self.assertFalse(stale["valid"])
        self.assertEqual(stale["errors"][0]["code"], "barrier.stale_revision")

    def test_validate_task_design_requires_options_and_selected_option(self):
        packet = {
            "task_design": {
                "problem_definition": "Split planning into design and distribution.",
                "assumptions": ["orchestrator-started run"],
                "options": [
                    {
                        "id": "option-1",
                        "title": "Keep planner",
                        "summary": "Keep one planner stage.",
                        "fit_assessment": "Lowest change but keeps mixed responsibility.",
                        "tradeoffs": ["fast", "less clear"],
                    },
                    {
                        "id": "option-2",
                        "title": "Split design and distribution",
                        "summary": "Separate design selection from execution allocation.",
                        "fit_assessment": "Best fit for clear handoff contracts.",
                        "tradeoffs": ["more stages", "clearer evidence"],
                    },
                    {
                        "id": "option-3",
                        "title": "Full Maestro-style phases",
                        "summary": "Adopt a heavier phase/session model.",
                        "fit_assessment": "Too heavy for the current ledger-owned runtime.",
                        "tradeoffs": ["comprehensive", "duplicative"],
                    },
                ],
                "comparison_criteria": ["scope clarity", "runtime weight", "MCP evidence"],
                "selected_option_id": "option-2",
                "selection_rationale": "Separates result-shaping design from execution routing.",
                "selected_option_risks": ["additional stage boundary must stay lightweight"],
                "distribution_boundaries": ["do not redefine success criteria", "do not select concrete agents"],
                "artifact_profile": _artifact_profile("task-designer"),
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:task-designer",
            }
        }

        self.assertTrue(validate_task_design(packet)["valid"])

        invalid = validate_task_design({"task_design": {**packet["task_design"], "selected_option_id": "missing"}})
        self.assertFalse(invalid["valid"])
        self.assertIn("task_design.selected_option_missing", {item["code"] for item in invalid["errors"]})

    def test_validate_execution_plan_requires_distribution_criteria_md(self):
        packet = {
            "execution_plan": {
                "selected_task_design_ref": "artifact:task_design.md",
                "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
                "artifact_profile": _artifact_profile("task-distributor"),
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:task-distributor",
                "distribution_principles": ["minimum bounded worker fanout"],
                "fanout_budget": {"max_worker_lanes": 2},
                "worker_lanes": [
                    {
                        "lane_id": "worker-1",
                        "purpose": "Implement stage split.",
                        "specialist_category": "mcp-developer",
                        "input_artifacts": ["artifact:task_design.md", "artifact:task_distribution_criteria.md"],
                        "expected_outputs": ["code changes", "tests"],
                        "handoff_evidence": ["spawn_receipt_ref", "wait_handle", "wait_agent_evidence"],
                    }
                ],
                "dependencies": [],
            }
        }

        self.assertTrue(validate_execution_plan(packet)["valid"])

        invalid = validate_execution_plan(
            {"execution_plan": {**packet["execution_plan"], "task_distribution_criteria_ref": "artifact:criteria.json"}}
        )
        self.assertFalse(invalid["valid"])
        self.assertIn("execution_plan.criteria_ref_format", {item["code"] for item in invalid["errors"]})

    def test_validate_review_plan_requires_distribution_criteria_md(self):
        packet = {
            "review_plan": {
                "worker_handoff_results_ref": "artifact:worker_handoffs.json",
                "review_distribution_criteria_ref": "artifact:review_distribution_criteria.md",
                "artifact_profile": _artifact_profile("review-distributor"),
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:review-distributor",
                "review_principles": ["coverage follows actual worker evidence"],
                "coverage_contract": {"requires_specialist_reviewers": True},
                "review_lanes": [
                    {
                        "lane_id": "review-1",
                        "purpose": "Review architecture split.",
                        "reviewer_category": "architect-reviewer",
                        "input_artifacts": ["artifact:worker_handoffs.json"],
                        "required_findings": ["bugs", "contract gaps"],
                        "handoff_evidence": ["spawn_receipt_ref", "wait_handle", "wait_agent_evidence"],
                    }
                ],
            }
        }

        self.assertTrue(validate_review_plan(packet)["valid"])

        invalid = validate_review_plan(
            {"review_plan": {**packet["review_plan"], "review_distribution_criteria_ref": "artifact:criteria.json"}}
        )
        self.assertFalse(invalid["valid"])
        self.assertIn("review_plan.criteria_ref_format", {item["code"] for item in invalid["errors"]})

    def test_artifact_profile_is_required_for_reusable_stage_artifacts(self):
        task_design = {
            "problem_definition": "unit design",
            "assumptions": ["unit"],
            "options": [
                {"id": "option-1", "title": "A", "summary": "A", "fit_assessment": "ok", "tradeoffs": ["x"]},
                {"id": "option-2", "title": "B", "summary": "B", "fit_assessment": "best", "tradeoffs": ["y"]},
                {"id": "option-3", "title": "C", "summary": "C", "fit_assessment": "too much", "tradeoffs": ["z"]},
            ],
            "comparison_criteria": ["fit"],
            "selected_option_id": "option-2",
            "selection_rationale": "best fit",
            "selected_option_risks": ["unit risk"],
            "distribution_boundaries": ["no redesign"],
        }
        execution_plan = {
            "selected_task_design_ref": "artifact:task_design.md",
            "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
            "distribution_principles": ["bounded fanout"],
            "fanout_budget": {"max_worker_lanes": 2},
            "worker_lanes": [
                {
                    "lane_id": "worker-1",
                    "purpose": "unit worker",
                    "specialist_category": "test-automator",
                    "input_artifacts": ["artifact:task_design.md"],
                    "expected_outputs": ["tests"],
                    "handoff_evidence": ["wait_agent_evidence"],
                }
            ],
            "dependencies": [],
        }
        review_plan = {
            "worker_handoff_results_ref": "artifact:worker_handoffs.json",
            "review_distribution_criteria_ref": "artifact:review_distribution_criteria.md",
            "review_principles": ["review actual worker evidence"],
            "coverage_contract": {"requires_specialist_reviewers": True},
            "review_lanes": [
                {
                    "lane_id": "review-1",
                    "purpose": "unit review",
                    "reviewer_category": "code-reviewer",
                    "input_artifacts": ["artifact:worker_handoffs.json"],
                    "required_findings": ["bugs"],
                    "handoff_evidence": ["wait_agent_evidence"],
                }
            ],
        }

        self.assertIn(
            "task_design.artifact_profile.shape",
            {item["code"] for item in validate_task_design({"task_design": task_design})["errors"]},
        )
        self.assertIn(
            "execution_plan.artifact_profile.shape",
            {item["code"] for item in validate_execution_plan({"execution_plan": execution_plan})["errors"]},
        )
        self.assertIn(
            "review_plan.artifact_profile.shape",
            {item["code"] for item in validate_review_plan({"review_plan": review_plan})["errors"]},
        )

    def test_sequential_thinking_ref_is_required_for_reasoning_stages(self):
        orchestrator_packet = {
            "stage_name": "orchestrator",
            "context_packet_version": 1,
            "consumed_context_revision": 1,
            "context_delta": {"approved_facts": ["unit"]},
            "new_artifact_refs": ["artifact:orchestrator"],
            "new_evidence_refs": ["evidence:orchestrator"],
            "stage_pass_ref": "stage_pass:orchestrator:1",
            "next_owner": "context-ledger",
            "orchestration_request": {"scope": "unit"},
        }
        self.assertIn(
            "sequential_thinking_ref.missing",
            {item["code"] for item in validate_stage_packet("orchestrator", orchestrator_packet)["errors"]},
        )

        valid_task_design = {
            "problem_definition": "unit design",
            "assumptions": ["unit"],
            "options": [
                {"id": "option-1", "title": "A", "summary": "A", "fit_assessment": "ok", "tradeoffs": ["x"]},
                {"id": "option-2", "title": "B", "summary": "B", "fit_assessment": "best", "tradeoffs": ["y"]},
                {"id": "option-3", "title": "C", "summary": "C", "fit_assessment": "too much", "tradeoffs": ["z"]},
            ],
            "comparison_criteria": ["fit"],
            "selected_option_id": "option-2",
            "selection_rationale": "best fit",
            "selected_option_risks": ["unit risk"],
            "distribution_boundaries": ["no redesign"],
            "artifact_profile": _artifact_profile("task-designer"),
        }
        self.assertIn(
            "task_design.sequential_thinking_ref.missing",
            {item["code"] for item in validate_task_design({"task_design": valid_task_design})["errors"]},
        )

        valid_execution_plan = {
            "selected_task_design_ref": "artifact:task_design.md",
            "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
            "artifact_profile": _artifact_profile("task-distributor"),
            "distribution_principles": ["bounded fanout"],
            "fanout_budget": {"max_worker_lanes": 2},
            "worker_lanes": [
                {
                    "lane_id": "worker-1",
                    "purpose": "unit worker",
                    "specialist_category": "test-automator",
                    "input_artifacts": ["artifact:task_design.md"],
                    "expected_outputs": ["tests"],
                    "handoff_evidence": ["wait_agent_evidence"],
                }
            ],
            "dependencies": [],
        }
        self.assertIn(
            "execution_plan.sequential_thinking_ref.missing",
            {item["code"] for item in validate_execution_plan({"execution_plan": valid_execution_plan})["errors"]},
        )

        valid_review_plan = {
            "worker_handoff_results_ref": "artifact:worker_handoffs.json",
            "review_distribution_criteria_ref": "artifact:review_distribution_criteria.md",
            "artifact_profile": _artifact_profile("review-distributor"),
            "review_principles": ["review actual worker evidence"],
            "coverage_contract": {"requires_specialist_reviewers": True},
            "review_lanes": [
                {
                    "lane_id": "review-1",
                    "purpose": "unit review",
                    "reviewer_category": "code-reviewer",
                    "input_artifacts": ["artifact:worker_handoffs.json"],
                    "required_findings": ["bugs"],
                    "handoff_evidence": ["wait_agent_evidence"],
                }
            ],
        }
        self.assertIn(
            "review_plan.sequential_thinking_ref.missing",
            {item["code"] for item in validate_review_plan({"review_plan": valid_review_plan})["errors"]},
        )

        waiver = {
            "status": "tool_error",
            "reason": "MCP_DOCKER sequentialthinking returned an error",
            "fallback_summary": "Used explicit option comparison fallback and preserved assumptions.",
        }
        self.assertTrue(
            validate_task_design({"task_design": {**valid_task_design, "sequential_thinking_waiver": waiver}})["valid"]
        )
        self.assertTrue(
            validate_execution_plan(
                {"execution_plan": {**valid_execution_plan, "sequential_thinking_waiver": waiver}}
            )["valid"]
        )
        self.assertTrue(
            validate_review_plan({"review_plan": {**valid_review_plan, "sequential_thinking_waiver": waiver}})["valid"]
        )

    def test_feedback_reentry_requires_reuse_and_invalidation_scope(self):
        result = validate_stage_completion(
            "feedbackgate",
            {
                "stage_name": "feedbackgate",
                "judgment_envelope": {
                    "feedback_required": True,
                    "task_design_reentry_decision": {
                        "action": "reuse_task_design",
                        "task_design_ref": "artifact:task_design.md",
                        "reason": "implementation-only feedback",
                    },
                },
            },
        )

        self.assertFalse(result["valid"])
        self.assertEqual(
            {item["code"] for item in result["errors"]},
            {
                "completion.task_design_reentry_decision.reusable_artifacts",
                "completion.task_design_reentry_decision.invalidated_artifacts",
                "completion.task_design_reentry_decision.distribution_action",
                "completion.task_design_reentry_decision.review_distribution_action",
            },
        )

    def test_context_ledger_feedback_reentry_requires_cache(self):
        packet = {
            "stage_name": "context-ledger",
            "context_packet_version": 1,
            "consumed_context_revision": 2,
            "context_delta": {"approved_facts": ["reuse design"]},
            "new_artifact_refs": ["artifact:context"],
            "new_evidence_refs": ["evidence:context"],
            "stage_pass_ref": "stage_pass:context-ledger:2",
            "next_owner": "task-distributor",
            "context_packet": {
                "task_design_reentry_decision": {
                    "action": "skip_to_distribution",
                    "task_design_ref": "artifact:task_design.md",
                    "reusable_artifacts": ["artifact:task_design.md"],
                    "invalidated_artifacts": ["artifact:execution_plan"],
                    "distribution_action": "revise_execution_plan",
                    "review_distribution_action": "reuse_review_criteria",
                    "reason": "Only distribution must change.",
                }
            },
        }

        result = validate_stage_packet("context-ledger", packet, current_revision=2)
        self.assertFalse(result["valid"])
        self.assertIn("reentry_cache.shape", {item["code"] for item in result["errors"]})

    def test_next_stage_guidance_covers_feedback_and_final_handoffs(self):
        feedback_packet = {
            "stage_name": "feedbackgate",
            "context_packet_version": 1,
            "consumed_context_revision": 4,
            "context_delta": {"approved_facts": ["feedback"]},
            "new_artifact_refs": ["artifact:feedback"],
            "new_evidence_refs": ["evidence:feedback"],
            "stage_pass_ref": "stage_pass:feedbackgate:1",
            "next_owner": "orchestrator",
            "judgment_envelope": {"feedback_required": True},
        }
        feedback_result = validate_stage_packet("feedbackgate", feedback_packet, current_revision=4)
        self.assertTrue(feedback_result["valid"], feedback_result)
        self.assertEqual(feedback_result["next_stage"]["owner"], "orchestrator")
        self.assertEqual(feedback_result["next_stage"]["activation_ref"], "$orchestrator")
        self.assertEqual(feedback_result["next_stage"]["contract_ref"], "skills/orchestrator/contract.json")
        self.assertEqual(feedback_result["next_stage"]["required_external_mcp_tools"], ["MCP_DOCKER.sequentialthinking"])
        self.assertIn("sequential_thinking_ref_or_waiver", feedback_result["next_stage"]["required_sections"])

        final_packet = {
            **feedback_packet,
            "next_owner": "final",
            "judgment_envelope": {"feedback_required": False},
        }
        final_result = validate_stage_packet("feedbackgate", final_packet, current_revision=4)
        self.assertTrue(final_result["valid"], final_result)
        self.assertEqual(final_result["next_stage"], build_next_stage_guidance("final"))
        self.assertEqual(final_result["next_stage"]["required_input_artifacts"], ["judgment_envelope", "feedback_gate_evidence"])

    def test_orchestrator_can_route_simple_tasks_to_direct_workflow(self):
        packet = {
            "stage_name": "orchestrator",
            "context_packet_version": 1,
            "consumed_context_revision": 0,
            "stage_execution_mode": "main_agent_role_pass",
            "context_delta": {"approved_facts": ["simple task can stay direct"]},
            "new_artifact_refs": ["artifact:orchestration_request"],
            "new_evidence_refs": ["stage_pass:orchestrator:1", "mcp:sequentialthinking:orchestrator"],
            "stage_pass_ref": "stage_pass:orchestrator:1",
            "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:orchestrator",
            "architecture_required": False,
            "workflow_mode": "express-direct",
            "next_owner": "direct-workflow",
            "orchestration_request": {
                "architecture_required": False,
                "workflow_mode": "express-direct",
                "complexity_classification": "simple",
                "direct_workflow_scope": {
                    "allowed_actions": ["normal implementation"],
                    "excluded_actions": ["specialist fanout"],
                    "cleanup_actions": ["delete the local PR branch after publishing"],
                },
                "express_direct_reason": "Single-file direct fix does not need design/distribution fanout.",
                "stage_pass_ref": "stage_pass:orchestrator:1",
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:orchestrator",
                "context_delta": {"approved_facts": ["simple task can stay direct"]},
                "new_artifact_refs": ["artifact:orchestration_request"],
                "new_evidence_refs": ["stage_pass:orchestrator:1"],
                "next_owner": "direct-workflow",
            },
        }

        result = validate_stage_packet("orchestrator", packet, current_revision=0)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["expected_next_owner"], "direct-workflow")
        self.assertEqual(result["next_stage"]["owner"], "direct-workflow")
        self.assertEqual(result["next_stage"]["activation_ref"], None)
        self.assertEqual(result["next_stage"]["required_mcp_tools"], [])
        self.assertIn("normal direct workflow", result["next_stage"]["action"])
        self.assertIn(
            "cleanup_actions",
            result["next_stage"]["stage_packet_template"]["orchestration_request"]["direct_workflow_scope"],
        )

        invalid = validate_stage_packet(
            "orchestrator",
            {
                **packet,
                "architecture_required": True,
                "orchestration_request": {
                    **packet["orchestration_request"],
                    "architecture_required": True,
                },
            },
            current_revision=0,
        )
        self.assertFalse(invalid["valid"], invalid)
        self.assertIn("handoff.next_owner", {item["code"] for item in invalid["errors"]})

        missing_express_fields = validate_stage_packet(
            "orchestrator",
            {
                **packet,
                "orchestration_request": {
                    "architecture_required": False,
                    "workflow_mode": "express-direct",
                    "complexity_classification": "simple",
                    "stage_pass_ref": "stage_pass:orchestrator:1",
                    "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:orchestrator",
                    "context_delta": {"approved_facts": ["simple task can stay direct"]},
                    "new_artifact_refs": ["artifact:orchestration_request"],
                    "new_evidence_refs": ["stage_pass:orchestrator:1"],
                    "next_owner": "direct-workflow",
                },
            },
            current_revision=0,
        )
        self.assertFalse(missing_express_fields["valid"], missing_express_fields)
        self.assertIn("express_direct.scope_shape", {item["code"] for item in missing_express_fields["errors"]})
        self.assertIn("express_direct.reason", {item["code"] for item in missing_express_fields["errors"]})

        missing_cleanup_actions = validate_stage_packet(
            "orchestrator",
            {
                **packet,
                "orchestration_request": {
                    **packet["orchestration_request"],
                    "direct_workflow_scope": {
                        "allowed_actions": ["normal implementation"],
                        "excluded_actions": ["specialist fanout"],
                    },
                },
            },
            current_revision=0,
        )
        self.assertFalse(missing_cleanup_actions["valid"], missing_cleanup_actions)
        self.assertIn(
            "orchestration_request.direct_workflow_scope.cleanup_actions.missing",
            {item["code"] for item in missing_cleanup_actions["errors"]},
        )

        malformed_scope = validate_stage_packet(
            "orchestrator",
            {
                **packet,
                "orchestration_request": {
                    **packet["orchestration_request"],
                    "direct_workflow_scope": {
                        "allowed_actions": ["normal implementation", ""],
                        "excluded_actions": [],
                        "cleanup_actions": ["delete the local PR branch after publishing"],
                    },
                },
            },
            current_revision=0,
        )
        self.assertFalse(malformed_scope["valid"], malformed_scope)
        self.assertIn(
            "orchestration_request.direct_workflow_scope.allowed_actions.item",
            {item["code"] for item in malformed_scope["errors"]},
        )
        self.assertIn(
            "orchestration_request.direct_workflow_scope.excluded_actions.missing",
            {item["code"] for item in malformed_scope["errors"]},
        )

        malformed_shapes = validate_stage_packet(
            "orchestrator",
            {
                **packet,
                "orchestration_request": "not an object",
            },
            current_revision=0,
        )
        self.assertFalse(malformed_shapes["valid"], malformed_shapes)
        self.assertIn("express_direct.request_shape", {item["code"] for item in malformed_shapes["errors"]})

        malformed_types = validate_stage_packet(
            "orchestrator",
            {
                **packet,
                "orchestration_request": {
                    **packet["orchestration_request"],
                    "direct_workflow_scope": "not an object",
                    "express_direct_reason": ["not", "a", "string"],
                },
            },
            current_revision=0,
        )
        self.assertFalse(malformed_types["valid"], malformed_types)
        self.assertIn("express_direct.scope_shape", {item["code"] for item in malformed_types["errors"]})
        self.assertIn("express_direct.reason", {item["code"] for item in malformed_types["errors"]})

    def test_next_stage_guidance_includes_valid_packet_templates(self):
        orchestrator_guidance = build_next_stage_guidance("orchestrator")
        orchestrator_template = orchestrator_guidance["stage_packet_template"]
        self.assertEqual(orchestrator_template["stage_name"], "orchestrator")
        self.assertIn("orchestration_request", orchestrator_template)
        self.assertIn("sequential_thinking_ref", orchestrator_template)
        self.assertEqual(orchestrator_template["next_owner"], "context-ledger")

        context_guidance = build_next_stage_guidance("context-ledger")
        context_template = context_guidance["stage_packet_template"]
        self.assertEqual(context_template["stage_name"], "context-ledger")
        self.assertIn("context_packet", context_template)
        self.assertIn("context_delta", context_template)
        self.assertEqual(context_template["context_packet"]["next_owner"], "task-designer")

        design_guidance = build_next_stage_guidance("task-designer")
        design_template = design_guidance["stage_packet_template"]
        self.assertEqual(design_template["stage_name"], "task-designer")
        self.assertIn("task_design", design_template)
        self.assertIsInstance(design_template["task_design"]["distribution_boundaries"], list)
        self.assertEqual(design_template["task_design"]["artifact_profile"]["version"], 1)
        for option in design_template["task_design"]["options"]:
            self.assertIn("title", option)
            self.assertIn("fit_assessment", option)
            self.assertIn("tradeoffs", option)

    def test_minimal_packets_for_all_mandatory_stages(self):
        cases = {
            "orchestrator": {
                "next_owner": "context-ledger",
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:orchestrator",
                "orchestration_request": {"scope": "unit"},
            },
            "context-ledger": {
                "next_owner": "task-designer",
                "context_packet": {"approved_facts": []},
            },
            "task-designer": {
                "next_owner": "task-distributor",
                "task_design": {
                    "problem_definition": "unit design",
                    "assumptions": ["unit"],
                    "options": [
                        {"id": "option-1", "title": "A", "summary": "A", "fit_assessment": "ok", "tradeoffs": ["x"]},
                        {"id": "option-2", "title": "B", "summary": "B", "fit_assessment": "best", "tradeoffs": ["y"]},
                        {"id": "option-3", "title": "C", "summary": "C", "fit_assessment": "too much", "tradeoffs": ["z"]},
                    ],
                    "comparison_criteria": ["fit"],
                    "selected_option_id": "option-2",
                    "selection_rationale": "best fit",
                    "selected_option_risks": ["unit risk"],
                    "distribution_boundaries": ["no redesign"],
                    "artifact_profile": _artifact_profile("task-designer"),
                    "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:task-designer",
                },
            },
            "task-distributor": {
                "next_owner": "worker",
                "execution_plan": {
                    "selected_task_design_ref": "artifact:task_design.md",
                    "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
                    "artifact_profile": _artifact_profile("task-distributor"),
                    "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:task-distributor",
                    "distribution_principles": ["bounded fanout"],
                    "fanout_budget": {"max_worker_lanes": 2},
                    "worker_lanes": [
                        {
                            "lane_id": "worker-1",
                            "purpose": "unit worker",
                            "specialist_category": "test-automator",
                            "input_artifacts": ["artifact:task_design.md"],
                            "expected_outputs": ["tests"],
                            "handoff_evidence": ["wait_agent_evidence"],
                        }
                    ],
                    "dependencies": [],
                },
            },
            "worker": {
                "next_owner": "review-distributor",
                "worker_handoff_results": [],
            },
            "review-distributor": {
                "next_owner": "review",
                "review_plan": {
                    "worker_handoff_results_ref": "artifact:worker_handoffs.json",
                    "review_distribution_criteria_ref": "artifact:review_distribution_criteria.md",
                    "artifact_profile": _artifact_profile("review-distributor"),
                    "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:review-distributor",
                    "review_principles": ["review actual worker evidence"],
                    "coverage_contract": {"requires_specialist_reviewers": True},
                    "review_lanes": [
                        {
                            "lane_id": "review-1",
                            "purpose": "unit review",
                            "reviewer_category": "code-reviewer",
                            "input_artifacts": ["artifact:worker_handoffs.json"],
                            "required_findings": ["bugs"],
                            "handoff_evidence": ["wait_agent_evidence"],
                        }
                    ],
                },
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

    def test_canonical_skill_flow_accepts_sequential_waivers(self):
        waiver = _sequential_thinking_waiver()

        def base(stage_name: str, revision: int, next_owner: str) -> dict:
            return {
                "stage_name": stage_name,
                "context_packet_version": 1,
                "consumed_context_revision": revision,
                "context_delta": {"approved_facts": [stage_name]},
                "new_artifact_refs": [f"artifact:{stage_name}"],
                "new_evidence_refs": [f"evidence:{stage_name}"],
                "stage_pass_ref": f"stage_pass:{stage_name}:1",
                "next_owner": next_owner,
            }

        completed: list[str] = []
        flow = [
            (
                "orchestrator",
                {
                    **base("orchestrator", 0, "context-ledger"),
                    "orchestration_request": {"scope": "unit"},
                    "sequential_thinking_waiver": waiver,
                },
            ),
            (
                "context-ledger",
                {
                    **base("context-ledger", 1, "task-designer"),
                    "context_packet": {"approved_facts": []},
                },
            ),
            (
                "task-designer",
                {
                    **base("task-designer", 2, "task-distributor"),
                    "task_design": {
                        "problem_definition": "unit design",
                        "assumptions": ["unit"],
                        "options": [
                            {"id": "option-1", "title": "A", "summary": "A", "fit_assessment": "ok", "tradeoffs": ["x"]},
                            {"id": "option-2", "title": "B", "summary": "B", "fit_assessment": "best", "tradeoffs": ["y"]},
                            {"id": "option-3", "title": "C", "summary": "C", "fit_assessment": "too much", "tradeoffs": ["z"]},
                        ],
                        "comparison_criteria": ["fit"],
                        "selected_option_id": "option-2",
                        "selection_rationale": "best fit",
                        "selected_option_risks": ["unit risk"],
                        "distribution_boundaries": ["no redesign"],
                        "artifact_profile": _artifact_profile("task-designer"),
                        "sequential_thinking_waiver": waiver,
                    },
                },
            ),
            (
                "task-distributor",
                {
                    **base("task-distributor", 3, "worker"),
                    "execution_plan": {
                        "selected_task_design_ref": "artifact:task_design.md",
                        "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
                        "artifact_profile": _artifact_profile("task-distributor"),
                        "sequential_thinking_waiver": waiver,
                        "distribution_principles": ["bounded fanout"],
                        "fanout_budget": {"max_worker_lanes": 1},
                        "worker_lanes": [
                            {
                                "lane_id": "worker-1",
                                "purpose": "unit worker",
                                "specialist_category": "test-automator",
                                "input_artifacts": ["artifact:task_design.md"],
                                "expected_outputs": ["tests"],
                                "handoff_evidence": ["wait_agent_evidence"],
                            }
                        ],
                        "dependencies": [],
                    },
                },
            ),
            (
                "worker",
                {
                    **base("worker", 4, "review-distributor"),
                    "worker_handoff_results": [],
                    "missing_lane_classifications": [{"lane_id": "worker-1", "reason": "self-test no child spawn"}],
                },
            ),
            (
                "review-distributor",
                {
                    **base("review-distributor", 5, "review"),
                    "review_plan": {
                        "worker_handoff_results_ref": "artifact:worker_handoffs.json",
                        "review_distribution_criteria_ref": "artifact:review_distribution_criteria.md",
                        "artifact_profile": _artifact_profile("review-distributor"),
                        "sequential_thinking_waiver": waiver,
                        "review_principles": ["review actual worker evidence"],
                        "coverage_contract": {"requires_specialist_reviewers": True},
                        "review_lanes": [
                            {
                                "lane_id": "review-1",
                                "purpose": "unit review",
                                "reviewer_category": "code-reviewer",
                                "input_artifacts": ["artifact:worker_handoffs.json"],
                                "required_findings": ["bugs"],
                                "handoff_evidence": ["wait_agent_evidence"],
                            }
                        ],
                    },
                },
            ),
            (
                "review",
                {
                    **base("review", 6, "feedbackgate"),
                    "review_handoff_results": [],
                    "review_waivers": [{"lane_id": "review-1", "reason": "self-test no child spawn"}],
                },
            ),
            (
                "feedbackgate",
                {
                    **base("feedbackgate", 7, "final"),
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": {"self_test": True},
                    "review_waivers": [{"lane_id": "review-1", "reason": "self-test no child spawn"}],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
            ),
        ]

        expected_next = {
            "orchestrator": "context-ledger",
            "context-ledger": "task-designer",
            "task-designer": "task-distributor",
            "task-distributor": "worker",
            "worker": "review-distributor",
            "review-distributor": "review",
            "review": "feedbackgate",
            "feedbackgate": "final",
        }
        for stage_name, packet in flow:
            with self.subTest(stage_name=stage_name):
                result = validate_stage_packet(
                    stage_name,
                    packet,
                    current_revision=packet["consumed_context_revision"],
                    completed_stages=completed,
                )
                self.assertTrue(result["valid"], result)
                self.assertEqual(result["next_stage"]["owner"], expected_next[stage_name])
                if stage_name in {"worker", "review", "feedbackgate"}:
                    completion = validate_stage_completion(stage_name, packet)
                    self.assertTrue(completion["valid"], completion)
                completed.append(stage_name)

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

    def test_feedbackgate_feedback_requires_task_design_reentry_decision(self):
        missing = validate_stage_completion(
            "feedbackgate",
            {
                "stage_name": "feedbackgate",
                "judgment_envelope": {"feedback_required": True},
            },
        )
        self.assertFalse(missing["valid"])
        self.assertIn(
            "completion.task_design_reentry_decision.shape",
            {item["code"] for item in missing["errors"]},
        )

        valid = validate_stage_completion(
            "feedbackgate",
            {
                "stage_name": "feedbackgate",
                "judgment_envelope": {
                    "feedback_required": True,
                    "task_design_reentry_decision": {
                        "action": "reuse_task_design",
                        "task_design_ref": "artifact:task_design.md",
                        "reusable_artifacts": ["artifact:task_design.md"],
                        "invalidated_artifacts": ["artifact:execution_plan"],
                        "distribution_action": "revise_execution_plan",
                        "review_distribution_action": "reuse_review_criteria",
                        "reason": "Feedback only affects worker implementation, not design assumptions.",
                    },
                },
            },
        )
        self.assertTrue(valid["valid"], valid)

    def test_context_ledger_can_route_feedback_reentry_past_task_designer(self):
        packet = {
            "stage_name": "context-ledger",
            "context_packet_version": 1,
            "consumed_context_revision": 2,
            "context_delta": {"approved_facts": ["reuse design"]},
            "new_artifact_refs": ["artifact:context"],
            "new_evidence_refs": ["evidence:context"],
            "stage_pass_ref": "stage_pass:context-ledger:2",
            "next_owner": "task-distributor",
            "context_packet": {
                "task_design_reentry_decision": {
                    "action": "skip_to_distribution",
                    "task_design_ref": "artifact:task_design.md",
                    "reusable_artifacts": ["artifact:task_design.md"],
                    "invalidated_artifacts": ["artifact:execution_plan"],
                    "distribution_action": "revise_execution_plan",
                    "review_distribution_action": "reuse_review_criteria",
                    "reason": "Only distribution must change.",
                },
                "reentry_cache": {
                    "task_design_ref": "artifact:task_design.md",
                    "reusable_artifacts": ["artifact:task_design.md"],
                    "invalidated_artifacts": ["artifact:execution_plan"],
                    "distribution_action": "revise_execution_plan",
                    "review_distribution_action": "reuse_review_criteria",
                },
            },
        }

        result = validate_stage_packet("context-ledger", packet, current_revision=2)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["expected_next_owner"], "task-distributor")

    def test_stage_completion_matrix_separates_schema_from_readiness(self):
        matrix = [
            (
                "worker",
                {"stage_name": "worker", "worker_handoff_results": [{}]},
                True,
                set(),
            ),
            (
                "worker",
                {
                    "stage_name": "worker",
                    "worker_handoff_results": [],
                    "missing_lane_classifications": [{"lane_id": "worker-1", "reason": "thread_limit_reached"}],
                },
                True,
                set(),
            ),
            (
                "worker",
                {"stage_name": "worker", "worker_handoff_results": []},
                False,
                {"completion.worker_lanes_missing"},
            ),
            (
                "worker",
                {
                    "stage_name": "worker",
                    "worker_handoff_results": [],
                    "missing_lane_classifications": [{"lane_id": "", "reason": "thread_limit_reached"}],
                },
                False,
                {"completion.missing_lane_classifications.lane_id", "completion.worker_lanes_missing"},
            ),
            (
                "worker",
                {
                    "stage_name": "worker",
                    "worker_handoff_results": [],
                    "missing_lane_classifications": "not-a-list",
                },
                False,
                {"completion.missing_lane_classifications.shape", "completion.worker_lanes_missing"},
            ),
            (
                "review",
                {"stage_name": "review", "review_handoff_results": [{}]},
                True,
                set(),
            ),
            (
                "review",
                {
                    "stage_name": "review",
                    "review_handoff_results": [],
                    "review_waivers": [{"lane_id": "review-1", "reason": "covered_by_policy"}],
                },
                True,
                set(),
            ),
            (
                "review",
                {"stage_name": "review", "review_handoff_results": []},
                False,
                {"completion.review_lanes_missing"},
            ),
            (
                "review",
                {
                    "stage_name": "review",
                    "review_handoff_results": [],
                    "review_waivers": [{"lane_id": "review-1", "reason": ""}],
                },
                False,
                {"completion.review_waivers.reason", "completion.review_lanes_missing"},
            ),
            (
                "review",
                {
                    "stage_name": "review",
                    "review_handoff_results": [],
                    "review_waivers": "not-a-list",
                },
                False,
                {"completion.review_waivers.shape", "completion.review_lanes_missing"},
            ),
            (
                "feedbackgate",
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": {"review_inputs_present": True},
                    "review_input_refs": ["review:1"],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
                True,
                set(),
            ),
            (
                "feedbackgate",
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": {"review_inputs_present": True},
                    "review_waivers": [{"lane_id": "review-1", "reason": "covered_by_policy"}],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
                True,
                set(),
            ),
            (
                "feedbackgate",
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {
                        "feedback_required": True,
                        "task_design_reentry_decision": {
                            "action": "revise_task_design",
                            "reusable_artifacts": [],
                            "invalidated_artifacts": ["artifact:task_design.md"],
                            "distribution_action": "revise_execution_plan",
                            "review_distribution_action": "revise_review_plan",
                            "reason": "Design assumptions changed.",
                        },
                    },
                },
                True,
                set(),
            ),
            (
                "feedbackgate",
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": {"feedback_required": False},
                    "feedback_gate_evidence": {},
                    "review_input_refs": ["review:1"],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
                False,
                {"completion.feedback_gate_evidence_missing"},
            ),
            (
                "feedbackgate",
                {
                    "stage_name": "feedbackgate",
                    "judgment_envelope": "not-a-dict",
                    "feedback_gate_evidence": {"review_inputs_present": True},
                    "review_input_refs": ["review:1"],
                    "stage_passes": ["stage_pass:review:1"],
                    "active_passes": ["stage_pass:worker:1"],
                },
                False,
                {"completion.judgment_shape"},
            ),
        ]

        for stage_name, packet, expected_valid, expected_codes in matrix:
            with self.subTest(stage_name=stage_name, packet=packet):
                result = validate_stage_completion(stage_name, packet)
                self.assertEqual(result["valid"], expected_valid, result)
                self.assertEqual({item["code"] for item in result["errors"]}, expected_codes)

    def test_feedbackgate_completion_rejects_adversarial_evidence_corpus(self):
        base_packet = {
            "stage_name": "feedbackgate",
            "judgment_envelope": {"feedback_required": False},
            "feedback_gate_evidence": {"review_inputs_present": True},
            "review_input_refs": ["review:1"],
            "stage_passes": ["stage_pass:review:1"],
            "active_passes": ["stage_pass:worker:1"],
        }
        malformed_values = [None, "", 0, True, {}, [], [None], [""], ["valid", None]]
        expected_by_field = {
            "feedback_gate_evidence": {
                None: "completion.feedback_gate_evidence_missing",
                "": "completion.feedback_gate_evidence.shape",
                0: "completion.feedback_gate_evidence.shape",
                True: "completion.feedback_gate_evidence.shape",
                "dict": "completion.feedback_gate_evidence_missing",
                "list": "completion.feedback_gate_evidence.shape",
            },
            "review_input_refs": {
                None: "completion.review_inputs_missing",
                "": "completion.review_input_refs.shape",
                0: "completion.review_input_refs.shape",
                True: "completion.review_input_refs.shape",
                "dict": "completion.review_input_refs.shape",
                "list": "completion.review_inputs_missing",
            },
            "stage_passes": {
                None: "completion.stage_passes_missing",
                "": "completion.stage_passes.shape",
                0: "completion.stage_passes.shape",
                True: "completion.stage_passes.shape",
                "dict": "completion.stage_passes.shape",
                "list": "completion.stage_passes_missing",
            },
            "active_passes": {
                None: "completion.active_passes_missing",
                "": "completion.active_passes.shape",
                0: "completion.active_passes.shape",
                True: "completion.active_passes.shape",
                "dict": "completion.active_passes.shape",
                "list": "completion.active_passes_missing",
            },
        }

        def expected_key(value):
            if value == {}:
                return "dict"
            if isinstance(value, list):
                return "list"
            return value

        for field_name, expected_codes in expected_by_field.items():
            for malformed_value in malformed_values:
                with self.subTest(field_name=field_name, malformed_value=malformed_value):
                    packet = {**base_packet, field_name: malformed_value}
                    result = validate_stage_completion("feedbackgate", packet)
                    self.assertFalse(result["valid"], result)
                    actual_codes = {item["code"] for item in result["errors"]}
                    self.assertIn(expected_codes[expected_key(malformed_value)], actual_codes)

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

    def test_design_distribution_stages_require_stage_specific_validation_in_sequence(self):
        cases = {
            "task-designer": "validate_task_design",
            "task-distributor": "validate_execution_plan",
            "review-distributor": "validate_review_plan",
        }

        for stage_name, validator_name in cases.items():
            with self.subTest(stage_name=stage_name, sequence="valid"):
                valid = validate_tool_sequence(
                    stage_name,
                    [
                        "read_context_packet",
                        "validate_context_revision",
                        "append_stage_pass",
                        "validate_stage_packet",
                        validator_name,
                        "write_context_packet",
                        "record_mcp_quiescence",
                        "validate_tool_sequence",
                    ],
                )
                self.assertTrue(valid["valid"], valid)

            with self.subTest(stage_name=stage_name, sequence="missing_validator"):
                invalid = validate_tool_sequence(
                    stage_name,
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

    def test_materialized_stages_require_completion_validation_in_sequence(self):
        stages = ("worker", "review", "feedbackgate")
        valid_sequence = [
            "read_context_packet",
            "validate_context_revision",
            "append_stage_pass",
            "validate_stage_packet",
            "validate_stage_completion",
            "write_context_packet",
            "record_mcp_quiescence",
            "validate_tool_sequence",
        ]
        invalid_sequences = [
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_packet",
                "write_context_packet",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_completion",
                "validate_stage_packet",
                "write_context_packet",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
            [
                "read_context_packet",
                "validate_context_revision",
                "append_stage_pass",
                "validate_stage_packet",
                "write_context_packet",
                "validate_stage_completion",
                "record_mcp_quiescence",
                "validate_tool_sequence",
            ],
        ]

        for stage_name in stages:
            with self.subTest(stage_name=stage_name, sequence="valid"):
                valid = validate_tool_sequence(stage_name, valid_sequence)
                self.assertTrue(valid["valid"], valid)

            for sequence in invalid_sequences:
                with self.subTest(stage_name=stage_name, sequence=sequence):
                    invalid = validate_tool_sequence(stage_name, sequence)
                    self.assertFalse(invalid["valid"], invalid)
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
            ledger.record_tool_call("run-1", "task-distributor", "read_context_packet")
            ledger.record_tool_call("run-1", "task-distributor", "validate_context_revision")

            calls = ledger.list_tool_calls("run-1", "task-distributor")
            self.assertEqual([item["tool_name"] for item in calls], ["read_context_packet", "validate_context_revision"])

    def test_context_packet_tools_return_next_stage_guidance(self):
        from tempfile import TemporaryDirectory
        from context_ledger_mcp import server as mcp_server

        previous_db = os.environ.get("CODEX_CONTEXT_LEDGER_DB")
        with TemporaryDirectory() as temp_dir:
            os.environ["CODEX_CONTEXT_LEDGER_DB"] = f"{temp_dir}/ledger.sqlite"
            try:
                init = mcp_server.initialize_run("run-guidance", "test guidance", stage_name="orchestrator")
                self.assertTrue(init["ok"], init)

                packet = {
                    "stage_name": "task-distributor",
                    "next_owner": "worker",
                    "execution_plan": {
                        "selected_task_design_ref": "artifact:task_design.md",
                        "task_distribution_criteria_ref": "artifact:task_distribution_criteria.md",
                        "artifact_profile": _artifact_profile("task-distributor"),
                "sequential_thinking_ref": "mcp:MCP_DOCKER.sequentialthinking:task-distributor",
                        "distribution_principles": ["bounded fanout"],
                        "fanout_budget": {"max_worker_lanes": 2},
                        "worker_lanes": [
                            {
                                "lane_id": "worker-1",
                                "purpose": "unit worker",
                                "specialist_category": "test-automator",
                                "input_artifacts": ["artifact:task_design.md"],
                                "expected_outputs": ["tests"],
                                "handoff_evidence": ["wait_agent_evidence"],
                            }
                        ],
                        "dependencies": [],
                    },
                }
                write = mcp_server.write_context_packet(
                    "run-guidance",
                    packet,
                    expected_revision=0,
                    stage_name="task-distributor",
                )
                self.assertTrue(write["ok"], write)
                self.assertEqual(write["next_stage"]["owner"], "worker")
                self.assertEqual(write["next_stage"]["activation_ref"], "$worker")
                self.assertEqual(write["next_stage"]["contract_ref"], "skills/worker/contract.json")

                read = mcp_server.read_context_packet("run-guidance", stage_name="worker")
                self.assertTrue(read["ok"], read)
                self.assertEqual(read["next_stage"], write["next_stage"])
            finally:
                if previous_db is None:
                    os.environ.pop("CODEX_CONTEXT_LEDGER_DB", None)
                else:
                    os.environ["CODEX_CONTEXT_LEDGER_DB"] = previous_db

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
