---
name: docker-memory
description: Use Docker MCP Memory as an optional knowledge-graph helper. Use when the agent needs to search, record, or reuse durable cross-run observations without making memory use mandatory in architecture Markdown contracts.
---

# Docker Memory

Use this skill only when memory helps the current task. It is an optional helper, not a mandatory architecture gate.

## Contract Gate

Before using this optional helper, read the adjacent `contract.json` and preserve `mandatory_for_architecture_required=false`. Treat `source_docs`, `forbidden_outputs`, and `required_evidence` as guardrails. Docker Memory remains optional and is not enforced as an architecture gate.

## Tooling

Prefer Docker MCP Memory through `MCP_DOCKER`:

- If memory tools are not visible, activate the catalog server with `mcp_add {"name":"memory","activate":true}` when available.
- Search first with `search_nodes`.
- Read broad graph state with `read_graph` only when targeted search is insufficient.
- Record durable observations with `create_entities` only when the information is stable and reusable.

## Workflow

1. Define the memory question narrowly.
2. Search existing nodes before creating anything.
3. Use memory findings as supporting context, not as current-state proof when live verification is cheap.
4. When writing memory, store short observations with clear entity names and entity types.
5. Keep architecture facts separate from run-local state; `codex-context-ledger` remains the run-level source of truth.

## Hard Rules

- Do not force memory use from global Markdown contracts.
- Do not store secrets, private credentials, raw personal data, or large artifact contents.
- Do not treat memory as a substitute for MCP validation results, MCP session activation checks, or current CLI output.
- Do not overwrite or delete memory unless explicitly asked.
