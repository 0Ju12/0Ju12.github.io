---
title: "11월 dbt 업데이트 — dbt v2 지원 확대와 원격 MCP 서버의 권한 검사"
date: "2026-11-19"
summary: "dbt의 11월 정리 글과 릴리스 노트를 바탕으로, dbt v2가 지원하는 웨어하우스·묶음 테스트, 원격 dbt MCP 서버의 권한 검사 변경을 정리했습니다. 에이전트가 dbt 프로젝트를 읽고 실행하게 될 때 무엇을 확인해야 하는지 봅니다."
tags: [이슈 분석, dbt, MCP]
series: ai-trend
episode: 20
next_topic: "#21 11/14 BigQuery·Looker 에이전트 관측·평가 — 에이전트의 대화와 비용을 내 BigQuery 테이블에 남기기"
---

> **한 줄 요약** — 지난 회차의 업무 정의 계층은 "에이전트가 무엇을 참고하나"의 문제였습니다. 이번은 "에이전트가 데이터 변환 도구를 직접 다룰 때 무엇을 허락하나"입니다. dbt는 11월 정리 글에서 **dbt v2의 지원 웨어하우스 확대**와 **원격 MCP 서버가 도구 호출마다 권한을 확인하도록 바뀐 점**을 알렸습니다. #3(MCP)과 #9(가드레일)를 데이터 파이프라인에 적용한 사례입니다.

## 핵심 개념

- **dbt**: SQL로 쓴 모델을 의존 순서대로 실행하고, 각 모델에 테스트(고유값·빈 값 없음 등)를 붙여 데이터 품질을 확인하는 도구입니다.
- **dbt v2**: dbt Summit(9월)에서 발표된 다음 메이저 버전입니다. 릴리스 노트는 Rust로 쓴 단일 엔진이며 `pip install dbt` 로 설치한다고 설명합니다.
- **원격 dbt MCP 서버**: 에이전트가 dbt 프로젝트의 모델·문서·실행 기록을 조회하고 일부 작업을 요청할 수 있게 하는 MCP 서버를 dbt가 호스팅하는 형태입니다.
- **비유**: 공장 설비(웨어하우스)에 원격 조작판(MCP)을 달아 주는 것과 비슷합니다. 조작판을 연결할 수 있다는 것과, 버튼마다 누가 눌러도 되는지 확인하는 것은 별개의 일입니다. 이번 변경은 뒤쪽입니다.

## 지금 무슨 일이 일어나고 있나

- **dbt v2 지원 웨어하우스.** 11월 정리 글은 dbt v2가 Amazon Redshift, Databricks, Google BigQuery, Snowflake, **DuckDB**에서 GA이고, ClickHouse와 Apache Spark는 베타라고 밝혔습니다. v2 자체의 발표는 9월이고, 11월 글은 지원 범위를 정리한 것입니다.
- **묶음 테스트(batch testing) GA.** 모델마다 따로 돌던 고유값(unique)·빈 값 없음(not_null) 테스트를 테스트 종류별로 한 번의 쿼리로 묶어 실행합니다. 테스트 코드는 그대로 두고 `--batch-tests` 옵션으로 켭니다. 로컬 단위 테스트는 알파, dbt Wizard 데스크톱은 공개 베타로 적혀 있습니다.
- **원격 MCP 서버의 권한 검사 변경.** 11월 릴리스 노트에 따르면 원격 MCP가 **도구 호출마다** 그 호출이 대상으로 하는 프로젝트·환경·작업·실행에 대한 권한을 확인하도록 바뀌었고, 연결만 하려고 Developer 권한을 받을 필요는 없어졌습니다. Gemini Enterprise 연결 지원과 Databricks Marketplace 등록도 함께 발표됐습니다.
- **엇갈리는 점과 주의 문구.** dbt Summit 자료는 MCP 서버를 GA로, 문서는 OAuth 기준 공개 베타로 적고 있습니다. 문서에는 "원격 MCP 도구는 사전 공지나 지원 중단 기간 없이 바뀔 수 있다"는 문구가 있고, 로컬 dbt CLI 작업은 원격 서버가 아니라 직접 띄우는 서버가 필요하다고 적혀 있습니다.

## 동작 구조

```
에이전트 ──MCP──▶ 원격 dbt MCP 서버
                    │  도구 호출 하나마다:
                    │   ① 이 사용자가 대상 프로젝트·환경·작업에 권한이 있는가?
                    │   ② 없으면 거부, 있으면 실행
                    ▼
            dbt 프로젝트 (모델 · 테스트 · 실행 기록)
                    │
                    ▼
              웨어하우스 (Snowflake · BigQuery · DuckDB …)
```

```python
def handle_tool_call(user, tool, target):
    if not permissions.allows(user, action=tool.name, scope=target):   # 연결이 아니라 호출 단위로
        return deny(f"{tool.name}: {target} 에 대한 권한 없음")
    if tool.writes and target.env == "prod":
        return require_human_approval(tool, target)                    # 운영 반영은 사람이
    return tool.run(target)
```

