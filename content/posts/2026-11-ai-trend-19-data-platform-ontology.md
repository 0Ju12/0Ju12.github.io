---
title: "11/9 Databricks Genie Ontology GA · 11/3 Snowflake Business Ontology — 에이전트에게 '업무 정의'를 주는 계층"
date: "2026-11-19"
summary: "데이터 플랫폼 두 곳이 11월 초 에이전트용 '온톨로지(업무 정의) 계층'을 잇달아 내놓았습니다. 무엇을 발표했는지, 공식 자료끼리 상태 표기가 어떻게 엇갈리는지, 데이터 엔지니어에게 어떤 일이 생기는지 정리했습니다."
tags: [이슈 분석, 시맨틱 레이어, 데이터 플랫폼]
series: ai-trend
episode: 19
next_topic: "#20 11월 dbt 업데이트 — dbt v2 지원 확대와 원격 MCP 서버의 권한 검사"
---

> **한 줄 요약** — #18까지 개념을 정리했고, 이번 회차부터는 그 주의 실제 사건을 앞 회차와 이어 읽습니다. 첫 사건은 데이터 플랫폼 쪽입니다. Databricks와 Snowflake가 11월 초 각각 **에이전트가 참고할 '업무 정의' 계층**을 발표했습니다. #3(MCP)에서 본 "도구를 어떻게 연결하나" 다음 단계로, "에이전트가 '매출'이 무엇인지 어떻게 아나"의 문제입니다.

## 핵심 개념

- **온톨로지(업무 정의 계층)**: '활성 고객', '순매출'처럼 회사마다 뜻이 다른 용어와, 그 용어가 어느 테이블·열·계산식에 대응하는지를 모아 둔 것입니다. 사람에게는 용어집이고, 에이전트에게는 질문을 SQL로 바꿀 때 쓰는 지도입니다.
- **시맨틱 레이어와의 관계**: 지표 정의를 한곳에 모아 BI 도구가 같은 숫자를 내게 하던 시맨틱 레이어와 겹치는 개념입니다. 이번 발표들은 그 소비자를 사람과 대시보드에서 **에이전트**로 넓혔다는 점이 다릅니다.
- **비유**: 신입 분석가에게 데이터베이스 접속 권한만 주면 테이블 이름을 보고 짐작해서 숫자를 뽑습니다. 팀 위키에 "매출은 환불을 뺀 금액, 이 테이블의 이 열"이라고 적혀 있으면 같은 질문에 같은 답이 나옵니다. 온톨로지는 에이전트용 팀 위키입니다.

## 지금 무슨 일이 일어나고 있나

- **Databricks — Genie Ontology GA.** 11월 릴리스 노트(11/9)와 GA 발표 글에 따르면 Genie Ontology가 정식 출시됐습니다. Databricks는 이를 "팀의 일상 업무에서 에이전트가 만들고 사람이 관리하는" 온톨로지로 설명하고, Genie One MCP 서버를 통해 Databricks 밖의 에이전트도 같은 업무 맥락을 쓸 수 있다고 밝혔습니다. **엇갈리는 점**: 같은 시점의 제품 문서에는 아직 '공개 미리보기'로 적혀 있습니다. GA 글이 더 최근이라 문서가 늦게 갱신된 것으로 보이지만, 이번 조사에서는 확정하지 못했습니다.
- **Snowflake — Business Ontology 발표.** 11/3 Expedition 2026 보도자료에서 Horizon Catalog 안의 Business Ontology(에이전트에게 미리 승인된 업무 정의를 주는 기능)와 Cortex AI Gateway(모든 에이전트에 보안·거버넌스와 팀·에이전트별 비용 확인을 적용)를 발표했습니다. Business Ontology는 블로그 기준 "곧 공개 미리보기"로, **아직 쓸 수 있는 상태는 아닙니다**. Cortex AI Gateway는 문서 릴리스 노트에서 일부 기능(추론·관찰·비용 관리)이 11/3 GA로 적혀 있는 반면, 같은 시기 블로그는 미리보기로 표기해 상태가 엇갈립니다.
- **공통점**: 두 회사 모두 "에이전트가 데이터를 바로 읽게 하는 것"이 아니라, **사람이 승인한 정의를 거쳐 읽게 하는 것**을 핵심으로 내세웠습니다. 위 내용은 모두 회사 자료이고, 독립적인 사용 평가는 아직 찾지 못했습니다.

## 동작 구조

```
사용자: "지난달 활성 고객 수는?"
   │
   ▼
에이전트 ── 온톨로지 조회: "활성 고객" = 30일 안에 결제 1회 이상
   │                      → 테이블 orders, 열 customer_id, paid_at
   ▼
SQL 생성 ── 권한 확인(AI Gateway·카탈로그) ── 실행
   │
   ▼
답 + 근거 (어떤 정의·테이블을 썼는지)
```

```python
def answer(question):
    terms = ontology.lookup(question)            # 승인된 정의만
    if terms.missing:
        return ask_user(f"'{terms.missing[0]}'의 정의가 등록돼 있지 않습니다")
    sql = llm.to_sql(question, definitions=terms.found)
    check_permissions(sql, user)                 # 사람이 볼 수 있는 범위 안에서만
    rows = warehouse.run(sql, read_only=True)
    return {"answer": summarize(rows), "used": terms.found, "sql": sql}
```

