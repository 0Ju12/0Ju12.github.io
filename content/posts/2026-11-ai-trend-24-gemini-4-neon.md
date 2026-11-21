---
title: "11/18 Google Gemini 4 Neon — '깊은 분석' 자리의 새 모델과, 사이버 변형을 따로 여는 방식"
date: "2026-11-21"
summary: "Google이 11월 18일 Gemini 4 Neon을 공개했습니다. 빠른 모델과 장시간 작업용 모델 사이에 놓인 위치, 생각 수준·가격·캐시 할인, 그리고 사이버 변형은 검증된 방어자에게만 따로 여는 조건을 #22의 OpenAI 사례와 비교했습니다."
tags: [이슈 분석, LLM, AI 안전]
series: ai-trend
episode: 24
next_topic: "#25 이슈 분석 — 다음 주 AI 뉴스"
---

> **한 줄 요약** — #22에서는 OpenAI가 사이버보안 능력이 높은 모델을 내놓으면서 위험한 보안 작업을 승인된 사용자에게만 여는 방식을 봤습니다. 하루 뒤인 11월 18일 Google도 새 모델 **Gemini 4 Neon**을 공개하면서 비슷한 조건을 붙였습니다. 일반 모델은 바로 열고, **사이버 방어용 변형은 'Fairwind Program'을 통해 검증된 방어자에게만** 며칠 안에 순차 제공한다고 밝혔습니다. 모델 자체로는 #13(추론 모델)과 #16(비용 최적화)에서 다룬 '생각 수준'과 '캐시 할인'이 가격표에 그대로 드러나는 사례입니다.

## 핵심 개념