| 변경 | 전 | 후 (11월 기준) |
|---|---|---|
| 권한 확인 단위 | 연결할 때 넓은 권한 필요 | 도구 호출마다 대상 범위 확인 |
| 테스트 실행 | 모델·테스트마다 쿼리 | 종류별로 묶어 한 쿼리 (옵션) |
| 지원 웨어하우스 (v2 GA) | — | Redshift·Databricks·BigQuery·Snowflake·DuckDB |

## 왜 중요한가 / 한계

- **에이전트에게 맡길 수 있는 범위가 권한으로 정해집니다.** 연결 시점에 넓은 권한을 주는 방식에서는 에이전트가 한 번 연결되면 할 수 있는 일이 너무 넓어집니다. 호출 단위 확인은 #9(가드레일)의 "막을 때는 닫힌 쪽으로"를 도구 수준에서 구현한 것입니다.
- **묶음 테스트는 품질 검사를 자주 돌리게 해 줍니다.** 테스트가 많아질수록 실행 시간이 부담이 되는데, 같은 종류를 묶으면 쿼리 수가 줄어듭니다. 다만 효과의 크기는 공식 자료에서 수치로 확인하지 못했습니다.
- **한계 1 — 도구가 예고 없이 바뀔 수 있습니다.** 원격 MCP 도구에 의존하는 자동화는 바뀐 도구 때문에 조용히 실패할 수 있으므로, 호출 결과를 검증하고 실패를 기록해야 합니다.
- **한계 2 — 상태 표기의 혼선.** GA와 베타 표기가 자료마다 달라, 도입 전에는 계정 등급별 문서를 직접 확인해야 합니다.
- **한계 3 — 권한이 맞아도 결과는 틀릴 수 있습니다.** 권한 검사는 "해도 되는가"를 보고, "결과가 맞는가"는 여전히 테스트와 검증이 맡습니다.

## 내 프로젝트와 연결

- **공개 데이터 웨어하우스**는 dbt-core 1.12와 dbt-duckdb로 만들었고, 모델 35개에 품질 테스트 101개를 붙였습니다. 이번에 v2가 GA로 지원하는 목록에 DuckDB가 들어 있어 옮겨 볼 수 있는 대상이지만, **아직 dbt v2나 묶음 테스트로 돌려 보지는 않았습니다.** 옮긴다면 테스트 결과가 v1과 같은지, 실행 시간이 어떻게 달라지는지를 같은 데이터로 비교하겠습니다.
- **데이터 에이전트**도 MCP 서버였고, SQL을 읽기 전용으로 막았습니다. 다만 사용자별·도구별 권한 구분은 없이 서버 하나가 같은 권한으로 동작했습니다. 원격 dbt MCP의 호출 단위 권한 검사가 제 구현에 없던 부분입니다.
- **관통 7 FastAPI 프록시**에서 가드레일 판정이 형식에 맞지 않으면 503으로 막았던 것처럼, 위 의사코드의 `deny` 는 확인하지 못하면 실행하지 않는 쪽입니다.

## 면접 질문

**Q. 에이전트가 dbt 같은 데이터 파이프라인 도구를 직접 실행하게 한다면 무엇을 먼저 정하겠습니까?**

> 권한과 검증을 먼저 정하겠습니다. 연결할 때 넓은 권한을 주지 않고, 도구 호출마다 그 호출이 건드리는 환경과 작업에 권한이 있는지 확인하게 하고, 운영 환경에 쓰는 작업은 사람이 승인하게 하겠습니다. 실행 결과는 dbt 테스트로 다시 확인합니다. 제 웨어하우스는 모델 35개에 품질 테스트 101개를 붙여 잘못된 자료가 들어오면 빌드가 실패하게 했고, 데이터 에이전트는 SQL을 읽기 전용으로 막았습니다. 다만 사용자별 권한은 나누지 않았기 때문에, 이번 dbt 원격 MCP의 호출 단위 권한 검사처럼 그 부분을 보완하겠습니다.

## 출처

- dbt Labs, [What's new in dbt: November 2026](https://www.getdbt.com/blog/whats-new-in-dbt-november-2026)
- dbt Docs, [dbt release notes](https://docs.getdbt.com/docs/dbt-versions/release-notes) — v2(9월), 원격 MCP 권한 변경·Gemini Enterprise·Databricks Marketplace(11월)
- dbt Docs, [dbt Model Context Protocol server](https://docs.getdbt.com/docs/dbt-ai/about-mcp?version=2) — 공개 베타 표기, 도구 변경 주의 문구
- dbt Docs, [Connect to the remote dbt MCP server](https://docs.getdbt.com/docs/dbt-ai/mcp-quickstart-remote)
- dbt Labs, [Everything we announced at dbt Summit and why it matters](https://www.getdbt.com/blog/dbt-summit-2026-product-announcements) — MCP 서버 GA 표기