| | 온톨로지 없이 | 온톨로지를 거쳐 |
|---|---|---|
| 같은 질문의 답 | 테이블 이름 짐작에 따라 달라질 수 있음 | 같은 정의를 쓰면 같은 답 |
| 근거 | SQL만 보임 | 어떤 업무 정의를 썼는지 보임 |
| 새 용어 | 모델이 추측 | "정의 없음"으로 멈출 수 있음 |
| 관리 부담 | 적음 | 정의를 계속 관리해야 함 |

## 왜 중요한가 / 한계

- **데이터 엔지니어의 일이 하나 늘어납니다.** 테이블과 파이프라인뿐 아니라 "이 열이 업무에서 무슨 뜻인가"를 기계가 읽을 수 있게 관리하는 일이 생깁니다. dbt의 모델 설명·테스트가 이 정의의 출발점이 될 수 있습니다(#20에서 이어집니다).
- **#7(Agentic RAG)과 같은 원리**입니다. 모델이 모르는 사실은 검색으로 넣듯, 모델이 모르는 회사의 정의도 밖에서 넣어 줍니다.
- **한계 1 — 정의가 틀리면 틀린 답이 일관되게 나옵니다.** 온톨로지는 답을 맞게 해 주는 장치가 아니라 같게 해 주는 장치입니다. 정의 자체의 검증은 따로 필요합니다.
- **한계 2 — '에이전트가 만든다'는 설명.** Databricks는 에이전트가 온톨로지를 만들고 사람이 관리한다고 설명하는데, 자동으로 만든 정의를 누가 어떤 기준으로 승인하는지가 실제 운영의 핵심이 될 것입니다.
- **한계 3 — 상태 표기의 혼선.** 같은 회사 자료끼리도 GA·미리보기 표기가 엇갈렸습니다. 도입을 검토한다면 계약·문서 기준으로 다시 확인해야 합니다.

## 내 프로젝트와 연결

- **데이터 에이전트(MCP 서버)** 에서 LLM이 내 공개 데이터 결과를 SQL로 조회하게 했고, 읽기 전용으로 막고 답에 들어간 숫자를 조회 결과와 대조했습니다. 다만 업무 정의 계층은 없어서, 모델이 테이블 이름과 열 이름을 보고 질문을 해석했습니다. 온톨로지는 바로 그 빈자리를 채우는 장치입니다.
- **dbt 웨어하우스**에서는 모델마다 설명과 품질 테스트를 붙였습니다. 예를 들어 전력 수요의 '24시'를 다음 날로 넘기지 않도록 시간 키를 시작 시각으로 정하고 테스트로 고정했습니다. 이런 결정이 바로 사람이 승인한 정의에 해당하지만, 에이전트가 읽을 수 있는 형태로 내보낸 적은 없습니다.
- **국보 RAG 가이드**의 근거 번호 검증처럼, 답에 "어떤 정의를 썼는지"를 함께 내보이는 설계는 위 의사코드의 `used` 와 같은 자리입니다.

## 면접 질문

**Q. LLM 에이전트가 회사 데이터를 조회해 답하게 할 때, 같은 질문에 다른 숫자가 나오는 문제를 어떻게 막겠습니까?**

> 지표의 정의를 모델이 짐작하게 두지 않고, 사람이 승인한 정의를 거쳐 SQL을 만들게 하겠습니다. '활성 고객'처럼 회사마다 다른 용어를 테이블·열·계산식과 함께 등록해 두고, 등록되지 않은 용어가 나오면 추측하지 말고 되묻게 합니다. 답에는 어떤 정의와 SQL을 썼는지 함께 남겨 검증할 수 있게 합니다. 제 데이터 에이전트는 읽기 전용 SQL과 숫자 대조까지는 했지만 정의 계층이 없어서 모델이 열 이름으로 해석했는데, 이번에 Databricks와 Snowflake가 발표한 온톨로지 기능이 그 부분을 채우는 방향이라고 봅니다.

## 출처

- Databricks, [Announcing GA of Genie Ontology](https://www.databricks.com/blog/announcing-ga-genie-ontology)
- Databricks Docs, [Genie Ontology](https://docs.databricks.com/aws/en/genie/genie-ontology/) — 제품 문서는 조사 시점에 '공개 미리보기'로 표기
- Databricks Docs, [Release notes — November 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/november)
- Databricks, [The Genie One MCP is now Generally Available](https://www.databricks.com/blog/genie-one-mcp-now-generally-available)
- Snowflake, [Snowflake Helps Enterprises Deploy AI Agents with Trusted Business Context and Built-In Controls](https://www.snowflake.com/en/news/press-releases/expedition-2026-business-ontology-ai-gateway/) (2026.11.03)
- Snowflake, [Business Ontology: Governed Context for AI](https://www.snowflake.com/en/blog/business-ontology-context/) — "곧 공개 미리보기"
- Snowflake Docs, [Sep 15, 2026: Cortex AI Gateway (Preview)](https://docs.snowflake.com/en/release-notes/2026/other/2026-09-15-cortex-ai-gateway)
