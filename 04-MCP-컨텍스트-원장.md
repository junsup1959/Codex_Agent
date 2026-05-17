---
title: MCP 컨텍스트 원장 구조
updated: 2026-05-18
tags:
  - codex
  - mcp
  - context-ledger
aliases:
  - MCP Context Ledger
---

# MCP 컨텍스트 원장 구조

> [!summary]
> 현재 구조에서 context manager는 장기 상주 physical agent가 아니다. run/session context authority는 `codex-context-ledger` MCP다.

## 왜 MCP 원장으로 바뀌었나

이전 방식처럼 context-manager를 physical resident agent로 계속 유지하면 다음 문제가 생긴다.

- loop마다 context owner가 중복될 수 있다.
- physical child agent 수가 늘어 fanout budget을 압박한다.
- context state가 대화 기억에 묻혀 validator가 보기 어려워진다.
- stage pass와 artifact ref가 흩어진다.

그래서 현재 구조는 `context_ledger_mcp_required=true`를 둔다. context-manager role pass는 main agent가 수행하되, 상태는 MCP 원장에 기록한다.

## `codex-context-ledger`가 관리하는 것

| 항목 | 의미 |
| --- | --- |
| `run_id` | architecture-required run 식별자 |
| `loop_id` | feedback loop 식별자 |
| `loop_attempt` | 반복 횟수 |
| `context_packet` | 다음 role pass가 읽을 승인된 context |
| `context_revision` | context packet versioning |
| `context_authority_ref` | 이 packet의 권한 출처 |
| `role_pass_readiness` | 다음 stage가 실행 가능한지 여부 |
| `artifact_refs` | 생성/변경/검증된 artifact 참조 |
| `stage_passes` | stage artifact가 validator/gate를 통과한 기록 |
| `active_passes` | materialized child lane 상태 |
| `mcp_quiescence_snapshot` | MCP process cleanup 상태 |
| `stale_markers` | 오래되었거나 폐기된 정보 표시 |

## context-manager role pass

context-manager는 다음을 하지 않는다.

- lane planning
- worker routing
- aggregation
- review routing
- meta judgment
- final approval

context-manager는 다음만 한다.

1. orchestrator의 `orchestration_request`를 읽는다.
2. 현재 run ledger를 초기화하거나 갱신한다.
3. 승인된 사실, constraint, artifact inventory를 `context_packet`으로 정리한다.
4. stale marker를 붙인다.
5. 다음 role pass readiness를 기록한다.

## main-agent role pass와 context 관계

모든 main-agent role pass는 실행 전에 최신 `context_packet`을 읽어야 한다. 실행 후에는 새 evidence, artifact ref, blocker, stale finding을 ledger에 다시 기록해야 한다.

이 규칙 때문에 downstream stage는 대화 기억이 아니라 MCP-backed context revision을 기준으로 동작한다.

## Docker MCP 정책

architecture-required run에서는 MCP 사용 evidence 또는 명시적 waiver가 필요하다.

특히 다음 stage는 `MCP_DOCKER/sequentialthinking:success`가 요구된다.

- `orchestrator`
- `context-manager`
- `aggregator`
- `review-router`
- reviewer lanes
- `meta-judge`

주의할 점:

- standalone `sequentialthinking` evidence는 충분하지 않다.
- `Transport closed` 같은 error-shaped output은 성공 evidence가 아니다.
- inactive server나 unavailable tool도 성공 evidence가 아니다.
- 실패한 MCP 호출은 blocker 또는 waiver evidence다.

## Docker MCP Memory와의 차이

`codex-context-ledger`와 Docker MCP Memory는 다르다.

| 항목 | `codex-context-ledger` | Docker MCP Memory |
| --- | --- | --- |
| 용도 | run 단위 context authority | 장기 지식 그래프 helper |
| 필수 여부 | architecture-required에서 필수 | 선택 |
| 저장 대상 | context packet, stage pass, artifact ref | 재사용 가능한 관찰 |
| gate 대체 여부 | context authority 역할 | gate 대체 안 함 |
| skill | context-manager role pass에서 사용 | `$docker-memory` optional skill |

Docker Memory에 기록할 수 있는 것은 안정적이고 재사용 가능한 관찰이다. secret, raw personal data, 큰 artifact 본문, run-local truth를 저장하면 안 된다.

## MCP quiescence

handoff 전에 각 stage owner는 MCP session/process를 정리하고 `mcp_quiescence_snapshot`을 붙여야 한다.

필수 형태:

```json
{
  "open_mcp_process_count": 0,
  "open_mcp_process_ids": [],
  "cleanup_status": "clean",
  "snapshot_at": "<timestamp>"
}
```

`open_mcp_process_count`가 0이 아니거나 snapshot이 누락되면 handoff/final approval이 막힌다.
