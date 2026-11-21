---
title: "11/17~20 Microsoft Ignite 2026 — Fabric HorizonDB·Database Hub·Fabric apps, 운영 DB와 분석 저장소를 한 플랫폼에 두기"
date: "2026-11-21"
summary: "Microsoft가 Ignite 2026에서 Fabric 안에 서버리스 PostgreSQL(HorizonDB, 공개 미리보기)을 넣고, Database Hub와 Fabric apps를 정식 출시했습니다. 운영 DB와 분석 저장소 사이를 미러링과 역 ETL로 잇는 구조, 그리고 자료마다 엇갈리는 출시 단계를 정리했습니다."
tags: [이슈 분석, 데이터 플랫폼, 데이터 엔지니어링]
series: ai-trend
episode: 23
next_topic: "#24 11/18 Google Gemini 4 Neon — '깊은 분석' 자리의 새 모델과, 사이버 변형을 따로 여는 방식"
---

> **한 줄 요약** — #19에서는 Databricks와 Snowflake가 에이전트에게 '업무 정의'를 주는 계층을 봤고, #21에서는 에이전트의 기록을 BigQuery 테이블에 남기는 방식을 봤습니다. 이번에는 Microsoft 차례입니다. 11월 17~20일 Ignite 2026에서 Microsoft는 Fabric 안에 **서버리스 PostgreSQL(Fabric HorizonDB)**을 공개 미리보기로 넣고, 여러 곳의 데이터베이스를 한 화면에서 보는 **Database Hub**와 Fabric 데이터 위에 업무 앱을 만드는 **Fabric apps**를 정식 출시했다고 밝혔습니다. 앱이 쓰는 운영 DB와 분석 저장소를 한 플랫폼 안에서 잇겠다는 방향입니다.

## 핵심 개념

- **운영 DB(OLTP)와 분석 저장소(OLAP)**: 운영 DB는 주문·회원처럼 한 건씩 자주 바뀌는 데이터를 빠르게 읽고 씁니다. 분석 저장소는 많은 행을 모아 집계하는 데 맞춰져 있습니다. 보통 둘을 나누고, 그 사이를 ETL로 옮깁니다.
- **미러링**: 운영 DB의 변경을 분석 저장소(여기서는 OneLake)로 계속 복제하는 방식입니다. 한 번에 옮기는 ETL과 달리, 바뀐 부분이 따라 들어옵니다.
- **역 ETL(reverse ETL)**: 방향이 반대입니다. 분석 저장소에서 계산한 결과(예: 고객 등급, 예측값)를 다시 운영 DB로 넣어 앱이 쓰게 합니다.
- **비유**: 가게의 계산대 장부(운영 DB)와 본사의 월말 결산표(분석 저장소)가 있다고 하면, 미러링은 계산대 장부를 본사로 실시간 복사하는 것이고, 역 ETL은 본사가 계산한 '단골 할인 대상' 명단을 다시 계산대로 내려보내는 것입니다.

## 지금 무슨 일이 일어나고 있나

