# Handoff Templates

Use these templates as copy-ready envelopes. Replace placeholders instead of expanding the schema.

## Shared `handoff_result`

```yaml
handoff_result:
  sender: "<agent-role>"
  pass_id: "<pass-id>"
  parent_pass_id: "<parent-pass-id>"
  pass_status: "completed|blocked|needs-clarification"
  owned_scope: "<bounded scope>"
  artifact_summary: "<what was produced or learned>"
  evidence_refs:
    - "<file path, test name, command, log, or source>"
  confidence: "<low|medium|high: short rationale>"
  merge_point: "<where the caller should merge this>"
  context_packet_version: "<context version>"
  caller_signals:
    - "<blocker, contradiction, assumption, or follow-up>"
```

Use for any worker or reviewer return.

## Aggregator Packet

```yaml
aggregation_packet:
  sender: "aggregator"
  pass_id: "<pass-id>"
  parent_pass_id: "<parent-pass-id>"
  owned_scope: "<merged worker scope>"
  artifact_summary: "<normalized merge summary>"
  worker_returns:
    - pass_id: "<worker-pass-id>"
      status: "<completed|blocked|partial>"
      key_output: "<one-line result>"
      evidence_refs:
        - "<evidence ref>"
  contradictions:
    - "<conflict between worker outputs>"
  open_questions:
    - "<missing evidence or unresolved issue>"
  reviewer_hints:
    - "<what review should focus on>"
  merge_point: "review-router"
  context_packet_version: "<context version>"
```

Use after worker outputs are normalized and before review begins.

## Review Return Packet

```yaml
review_return:
  sender: "<reviewer-role>"
  pass_id: "<pass-id>"
  parent_pass_id: "<parent-pass-id>"
  owned_scope: "<review scope>"
  artifact_summary: "<what was reviewed>"
  findings:
    - severity: "<high|medium|low>"
      status: "<confirmed|likely|needs-validation>"
      issue: "<short finding>"
      evidence_refs:
        - "<evidence ref>"
  residual_risks:
    - "<risk that remains even if no confirmed bug was found>"
  missing_validation:
    - "<test or evidence that was not available>"
  recommended_decision: "<approve|refine|re-review>"
  merge_point: "meta-judge"
  context_packet_version: "<context version>"
```

Use for any reviewer handoff to `meta-judge`.

## Judgment Envelope

```yaml
judgment_envelope:
  loop_stage: "<context-sync|planning|execution|aggregation|review|judgment|refinement|complete>"
  decision: "<continue loop|request context refresh|request plan refinement|request worker refinement|request review refinement|respond to user|final output|complete>"
  next_owner: "<agent-role or user>"
  feedback_target: "<context-manager|task-planner|worker-layer|aggregator|review-router|review-layer|orchestrator|user|none>"
  context_packet_version: "<context version>"
  active_passes_summary: "<optional short summary>"
  rationale: "<why this decision is the smallest correct next move>"
```

Use once per judgment pass. If refinement is needed, send it back to `orchestrator`.
