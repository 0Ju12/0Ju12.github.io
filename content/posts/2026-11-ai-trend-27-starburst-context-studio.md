---
title: "11/18 Starburst Context Studio — 에이전트에게 '매출'의 뜻을 알려 주는 정의 저장소"
date: "2026-11-23"
summary: "Starburst가 카탈로그·BI 도구·지표 저장소에 흩어진 업무 정의를 모아, 충돌하면 사람이 고르게 하고, 확정된 정의를 MCP로 에이전트에게 주는 Context Studio를 발표했습니다. 데이터 팀에게 지표 정의 관리가 어떤 일이 되는지 정리했습니다."
tags: [이슈 분석, 데이터 엔지니어링, 시맨틱 레이어]
series: ai-trend
episode: 27
next_topic: "#28 이슈 분석 — 다음 주 AI 뉴스"
---

> **한 줄 요약** — #19에서는 에이전트가 데이터를 바르게 읽으려면 '고객', '주문' 같은 업무 개념을 데이터에 연결하는 온톨로지가 필요하다고 봤고, #23에서는 Microsoft가 Fabric IQ로 같은 일을 플랫폼 안에 묶는 것을 봤습니다. 11월 18일 Starburst가 발표한 **Context Studio**는 방향이 조금 다릅니다. 정의를 한 플랫폼으로 옮기지 않고, **이미 정의가 있는 곳(카탈로그·BI 도구·지표 저장소·쿼리 기록)에서 모아 와 충돌을 표시하고, 사람이 확정한 정의만 MCP로 에이전트에게 줍니다.** 데이터를 옮기지 않고 조회하던 페더레이션을 '정의'까지 넓힌 셈입니다.

## 핵심 개념

- **업무 정의(business context)**: '활성 고객', '순매출', '이탈'처럼 같은 단어라도 팀마다 계산식이 다른 개념의 공식 뜻입니다. 용어집, 지표 계산식, 업무 규칙, 동의어, 표를 잇는 조인 키가 여기에 들어갑니다.
- **시맨틱 레이어**: 지표 정의를 한 곳에 두고 BI 도구와 쿼리가 모두 그 정의를 쓰게 하는 계층입니다. 보통은 정의를 그 계층 안으로 옮겨 다시 만들어야 합니다.
- **페더레이션**: 데이터를 한 저장소로 복사하지 않고, 여러 원천을 그 자리에서 함께 조회하는 방식입니다. Starburst(Trino 기반)의 본래 강점입니다.
- **비유**: 회사 안에 부서마다 다른 사전이 있다고 하면, 모든 사전을 하나로 새로 쓰는 대신 각 사전에서 표제어를 모아 뜻이 다른 낱말에 표시를 붙이고, 편집자가 공식 뜻을 정한 '통합 색인'을 만드는 것과 비슷합니다. 에이전트는 이 색인만 보고 답합니다.

## 지금 무슨 일이 일어나고 있나

- **발표.** Starburst는 11월 18일 Launch Point 행사에서 Context Studio를 발표했습니다. 회사 설명으로는 기존 Data Products와 함께 'Enterprise Context Layer'를 이루며, 페더레이션 분석 엔진과 자사 AI 에이전트(AIDA) 사이에 놓입니다.
- **무엇을 모으나.** 업무 카탈로그, BI 도구, 지표 저장소, 쿼리 기록, 기존 데이터 제품에서 정의를 가져옵니다(harvest). Galaxy 릴리스 노트는 모으는 대상을 용어집·지표·업무 규칙·동의어·조인 키로 적고, 이를 하나의 '인증된 저장소'로 묶는다고 씁니다.
- **충돌 처리.** 원천끼리 정의가 다르면 충돌로 표시하고, 어느 정의를 쓸지는 사람이 정합니다. 확정된 정의만 에이전트에게 제공됩니다.
- **에이전트 연결.** MCP를 지원하는 에이전트가 확정된 정의를 받아 갈 수 있고, 자사 AIDA뿐 아니라 외부 에이전트도 연결할 수 있다고 밝혔습니다.
- **감사 기록.** 에이전트가 어떤 데이터 원천에 접근했는지, 어떤 SQL을 만들었는지, 답에 어떤 정보를 썼는지를 기록한다고 설명합니다.
- **제공 단계와 날짜.**
  - 발표 자료는 Starburst Galaxy와 Starburst Enterprise(클라우드·자체 설치)에서 **비공개 미리보기**라고 씁니다.
  - Galaxy 릴리스 노트에는 같은 기능의 비공개 미리보기가 **10월 5일**에 이미 올라 있습니다. 11월 18일은 공식 발표일이고, 일부 고객 시험은 그 전에 시작된 것으로 보입니다.
  - Starburst 문서상 비공개 미리보기는 일부 계정만 쓰고 운영 용도로는 지원하지 않는 단계입니다. 정식 출시 시기(2027년 1분기)와 가격 미정은 2차 보도로만 확인했습니다.