- **Fabric HorizonDB — 공개 미리보기.** Fabric 안에서 쓰는 서버리스 PostgreSQL입니다. Microsoft 설명에 따르면 데이터베이스를 몇 초 만에 만들고, 5분 동안 쓰지 않으면 멈췄다가 다음 쿼리가 오면 다시 켜집니다. 데이터를 OneLake로 미러링해 분석에 쓰고, Fabric 데이터를 연합 쿼리로 읽고, 분석 결과를 Copy 작업으로 다시 PostgreSQL에 넣는(역 ETL) 흐름을 함께 소개했습니다.
- **Azure HorizonDB — 정식 출시.** Fabric 밖의 관리형 PostgreSQL 호환 서비스는 정식 출시됐고, 13개 Azure 리전에서 쓸 수 있다고 밝혔습니다. 이름이 같아 헷갈리기 쉬운데, Fabric 쪽은 미리보기, Azure 쪽은 정식 출시입니다.
- **Database Hub in Fabric — 정식 출시.** Azure·Fabric·온프레미스·다른 클라우드에 흩어진 데이터베이스를 한곳에서 찾고 모니터링하고 관리하는 기능입니다. 이 기능은 몇 주 전 Microsoft 기술 블로그에서 '공개 미리보기'로 소개됐는데, Ignite에서 정식 출시로 바뀌었습니다. SQL·PostgreSQL용 데이터베이스 에이전트는 아직 미리보기입니다.
- **Fabric apps — 정식 출시.** Fabric 데이터 위에 업무 앱을 만드는 기능입니다. 저장소로 Microsoft SQL database나 Fabric HorizonDB를 고르고, 이미 있는 시맨틱 모델·웨어하우스·레이크하우스에 연결하는 방식이라고 설명했습니다.
- **Fabric IQ와 Microsoft IQ.** Fabric IQ는 데이터를 업무 개체(고객·주문 같은 개념)에 연결하는 Fabric 작업 영역입니다. Microsoft는 이를 Work IQ·Foundry IQ·Web IQ와 묶은 'Microsoft IQ'를 새로 발표했습니다.
- **과금.** Fabric에 기존 용량 기반 과금 외에 사용량 기반의 'Copilot Credits' 선택지를 더한다고 밝혔습니다. 단가와 용량 단위 환산은 찾지 못했습니다.
- **엇갈리는 점.**
  - Fabric IQ는 Fabric의 '새 기능' 문서에서 **미리보기**로 나옵니다. 반면 Ignite Book of News는 Fabric IQ와 Microsoft Copilot·Fabric apps의 **연동은 정식 출시**라고 씁니다. 작업 영역 자체와 개별 연동의 단계가 다른 것으로 보입니다.
  - Fabric IQ MCP 서버는 '새 기능' 문서에 9월 정식 출시로 올라 있습니다. 그런데 설정 문서는 범위를 Power BI 보고서와 시맨틱 모델 **읽기 전용**으로 적고, 온톨로지와 데이터 에이전트는 아직 지원하지 않는다고 씁니다.
- **확인 범위.** 이 글을 쓰는 환경에서는 Microsoft 페이지를 직접 열지 못했습니다. 위 내용은 Microsoft 공식 도메인(azure.microsoft.com, news.microsoft.com, learn.microsoft.com, techcommunity.microsoft.com)으로 범위를 제한한 검색 결과에 실린 발췌로 확인했습니다.

## 동작 구조

```
앱 (Fabric apps)
   │  읽기·쓰기
   ▼
Fabric HorizonDB (PostgreSQL, 서버리스) ──미러링──▶ OneLake ──▶ 웨어하우스·시맨틱 모델
   ▲                                                              │
   └──────────── 역 ETL (Copy 작업: 분석 결과를 다시 넣기) ◀──────┘
```

역 ETL에서 가장 먼저 정해야 하는 것은 "같은 작업이 두 번 돌면 어떻게 되는가"입니다.

```python
def reverse_etl(scores, pg):
    # 분석 저장소에서 계산한 고객 등급을 운영 DB에 넣기
    for row in scores:
        pg.execute(
            "insert into customer_grade (customer_id, grade, computed_at) values (%s, %s, %s) "
            "on conflict (customer_id) do update set grade = excluded.grade, computed_at = excluded.computed_at "
            "where customer_grade.computed_at < excluded.computed_at",   # 더 오래된 계산이 새 값을 덮지 않게
            (row.customer_id, row.grade, row.computed_at))
```

키 기준으로 덮어쓰고, 계산 시각이 더 새로울 때만 바꾸면 작업이 재시도되거나 순서가 뒤바뀌어도 결과가 같습니다.

## 왜 중요한가 / 한계

- **데이터 이동이 플랫폼 안으로 들어옵니다.** 지금까지는 운영 DB → 분석 저장소 ETL, 분석 결과 → 운영 DB 역 ETL을 각각 따로 만들고 운영했습니다. 미러링과 Copy 작업이 같은 플랫폼 기능이 되면, 파이프라인 코드는 줄고 대신 "얼마나 늦게 따라오는가(지연)"와 "누가 어떤 테이블을 쓰는가(권한)"를 확인하는 일이 남습니다.
- **에이전트가 쓰는 데이터도 같은 곳에 모입니다.** #19의 온톨로지, #20의 원격 MCP 권한 검사, #21의 에이전트 관측과 같은 흐름입니다. 이번에 Microsoft는 업무 개체(Fabric IQ)와 앱 저장소(HorizonDB), 운영 관리(Database Hub)를 한 플랫폼에 묶었습니다.
- **한계 1 — 출시 단계가 기능마다 다릅니다.** 같은 이름(HorizonDB)이 Azure에서는 정식 출시, Fabric에서는 미리보기입니다. Fabric IQ도 작업 영역과 연동의 단계가 다릅니다. 도입을 검토할 때는 기능 단위로 단계를 확인해야 합니다.
- **한계 2 — 서버리스의 첫 쿼리.** 5분 동안 쓰지 않으면 멈추는 구조라, 멈춘 뒤 첫 쿼리가 다시 켜는 시간만큼 늦어질 수 있습니다. 그 시간이 얼마인지는 찾지 못했습니다.
- **한계 3 — 비용 구조가 아직 불분명합니다.** Copilot Credits의 단가와 기존 용량과의 관계를 확인하지 못했습니다.

