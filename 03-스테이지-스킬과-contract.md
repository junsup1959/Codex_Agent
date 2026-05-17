---
title: 스테이지 스킬과 contract 구조
updated: 2026-05-18
tags:
  - codex
  - skills
  - contracts
aliases:
  - Stage Skills And Contracts
---

# 스테이지 스킬과 contract 구조

> [!summary]
> 현재 구조는 skill을 단순 지침 파일로만 두지 않는다. 각 필수 stage skill 옆에 `contract.json`을 두고, validator가 이를 읽어 drift를 잡는다.

## 필수 stage skill 목록

architecture-required control flow에서 필수인 skill은 다음 7개다.

| Skill | Stage owner | 기본 실행 방식 | 핵심 output |
| --- | --- | --- | --- |
| `$orchestrator` | `orchestrator` | `main_agent_role_pass` | `orchestration_request` |
| `$task-planner` | `task-planner` | `main_agent_role_pass` | `execution_plan` |
| `$worker-router` | `worker-router` | `main_agent_role_pass` | worker `launch_manifest` |
| `$task-distributor` | `task-distributor` | `main_agent_role_pass` | `active_passes`, `handoff_results` |
| `$result-aggregator` | `aggregator` | `main_agent_role_pass` | `aggregation_packet` |
| `$review-router` | `review-router` | `main_agent_role_pass` | review `launch_manifest` |
| `$feedback-synthesizer` | `meta-judge` | `main_agent_role_pass` | `judgment_envelope`, `feedback_gate_evidence` |

선택 helper:

| Skill | 필수 여부 | 용도 |
| --- | --- | --- |
| `$docker-memory` | 필수 아님 | Docker MCP Memory를 장기 지식 그래프 보조로 사용할 때만 활성화 |

## 폴더 구조

각 skill은 보통 다음 구조를 가진다.

```text
${CODEX_HOME}\skills\<skill-name>\
  SKILL.md
  contract.json
  agents\openai.yaml
```

`SKILL.md`는 사람이 읽는 절차다. `contract.json`은 validator가 읽는 구조화된 계약이다. `agents/openai.yaml`은 skill 등록/노출을 위한 metadata 계층이다.

## Contract Gate

각 stage skill에는 `Contract Gate`가 들어 있다. 실행자는 skill을 수행하기 전에 인접한 `contract.json`을 읽어야 한다.

Contract Gate에서 확인할 항목:

- `input_artifacts`: stage 시작 전에 읽어야 하는 artifact
- `output_artifacts`: 이 stage가 만들 수 있는 artifact
- `forbidden_outputs`: 이 stage가 절대 만들면 안 되는 artifact
- `required_evidence`: handoff 전에 붙여야 하는 evidence
- `source_docs`: 참조해야 할 architecture MD 파일

이 구조의 목적은 자연어 skill과 Python validator 사이에 중복된 진실을 만들지 않는 것이다. 사람이 실행할 절차는 `SKILL.md`에 있고, 기계가 검사할 계약은 `contract.json`에 있다.

## contract.json 필드 의미

| 필드 | 설명 |
| --- | --- |
| `schema_version` | 현재 1 |
| `skill_name` | skill 폴더명 및 `SKILL.md` frontmatter name과 같아야 함 |
| `activation_ref` | `$orchestrator` 같은 호출 이름 |
| `mandatory_for_architecture_required` | architecture-required loop에서 필수인지 여부 |
| `stage_owner` | canonical stage owner |
| `stage_execution_mode` | 기본 실행 방식 |
| `purpose` | stage 책임 |
| `input_artifacts` | 입력 artifact 목록 |
| `output_artifacts` | 출력 artifact 목록 |
| `forbidden_outputs` | stage 책임 밖의 출력 목록 |
| `required_evidence` | 필요한 evidence 목록 |
| `source_docs` | 참조할 architecture docs |

## 필수 skill별 책임

### `$orchestrator`

사용자 요청을 architecture-required 여부로 분류하고, scope, constraints, success criteria, risk, feedback carryover를 정리한다. output은 `orchestration_request`다.

중요한 금지:

- context packet을 만들지 않는다.
- execution plan을 만들지 않는다.
- final readiness를 주장하지 않는다.

### `$task-planner`

현재 `context_packet`을 bounded `execution_plan`으로 바꾼다. worker lane 후보, ownership, expected artifact, validation prompt, review hint를 정한다.

중요한 금지:

- launch manifest를 만들지 않는다.
- worker를 spawn하지 않는다.
- aggregation이나 judgment를 수행하지 않는다.

### `$worker-router`

`execution_plan`을 worker `launch_manifest`로 변환한다. 이때 specialist list gate가 핵심이다. 반드시 `${CODEX_HOME}\agents\<category>\*.toml` catalog를 기준으로 concrete role을 선택한다.

중요한 금지:

- `spawn_agent` 호출 금지
- `active_passes` 생성 금지
- generic `worker` role 남발 금지

### `$task-distributor`

router가 만든 `launch_manifest`를 실제 child agent 실행으로 materialize한다. worker wave와 reviewer wave 모두에서 사용된다.

중요한 책임:

- fanout budget 준수
- `spawn_receipt_ref` 기록
- `wait_agent` evidence 확보
- timed out, failed, schema-invalid, blocked lane 분류

### `$result-aggregator`

worker 결과를 하나의 `aggregation_packet`으로 정규화한다. missing lane, contradiction, blocker를 숨기면 안 된다.

### `$review-router`

aggregation packet의 risk axis와 review hint를 보고 reviewer manifest를 만든다. worker router와 마찬가지로 specialist list를 다시 enumerate한다.

### `$feedback-synthesizer`

meta-judge stage 주변의 evidence를 정리한다. final output을 직접 허용하는 것이 아니라, `judgment_envelope`과 `feedback_gate_evidence`가 final을 허용하는지 판단한다.

## `$docker-memory`의 경계

`$docker-memory`는 optional helper다. contract에 `mandatory_for_architecture_required=false`가 있어야 한다.

이 skill은 다음을 대체하지 않는다.

- `codex-context-ledger`
- runtime validator
- feedback gate
- reviewer evidence
- 현재 CLI/MCP 검증

Memory는 장기 관찰을 찾거나 기록할 때만 쓴다. run-local truth는 context ledger가 가진다.