- **효과 수치.** 정확도·생산성이 얼마나 좋아지는지에 대한 수치는 발표되지 않았다고 여러 보도가 함께 지적했습니다.
- **확인 범위.** 발표 내용은 BusinessWire 배포본과 Starburst 공식 문서(docs.starburst.io)의 검색 결과 발췌로 확인했습니다. 이 글을 쓰는 환경에서는 원문 페이지를 직접 열지 못했습니다.

## 동작 구조

```
정의가 이미 있는 곳                         Context Studio                     에이전트
───────────────────                  ─────────────────────────          ──────────────
업무 카탈로그 ─┐                       ① 모으기 (harvest)
BI 도구 ───────┤ ──────────────▶     ② 충돌 표시  ──▶ 사람이 확정          MCP로
지표 저장소 ───┤                       ③ 인증된 정의 저장소 ─────────────▶  정의 받아 감
쿼리 기록 ─────┤                                                            │
데이터 제품 ───┘                                                            ▼
                                       ④ 감사 기록 ◀── 접근한 원천·만든 SQL·쓴 정보
```

데이터 팀 쪽에서 보면 "정의도 코드처럼 관리한다"는 일이 됩니다. Galaxy 릴리스 노트에 'Context Studio as Code API'가 미리보기 구성 요소로 올라 있는 것도 같은 방향입니다. 정의 하나를 다루는 흐름은 대략 이렇습니다.

```python
def resolve(term, sources, approved):
    found = {s.name: s.definition(term) for s in sources if s.definition(term)}
    if term in approved:                       # 사람이 확정한 정의가 있으면 그것만
        return approved[term]
    if len(set(found.values())) > 1:           # 원천끼리 계산식이 다르면
        open_review(term, found)               # 충돌로 올리고
        return None                            # 에이전트에게는 아직 주지 않음
    return next(iter(found.values()), None)

def answer(question, agent):
    terms = agent.extract_terms(question)              # "지난달 순매출" → ["순매출"]
    defs = {t: resolve(t, SOURCES, APPROVED) for t in terms}
    if None in defs.values():
        return "정의가 확정되지 않은 용어가 있어 답하지 않습니다: " + ", ".join(t for t, d in defs.items() if d is None)
    sql = agent.write_sql(question, defs)
    log(question=question, defs=defs, sql=sql)          # 어떤 정의로 어떤 SQL을 만들었는지
    return run_readonly(sql)
```

## 왜 중요한가 / 한계