## 내 프로젝트와 연결

- Fabric은 써 보지 않았습니다. 가장 가까운 경험은 **공개 데이터 웨어하우스**입니다. dbt(DuckDB)로 원본 → 정제 → 집계 → 분석 표를 만들고, 날짜 파티션 내보내기는 임시 파일에 쓴 뒤 바꿔치기해 다시 돌려도 같은 파일이 나오게 했습니다. 위 의사코드의 역 ETL에 필요한 것도 같은 성질(재실행해도 결과가 같음)입니다.
- 웨어하우스에서 지진 기록은 발표 뒤에 고쳐지기 때문에, 덮어쓰지 않고 이전 판을 남기는 변경 이력(SCD 2형)으로 쌓았습니다. 미러링으로 운영 DB의 변경을 따라 받을 때도, 바뀐 값을 덮어쓸지 이력으로 남길지는 따로 정해야 합니다.
- **데이터 에이전트**는 SQL을 읽기 전용으로 막고, 답에 들어간 숫자를 조회 결과와 대조합니다. Fabric IQ MCP 서버가 읽기 전용 범위로 시작한 것과 같은 방향입니다.

## 면접 질문

**Q. 운영 DB와 분석 저장소를 미러링과 역 ETL로 잇는다면, 무엇을 먼저 확인하겠습니까?**

> 세 가지를 먼저 보겠습니다. 첫째, 미러링이 얼마나 늦게 따라오는지 재서 대시보드에 '마지막 반영 시각'을 같이 보여 주겠습니다. 둘째, 역 ETL은 키 기준으로 덮어쓰고 계산 시각이 새로울 때만 바꿔서, 재시도해도 결과가 같게 하겠습니다. 셋째, 운영 DB에 쓰는 계정의 권한을 그 테이블로만 좁히겠습니다. 웨어하우스 프로젝트에서 날짜 파티션을 다시 내보내도 같은 파일이 나오게 하고, 그걸 테스트로 확인했던 방식을 그대로 쓰겠습니다.

## 출처

- Microsoft Azure Blog, [Microsoft Ignite 2026: What's new in Azure, the platform purpose-built for AI](https://azure.microsoft.com/en-us/blog/microsoft-ignite-2026-whats-new-in-azure-the-platform-purpose-built-for-ai/) — HorizonDB, Fabric apps, Microsoft IQ, Copilot Credits (공식 도메인 검색 발췌로 확인)
- Microsoft, [Ignite 2026 Book of News](https://news.microsoft.com/events/ignite/2026/book-of-news/) — Fabric IQ 연동 정식 출시
- Microsoft Tech Community, [HorizonDB: PostgreSQL for enterprises, developers, and agents on Azure and Fabric](https://techcommunity.microsoft.com/blog/adforpostgresql/horizondb-postgresql-for-enterprises-developers-and-agents-on-azure-and-fabric/4573498) — Fabric HorizonDB 미리보기, 5분 비활성 시 일시 정지, 미러링·역 ETL
- Microsoft Tech Community, [What's new in databases at Microsoft Ignite 2026](https://techcommunity.microsoft.com/blog/azuresqlblog/whats-new-in-databases-at-microsoft-ignite-2026-ai-ready-data-for-apps-and-agent/4570764) — Database Hub 정식 출시, 데이터베이스 에이전트 미리보기
- Microsoft Tech Community, [Database Hub in Fabric: Now in Public Preview](https://techcommunity.microsoft.com/blog/azuresqlblog/database-hub-in-fabric-now-in-public-preview--turn-database-signals-into-guided-/4560846) — Ignite 이전의 미리보기 발표
- Microsoft Learn, [What's new in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/fundamentals/whats-new) · [Get started with the Fabric IQ MCP server](https://learn.microsoft.com/en-us/fabric/iq/connectors/fabric-iq-mcp) — Fabric IQ 미리보기, MCP 서버 읽기 전용 범위
