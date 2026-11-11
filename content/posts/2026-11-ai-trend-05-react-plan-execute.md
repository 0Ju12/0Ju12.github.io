---
title: "ReAct와 Plan-and-Execute — 에이전트는 어떻게 계획하나"
date: "2026-11-11"
summary: "한 걸음마다 다시 생각하는 ReAct와, 먼저 계획을 세우고 실행하는 Plan-and-Execute의 차이를 비용·속도·실패 방식으로 비교했습니다. ReWOO·LLMCompiler 같은 변형과 코딩 에이전트의 plan mode까지 이어서 봅니다."
tags: [에이전트, ReAct, 계획]
series: ai-trend
episode: 5
next_topic: "#6 에이전트 메모리 — 대화가 끝나도 남는 것과 남기면 안 되는 것"
---

> **한 줄 요약** — 지난 네 회차는 에이전트가 **무엇을 부를 수 있는가**(도구, MCP, 다른 에이전트)였습니다. 이번에는 **어떤 순서로 부를지를 누가 언제 정하는가**입니다. ReAct는 한 걸음 갈 때마다 정하고, Plan-and-Execute는 출발 전에 정합니다. 둘의 차이는 성능보다 비용, 속도, 틀렸을 때의 모습에서 드러납니다.

## 핵심 개념

- **ReAct**(Yao 외, 2022): 생각(Thought) → 행동(Action) → 관찰(Observation)을 반복합니다. #1에서 본 에이전트 루프가 바로 이 형태입니다. 도구 결과를 볼 때마다 다음 행동을 새로 정하므로 예상 밖의 결과에 잘 적응합니다.
- **Plan-and-Execute**: 먼저 전체 단계를 목록으로 쓰고(planner), 단계별로 실행한 뒤(executor), 필요하면 계획을 고칩니다(replanner). 프롬프트 기법으로는 Plan-and-Solve(Wang 외, 2023)가 출발점입니다.
- **비유**: ReAct는 내비게이션 없이 교차로마다 표지판을 보고 방향을 정하는 운전입니다. 길이 막히면 바로 돌아갈 수 있지만 교차로마다 멈춥니다. Plan-and-Execute는 출발 전에 경로를 정하는 운전입니다. 빠르지만 경로를 정할 때 몰랐던 공사 구간을 만나면 다시 계획해야 합니다.

## 지금 무슨 일이 일어나고 있나

- **변형이 계획과 실행 사이를 채우고 있습니다.** LangChain은 계획형 에이전트를 세 가지로 정리합니다. 기본 Plan-and-Execute, 계획 안에 `#E1` 같은 변수를 두어 앞 단계 결과를 뒤 단계가 받아 쓰게 하는 **ReWOO**, 단계 사이 의존 관계를 그래프(DAG)로 만들어 서로 무관한 단계를 동시에 실행하는 **LLMCompiler**입니다. LLMCompiler 논문은 순차 실행보다 최대 3.6배 빠르다고 보고했는데, 논문의 실험 조건에서 나온 값입니다.
- **섞어 쓰는 구조가 흔해졌습니다.** 바깥은 계획으로 큰 단계를 나누고, 각 단계 안에서는 짧은 ReAct 루프를 돌리는 방식입니다. 2026년에 나온 비교 글들은 "구조화된 업무에서 계획형이 몇 점 앞선다"는 수치를 싣기도 하지만, 측정 방법을 확인할 수 없는 글이 많아 이 글에서는 수치를 옮기지 않습니다.
- **코딩 에이전트의 plan mode**: Claude Code 공식 문서는 plan mode를 권한 모드의 하나로 설명합니다. 이 모드에서는 코드를 읽고 계획만 쓰며, 사람이 계획을 승인하기 전에는 파일을 고치지 않습니다. 계획과 실행 사이에 **사람의 승인**을 넣은 Plan-and-Execute로 볼 수 있습니다.
- **추론 모델과의 관계**: 모델이 답하기 전에 길게 생각하고, 도구 호출 사이사이에도 생각을 이어 가는 방식(interleaved thinking)이 여러 제공사 문서에 등장합니다. 계획을 별도 단계로 떼지 않아도 모델 안에서 일부 이루어진다는 뜻인데, 이 주제는 #13(추론 모델)에서 따로 다룹니다.

## 동작 구조

```
ReAct                               Plan-and-Execute
─────                               ────────────────
생각 → 도구 → 관찰                   계획: [1, 2, 3, 4]      ← LLM 1회
생각 → 도구 → 관찰                   실행: 1 → 2 → 3 → 4      ← 단계마다 도구(필요하면 작은 LLM)
생각 → 도구 → 관찰                   점검: 끝났나? 다시 계획?   ← LLM 1회
생각 → 답
(걸음마다 큰 모델 호출,               (큰 모델 호출이 적음,
 지금까지의 기록을 매번 다시 읽음)     계획이 낡으면 통째로 틀림)
```

```python
# Plan-and-Execute 의 뼈대
plan = planner(goal)                       # ["회사 찾기", "댓글 수집", "분류", "요약"]
done = []
while plan:
    step = plan.pop(0)
    result = executor(step, context=done)  # 도구 호출 또는 작은 모델
    done.append((step, verify(result)))    # 단계 결과를 코드로 확인
    if needs_replan(done):                 # 결과가 없거나 전제가 깨졌을 때만
        plan = replanner(goal, done)       # 남은 계획을 다시 씀
answer = summarize(goal, done)
```