- **모델 등급**: 같은 회사가 속도·비용·능력이 다른 모델을 여러 개 냅니다. Gemini 4 제품군에서 Hydrogen은 빠른 일상 작업, Carbon은 긴 작업과 코드, Argon은 최상위 모델이고, Neon은 Gemini 앱 모델 선택에서 '더 깊은 분석' 자리에 들어갔습니다.
- **생각 수준(thinking level)**: 답하기 전에 내부적으로 얼마나 오래 추론할지 고르는 값입니다. 높일수록 정확해질 수 있지만 느리고 비싸집니다(#13).
- **캐시 입력 할인**: 앞부분이 같은 긴 입력(시스템 지시, 문서)을 다시 보낼 때, 이미 처리한 부분을 싸게 계산해 주는 방식입니다(#16).
- **비유**: 같은 병원에 동네 의원(빠름), 종합병원 전문의(깊은 분석), 대학병원 협진(장시간·복잡한 사례)이 있고, 위험한 약은 면허가 확인된 의사에게만 처방권을 주는 것과 비슷합니다.

## 지금 무슨 일이 일어나고 있나

- **공개와 제공 범위.** Google은 11월 18일 Gemini 4 Neon을 Gemini API(Google AI Studio), 기업용 Gemini, Google Antigravity(유료 AI Pro·Ultra 구독자), Gemini 앱(Pro·Ultra 구독자)에 순차 제공한다고 밝혔습니다. Google Cloud 릴리스 노트에는 Gemini Enterprise Agent Platform에서 정식 출시로 올라와 있습니다.
- **위치.** 모델 카드는 Neon을 긴 작업을 맡는 Carbon과 빠른 실행을 맡는 Hydrogen 사이에 둡니다. Antigravity에서는 Neon을 계획을 세우는 쪽, Hydrogen을 실행하는 쪽으로 한 세션에서 함께 쓰는 구성을 소개했습니다(#5의 계획·실행 분리와 같은 구조).
- **가격과 입력 길이.** 발표 글 기준 입력 100만 토큰당 3달러, 캐시된 입력은 0.15달러(95% 할인), 출력은 100만 토큰당 15달러이고, 입력 창은 100만 토큰입니다. Google Cloud 가격표에는 리전 지정 요금이 약 10% 높게 나오고, 항목 이름이 분명하지 않은 더 높은 요금(입력 5.40달러·출력 27달러)도 함께 있어 어느 조건의 값인지 확인하지 못했습니다.
- **생각 수준.** Google Cloud 문서에 따르면 Neon은 LOW·MEDIUM·HIGH(기본값)·XHIGH를 지원하고, MINIMAL을 보내면 HTTP 400 오류를 돌려줍니다. 개발자 포럼에는 일부 계정에서 XHIGH 요청이 400으로 거절됐다는 글과, 나중에 됐다는 글이 함께 올라와 있습니다. 공식 설명이 아닌 사용자 보고입니다.
- **성능 수치.** 모델 카드는 AA Index v5.0.1에서 Neon 61점, Claude Opus 5.5 59점, GPT-6.2 Sol 57점이라고 적고, Vals Index v2.2에서 70.9%라고 적습니다. Neon 결과는 HIGH 생각 수준으로 잰 값입니다. Google이 발표한 수치이고, 같은 조건으로 재현한 외부 결과는 확인하지 못했습니다.
- **안전 평가.**
  - 콘텐츠 안전은 텍스트·다국어·이미지 입력 모두 Hydrogen과 비슷하고, 차이는 신뢰구간 안이라고 밝혔습니다.
  - 모델 카드에 따르면 위험 능력 평가는 Gemini 4 Argon의 결과를 가져와 썼습니다. 사이버·CBRN(화학·생물·방사능·핵) 분야에서 '위험 능력 수준'에 이르렀을 가능성을 배제할 수 없어 완화 조치를 적용했다고 적었습니다.
  - 전체 'Safety & Security Report'는 며칠 안에 공개한다고 했습니다.
- **사이버 변형.** 'Gemini 4 Neon for cyber'는 Fairwind Program을 통해 검증된 방어자(trusted defenders)에게 며칠 안에 순차 제공한다고 밝혔습니다.
- **확인 범위.** 이 글을 쓰는 환경에서는 Google 페이지를 직접 열지 못했습니다. 위 내용은 Google 공식 도메인(blog.google, deepmind.google, docs.cloud.google.com, ai.google.dev)으로 범위를 제한한 검색 결과에 실린 발췌로 확인했습니다.

## 동작 구조

```
요청
  │
  ├─ 일상·빠른 응답 ─────────▶ Hydrogen
  ├─ 깊은 분석 ──────────────▶ Neon   (생각 수준 LOW~XHIGH, 기본 HIGH)
  ├─ 긴 작업·복잡한 코드 ────▶ Carbon
  └─ 위험도 높은 보안 작업 ──▶ Neon for cyber  ← Fairwind 승인자만
```

서비스에 붙인다면 모델과 생각 수준을 요청마다 고르고, 비용을 같이 기록하는 쪽이 됩니다.

```python
def choose(task):
    if task.kind == "cyber_offense_eval" and not task.user.approved("fairwind"):
        return refuse("승인된 방어자만")
    if task.kind == "quick":
        return call("hydrogen")
    level = "HIGH" if task.needs_reasoning else "LOW"      # 기본값을 그대로 두지 않고 일의 종류로 정함
    resp = call("neon", thinking=level, cache_key=task.system_prompt_id)   # 같은 지시문은 캐시로
    log(task.id, model="neon", level=level, tokens_in=resp.usage.input, tokens_cached=resp.usage.cached, tokens_out=resp.usage.output)
    return resp
```

## 왜 중요한가 / 한계

- **'승인된 사용자에게만' 여는 방식이 두 회사에서 연달아 나왔습니다.** #22의 OpenAI는 Daybreak 승인 등급과 요청마다 켜는 표시를 요구했고, Google은 사이버 변형 자체를 별도 프로그램으로 나눴습니다. 방법은 다르지만 "능력이 높은 기능은 누가 쓰는지 확인한 뒤 연다"는 #18의 위험도별 규제와 같은 방향입니다.
- **생각 수준과 캐시가 비용의 큰 몫을 정합니다.** 출력 단가가 입력의 5배이고 캐시 입력은 95% 싸서, 긴 지시문을 캐시로 돌리고 생각 수준을 일에 맞게 낮추면 비용이 크게 달라집니다(#16). 반대로 기본값(HIGH)을 그대로 쓰면 필요 없는 추론에도 돈을 냅니다.
- **한계 1 — 성능 수치는 회사 발표입니다.** 비교 대상 모델도 Google이 고른 조건으로 잰 값입니다. 내 일에 맞는지는 내 평가 세트로 다시 재야 합니다(#10).
- **한계 2 — 안전 보고서가 아직 나오지 않았습니다.** 위험 능력 평가는 상위 모델(Argon) 결과를 가져와 썼고, 전체 보고서는 공개 전입니다.
- **한계 3 — 문서끼리의 차이.** 가격표의 두 요금 세트, 생각 수준 XHIGH 동작은 문서와 사용자 보고가 엇갈립니다.

## 내 프로젝트와 연결

- **AI 챌린지 VQA**에서 Qwen 4B와 27B의 Public Score 차이는 약 0.01이었습니다(0.94608 → 0.95591). 큰 모델이 늘 그만큼 낫지는 않아서, 새 후보는 단독 점수보다 기존 앙상블에서 고친 문제와 새로 틀린 문제(fixes−breaks)로 골랐습니다. 모델 등급을 고를 때도 같은 기준을 쓸 수 있습니다.
- **한끼 에이전트**는 모델에게 해석·도구 선택·문장 작성만 맡기고, 재고·분량 계산은 코드가 합니다. 모델 호출이 실패하면 규칙 계획으로 이어 가게 했습니다. 다만 요청별 토큰 수는 기록하지 않아서, 위 의사코드처럼 생각 수준이나 캐시에 따른 비용 차이를 수치로 비교하지는 못했습니다.
- **데이터 에이전트**는 답에 들어간 숫자를 조회 결과와 대조합니다. 생각 수준을 낮춰 비용을 줄일 때 정확도가 떨어지는지 확인하는 장치로도 쓸 수 있습니다.

## 면접 질문

**Q. 같은 회사의 모델이 여러 등급으로 나올 때, 서비스에 어떤 모델을 쓸지 어떻게 정하겠습니까?**

> 회사 벤치마크는 출발점으로만 보고, 우리 일로 만든 고정 평가 세트에서 정확도·응답 시간·비용을 함께 재겠습니다. 큰 모델이나 높은 생각 수준이 실제로 고친 사례와 새로 틀린 사례를 따로 세서, 고친 쪽이 분명히 많을 때만 올리겠습니다. VQA 챌린지에서 4B와 27B의 차이가 약 0.01이었고, 후보를 fixes−breaks로 골랐던 방식입니다. 그리고 요청마다 토큰 수를 기록해서 비용 차이를 숫자로 보겠습니다. 한끼 에이전트에서는 이 기록이 없어 비교하지 못했던 부분입니다.

## 출처

- Google, [Introducing Gemini 4 Neon](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/) — 2026-11-18, 제공 범위, 가격·캐시 할인·입력 창, 사이버 변형과 Fairwind Program (공식 도메인 검색 발췌로 확인)
- Google DeepMind, [Gemini 4 Neon — Model Card](https://deepmind.google/models/model-cards/gemini-4-neon/) · [Model Evaluation](https://deepmind.google/models/evals-methodology/gemini-4-neon/) — 위치, AA Index·Vals Index 수치, 안전 평가
- Google Cloud, [Gemini 4 Neon (Gemini Enterprise Agent Platform)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon) · [Developer's guide to Gemini 4 Neon](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-neon) — 생각 수준, MINIMAL 400 오류
- Google Cloud, [Agent Platform Pricing](https://cloud.google.com/model-garden/pricing) — 리전 요금
- Google AI Developers Forum, [Gemini 4 Neon and Orchestrator (Neon) are now available in Google Antigravity](https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301) — Antigravity 구성 (XHIGH 거절 보고는 같은 포럼의 사용자 글)