- **에이전트가 틀리는 이유가 '모델'에서 '정의'로 옮겨 갑니다.** 같은 질문에 팀마다 다른 숫자가 나오는 일은 사람이 쿼리를 짤 때도 있었습니다. 에이전트는 그 차이를 모른 채 그럴듯한 SQL을 만들기 때문에, 틀려도 티가 나지 않습니다. 정의 충돌을 사람이 먼저 정리하게 하는 구조는 #25의 ZeroOps가 고침안을 사람 승인 뒤에만 반영하는 것과 같은 판단입니다.
- **데이터 팀의 일이 하나 늘어납니다.** 지금까지 지표 정의는 대시보드나 dbt 모델 안에 흩어져 있었습니다. 에이전트에게 정의를 주려면 누가 어떤 정의를 확정했는지, 언제 바뀌었는지를 관리해야 합니다. 정의가 바뀌면 지난 답과 숫자가 달라지므로, 정의에도 판 번호와 이력이 필요합니다.
- **옮기지 않는 방식의 장단점.** 정의를 그 자리에서 모으면 기존 BI·카탈로그를 다시 만들지 않아도 됩니다. 대신 원천이 바뀔 때마다 충돌이 새로 생기고, 그 검토를 누가 계속 맡을지가 문제로 남습니다.
- **한계 1 — 비공개 미리보기입니다.** 운영 용도로 지원하지 않는 단계이고, 정식 출시 시기와 가격은 2차 보도로만 확인했습니다.
- **한계 2 — 효과 수치가 없습니다.** 정의를 모아 주면 에이전트의 답이 얼마나 정확해지는지는 회사도 수치로 내놓지 않았습니다.
- **한계 3 — 같은 문제를 푸는 제품이 여럿입니다.** Snowflake는 11월 초 Business Ontology를, Microsoft는 Fabric IQ(#23)를 내놓았습니다. 정의를 한 플랫폼에 두는 쪽과 여러 곳에서 모으는 쪽 가운데 어느 쪽이 자리 잡을지는 아직 모릅니다.

## 내 프로젝트와 연결

- **공개 데이터 분석 웨어하우스**에서 정의 하나가 숫자 전체를 바꾼 경험이 있습니다. 처음 만든 날짜 차원에는 주말 표시만 있어서 대체공휴일과 선거일이 평일로 들어가 평일 평균을 끌어내렸습니다. 공휴일 seed로 '평일'의 정의를 고치자 쉬는 날과의 차이가 달라졌습니다. 그래서 질문 하나에 분석 표 하나를 두고, 대시보드와 README의 숫자가 모두 그 표에서 나오게 했습니다. 정의가 한 곳에 있어야 숫자가 하나로 맞습니다.
- 같은 웨어하우스의 **채용 공고 기술 사전**은 사전을 고쳐도 지난 공고에는 적용되지 않습니다. 그래서 공고마다 어느 판의 사전으로 뽑았는지(판 번호)를 남깁니다. 위에서 말한 '정의에도 판 번호와 이력이 필요하다'를 작은 규모로 한 셈입니다.
- **데이터 에이전트**는 SQL을 읽기 전용으로 막고, 답에 들어간 숫자를 조회 결과와 대조합니다. 다만 '순매출'처럼 정의가 갈리는 용어를 확인하는 단계는 없습니다. 위 의사코드의 resolve 같은 단계를 붙인다면, 정의가 확정되지 않은 용어가 나올 때 답을 멈추게 하는 쪽이 됩니다.

## 면접 질문

**Q. 사내 데이터에 질문하는 AI 에이전트가 팀마다 다른 '매출' 숫자를 내놓는다면, 데이터 엔지니어로서 무엇부터 하겠습니까?**

> 모델보다 정의부터 보겠습니다. 각 팀의 계산식을 모아 어디서 갈리는지 나누고, 합의한 정의를 한 곳에서만 계산하게 한 뒤 에이전트가 그 정의만 쓰게 하겠습니다. 정의가 확정되지 않은 용어가 나오면 답하지 않게 하고, 어떤 정의로 어떤 SQL을 만들었는지 기록하겠습니다. 제 웨어하우스에서 날짜 차원의 '평일' 정의를 고치자 평일 평균이 달라졌던 경험이 있어서, 질문 하나에 분석 표 하나를 두고 모든 숫자가 그 표에서 나오게 했습니다.

## 출처

- Starburst (BusinessWire 배포본), [Starburst Introduces Context Studio, Extending Federation from Data to Context](https://www.financialcontent.com/article/bizwire-2026-11-18-starburst-introduces-context-studio-extending-federation-from-data-to-context) — 2026-11-18, 모으는 원천, 충돌 표시와 사람 확정, MCP 연결, 감사 기록, 비공개 미리보기
- Starburst Docs, [Starburst Galaxy release notes](https://docs.starburst.io/starburst-galaxy/get-started/release-notes.html) — 10/5 비공개 미리보기, 용어집·지표·업무 규칙·동의어·조인 키, Context Studio as Code API (공식 도메인 검색 발췌로 확인)
- Starburst Docs, [Feature release types](https://docs.starburst.io/starburst-galaxy/get-started/feature-release-types.html) — 비공개 미리보기의 뜻
- SiliconANGLE, [Starburst adds context support to give AI agents consistent access to business data definitions](https://siliconangle.com/2026/11/18/starburst-adds-context-support-to-give-ai-agents-consistent-access-to-business-data-definitions/) — 2차 보도
- TechTarget, [Starburst intros Context Studio to boost trust in AI responses](https://www.techtarget.com/news/starburst-intros-context-studio-to-boost-trust-in-ai-responses/875010/) — 2차 보도, 효과 수치 미공개
