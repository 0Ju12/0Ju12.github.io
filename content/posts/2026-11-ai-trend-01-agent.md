---
title: "AI 에이전트란 무엇인가 — LLM이 도구를 쥐고 반복할 때"
date: "2026-11-09"
summary: "에이전트를 '도구를 쓰며 스스로 다음 단계를 정하는 LLM 루프'로 정의하고, 워크플로와 무엇이 다른지, 기업 도입 숫자가 왜 엇갈리는지 정리했습니다."
tags: [AI 에이전트, LLM, 시스템 설계]
series: ai-trend
episode: 1
next_topic: "#2 Tool use — 모델은 함수를 실행하지 않는다"
---

> **한 줄 요약** — 에이전트는 "더 똑똑한 챗봇"이 아니라, LLM이 도구 호출 결과를 보고 다음 행동을 고르는 **반복 구조**입니다. 그래서 성능보다 먼저 "언제 멈추고, 무엇을 못 하게 할지"가 설계의 중심이 됩니다.

## 핵심 개념

- **정의**: Anthropic은 에이전트를 "LLM이 도구를 루프 안에서 자율적으로 사용하는 것"이라는 짧은 정의로 정리했습니다. 구성 요소는 셋입니다 — 판단하는 모델, 바깥 세계와 닿는 도구, 결과를 보고 다시 판단하는 루프.
- **워크플로와의 차이**: 같은 글에서 둘을 구분합니다. 워크플로는 사람이 짠 코드 경로를 따라 LLM과 도구가 움직이고, 에이전트는 **LLM이 직접 경로를 정합니다.**
- **비유**: 워크플로는 레시피대로 요리하는 주방 보조, 에이전트는 냉장고를 열어 보고 메뉴를 정하는 요리사입니다. 요리사는 유연하지만, 재료를 다 써 버리거나 엉뚱한 요리를 할 위험도 함께 커집니다.

## 지금 무슨 일이 일어나고 있나

- **도입 전망은 크고, 경고도 크다.** Gartner는 2025년 8월에 "2026년 말까지 기업용 앱의 40%가 업무 특화 에이전트를 탑재할 것(2025년 5% 미만)"이라고 전망했습니다. 같은 해 6월에는 "에이전트 AI 프로젝트의 40% 이상이 비용·불분명한 가치·위험 통제 부족으로 2027년 말까지 취소될 것"이라고도 했습니다. 두 숫자는 모순이라기보다, 많이 시도되고 많이 정리되는 단계라는 뜻으로 읽힙니다.
- **"자율성보다 신뢰성"으로 무게가 옮겨 가고 있습니다.** Gartner는 2026년 5월, 모든 에이전트에 같은 수준의 통제를 적용하면 실패한다며 에이전트의 권한·위험도에 따라 거버넌스를 달리하라고 권고했습니다.
- **비용도 현실적인 변수입니다.** Anthropic의 멀티 에이전트 리서치 시스템 글에 따르면 에이전트는 일반 채팅보다 토큰을 약 4배, 멀티 에이전트는 약 15배 씁니다.
- 참고로 "기업의 몇 %가 에이전트를 운영 중"이라는 수치는 조사마다 크게 다릅니다(어떤 곳은 절반 이상, 어떤 곳은 20%대). 측정 방식이 제각각이라 숫자 하나를 근거로 쓰지 않는 편이 안전합니다.

## 동작 구조

```
목표 ──▶ [LLM] 다음 행동 결정 ──▶ 도구 실행 (검색·DB·API·코드)
            ▲                            │
            └──── 결과 관찰 ◀────────────┘
   멈춤 조건: 목표 달성 · 최대 반복 횟수 · 금지된 행동 · 비용 한도
```

```python
for step in range(MAX_STEPS):            # 멈춤 조건이 코드에 있어야 한다
    action = llm.decide(goal, history)   # 모델은 '무엇을 할지'만 고른다
    if action.type == "finish":
        break
    if not policy.allows(action):        # 실행 전에 코드가 허용 여부를 판단
        history.append(("blocked", action)); continue
    result = tools[action.name](**action.args)
    history.append((action, result))
```

## 왜 중요한가 / 한계

- **중요한 이유**: 정해진 절차로 풀기 어려운 일(자료 조사, 코드 수정, 여러 시스템을 오가는 업무)을 사람이 매 단계 지시하지 않아도 진행할 수 있습니다.
- **한계**: 단계가 늘수록 오류가 쌓입니다. 한 단계 정확도가 높아도 열 단계를 이어 붙이면 전체 성공률은 크게 떨어집니다. 그래서 Anthropic도 "대부분은 단일 LLM 호출 + 검색 + 예시로 충분하다, 단순하게 시작하라"고 권합니다.
- **논쟁점**: "에이전트"라는 말이 단순한 챗봇이나 정해진 자동화에도 붙으면서 의미가 흐려졌습니다. 시스템을 설명할 때는 "누가 경로를 정하는가(코드냐 모델이냐)"로 구분하는 게 정확합니다.

## 내 프로젝트와 연결

- **관통 7 AI 프록시**는 엄밀히 말하면 에이전트가 아니라 **워크플로**입니다. Guardrail → 라우트 결정 → 모델 선택 → 생성의 순서를 코드가 정하고, 모델은 각 단계의 판단(적절한가, 텍스트냐 이미지냐, 쉬운가 어려운가)만 합니다. 판단 결과가 스키마를 벗어나면 진행하지 않고 막았습니다.
- **국보 RAG 가이드**는 LangGraph로 "검색 → 생성" 그래프를 만들었지만, 역시 경로는 고정이고 모델이 단 근거 번호를 코드가 검증합니다.
- 두 프로젝트 모두 "모델에게 경로까지 맡길 이유가 아직 없었다"는 판단이었고, 에이전트로 넘어간다면 위 의사코드의 `policy.allows`와 `MAX_STEPS`에 해당하는 부분부터 설계하겠습니다.

## 면접 질문

**Q. 에이전트와 일반적인 LLM 파이프라인의 차이를 설명하고, 언제 에이전트를 쓰겠습니까?**

> 파이프라인은 실행 순서를 코드가 정하고, 에이전트는 도구 결과를 본 모델이 다음 행동을 정합니다. 입력마다 필요한 단계가 달라서 미리 경로를 짤 수 없을 때 에이전트를 씁니다. 다만 단계가 늘수록 오류와 비용이 커지므로, 저는 먼저 고정된 파이프라인으로 풀어 보고, 그게 안 되는 지점에만 에이전트를 두며, 최대 반복 횟수와 허용 도구 목록을 코드로 제한합니다. 관통 7 프록시에서도 모델은 판단만 하고, 형식이 맞지 않으면 진행하지 않게 했습니다.

## 출처

- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- Gartner, [40% of enterprise apps will feature task-specific AI agents by 2026 (2025.08)](https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025) · [Over 40% of agentic AI projects will be canceled by end of 2027 (2025.06)](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027) · [Uniform governance across AI agents will lead to failure (2026.05)](https://www.gartner.com/en/newsroom/press-releases/2026-05-26-gartner-says-applying-uniform-governance-across-ai-agents-will-lead-to-enterprise-ai-agent-failure)