ReWOO는 위 계획을 `E1 = search("…")`, `E2 = summarize(#E1)`처럼 써서 실행 중에는 LLM을 다시 부르지 않습니다. LLMCompiler는 `E1`과 `E2`가 서로 무관하면 동시에 실행합니다.

| | ReAct | Plan-and-Execute |
|---|---|---|
| 큰 모델 호출 | 걸음마다 | 계획·재계획 때 |
| 지연 | 짧은 일에 유리 | 길고 병렬로 나눌 수 있는 일에 유리 |
| 강한 상황 | 다음 행동이 결과에 달린 탐색 | 단계가 미리 보이는 정형 업무 |
| 흔한 실패 | 같은 행동 반복, 목표에서 벗어남 | 낡은 전제로 끝까지 실행, 지나친 재계획 |
| 추적 | 기록이 길어 읽기 어려움 | 계획이 문서로 남아 검토 가능 |

## 왜 중요한가 / 한계

- **비용 구조가 달라집니다.** ReAct는 걸음마다 지금까지의 기록 전체를 다시 넣으므로 단계가 늘수록 토큰이 빠르게 늘어납니다. 계획형은 실행 단계를 작은 모델이나 코드에 맡길 수 있습니다.
- **계획은 검토할 수 있는 산출물입니다.** 실행 전에 사람이나 코드가 계획을 보고 막을 수 있습니다. plan mode가 이 점을 쓰는 예입니다.
- **한계 1 — 계획 시점의 정보 부족**: 계획을 세울 때는 도구 결과를 아직 모릅니다. 검색 결과가 0건이면 뒤 단계가 모두 의미가 없어집니다. 언제 다시 계획할지 조건을 코드로 정해 두어야 합니다.
- **한계 2 — 재계획의 양면**: 재계획이 없으면 틀린 길을 끝까지 가고, 너무 잦으면 계획을 세운 의미가 없습니다.
- **한계 3 — 어느 쪽이든 종료 조건은 따로 필요합니다.** 최대 단계 수, 같은 호출 반복 감지, 시간 제한 같은 장치는 모델이 아니라 코드에 있어야 합니다.

## 내 프로젝트와 연결

- **관통 4·5의 분석 파이프라인**은 수집 → LLM 분류 → 정제 → 요약의 순서를 제가 코드로 고정했습니다. 계획을 LLM이 아니라 사람이 세운 Plan-and-Execute에 해당하고, 각 단계의 LLM 출력은 코드로 다시 검증했습니다. 단계가 미리 정해지는 업무라면 계획을 모델에 맡기지 않는 편이 싸고 추적하기 쉽다는 것을 이때 경험했습니다.
- **국보 RAG 가이드**는 LangGraph로 검색 → 생성 → 근거 번호 검증을 노드로 나누고, 검증에 실패하면 정해진 경로로 되돌렸습니다. "다시 계획할 조건을 코드로 둔다"는 위 한계 1의 대응과 같은 구조입니다.
- 최근 만든 **data-agent**(MCP 서버)는 도구 설명에 "표 목록 확인 → 열 확인 → SQL 실행 → 답 검사" 순서를 적어 두었습니다. 다만 실제 LLM을 붙여 그 순서를 지키는지 평가하지는 않았습니다. ReAct로 두면 모델이 검사 단계를 건너뛸 수 있어서, 순서를 강제하려면 계획을 코드 쪽에 두는 것이 맞다고 봅니다.

## 면접 질문

**Q. ReAct와 Plan-and-Execute 중 무엇을 쓸지 어떻게 정하나요?**

> 다음 행동이 직전 결과에 달려 있으면 ReAct, 단계가 미리 보이면 Plan-and-Execute를 씁니다. ReAct는 걸음마다 큰 모델을 부르고 기록 전체를 다시 읽어서 단계가 많아지면 느리고 비쌉니다. 계획형은 큰 모델 호출이 적고 계획을 실행 전에 검토할 수 있지만, 계획할 때 몰랐던 결과가 나오면 통째로 틀립니다. 그래서 재계획 조건과 최대 단계 수를 코드로 정해 둡니다. 제 프로젝트에서는 단계가 고정된 분석 파이프라인은 순서를 코드로 고정하고, LLM은 각 단계 안의 판단에만 쓰되 출력은 코드로 다시 확인했습니다.

## 출처

- Yao 외, [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) (2022)
- Wang 외, [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091) (2023)
- Xu 외, [ReWOO: Decoupling Reasoning from Observations](https://arxiv.org/abs/2305.18323) (2023)
- Kim 외, [An LLM Compiler for Parallel Function Calling](https://arxiv.org/abs/2312.04511) (2023) — 3.6배 수치의 출처
- LangChain Blog, [Plan-and-Execute Agents](https://blog.langchain.com/planning-agents) — 세 가지 계획형 구조 정리
- Claude Code 문서, [Permission modes](https://code.claude.com/docs/en/permission-modes) — plan mode 설명
- DEV Community, [ReAct vs Plan-and-Execute: picking an agent loop in 2026](https://dev.to/gabrielanhaia/react-vs-plan-and-execute-picking-an-agent-loop-in-2026-gnk) — 실패 방식 정리 (2차 자료)
