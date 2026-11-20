---
title: "11/14 BigQuery·Looker 에이전트 관측·평가 — 에이전트의 대화와 비용을 내 BigQuery 테이블에 남기기"
date: "2026-11-20"
summary: "Google Data Cloud가 11월 14일 BigQuery·Looker 데이터 에이전트의 관측·평가 기능을 넓혔습니다. 무엇이 GA이고 무엇이 아직 미리 보기인지, 어떤 기록이 어디에 남는지, 데이터 엔지니어가 이 기록으로 무엇을 확인할 수 있는지 정리했습니다."
tags: [이슈 분석, 에이전트 관측, BigQuery]
series: ai-trend
episode: 21
next_topic: "#22 11/17 OpenAI GPT-6.2 Astra·Sol — 사이버보안 'Critical' 등급 모델을 내보내며 붙인 조건"
---

> **한 줄 요약** — 지난 회차는 에이전트가 dbt를 다룰 때 "무엇을 허락하나"(호출마다 권한 검사)였습니다. 이번은 그다음 질문인 "에이전트가 무엇을 했는지 어떻게 아나"입니다. Google Data Cloud는 11월 14일 BigQuery·Looker 데이터 에이전트의 **대화 기록, 토큰·지연 지표, 단계별 실행 추적을 고객이 소유한 BigQuery 테이블과 Cloud Monitoring·Trace로 모으는 기능**을 GA로 발표했습니다. #10(에이전트 평가)에서 본 "결과뿐 아니라 과정을 기록해야 평가할 수 있다"를 데이터 플랫폼이 제품으로 붙인 사례입니다.

## 핵심 개념

- **에이전트 관측(observability)**: 에이전트가 요청 하나를 처리하면서 어떤 단계를 거쳤고, 어떤 도구를 불렀고, 시간과 토큰을 얼마나 썼는지 나중에 다시 볼 수 있게 남기는 것입니다.
- **스팬(span)과 추적(trace)**: 요청 하나를 "계획 → 도구 호출 → 응답" 같은 단계로 쪼개 각 단계의 시작·끝 시각을 기록한 것이 스팬이고, 스팬을 이어 붙인 전체 흐름이 추적입니다.
- **1P·3P 에이전트**: 1P는 BigQuery·Looker에 들어 있는 Google 제공 데이터 에이전트, 3P는 사용자가 ADK나 LangGraph 같은 프레임워크로 직접 만든 에이전트입니다.
- **비유**: 비행기의 비행 기록 장치와 비슷합니다. 평소에는 아무도 보지 않지만, 이상한 일이 생겼을 때 무엇을 언제 했는지 되짚을 수 있는 유일한 근거가 됩니다. 이번 발표의 핵심은 그 기록을 항공사(고객)가 가진 서랍(BigQuery 테이블)에 넣는다는 점입니다.

## 지금 무슨 일이 일어나고 있나

- **11월 14일 Google Cloud 블로그 발표.** BigQuery·Looker의 1P 데이터 에이전트와, ADK·LangGraph로 만든 3P 에이전트를 함께 볼 수 있는 관측·평가 기능을 넓혔다고 밝혔습니다. 기록을 모아 **고객이 소유한 BigQuery 테이블**에 넣고 거기서 분석하는 구조입니다.
- **GA로 표기된 것.** BigQuery 대화 기록, A2A(에이전트 간) 워크플로, Conversational Analytics API(관리자 감사 로그 기본, 데이터 읽기 감사 로그 선택), BigQuery Studio의 에이전트 모니터링 대시보드, Looker의 Conversational Analytics 시스템 활동 대시보드입니다.
- **미리 보기(preview)로 표기된 것.** BigQuery 안에서 돌리는 에이전트 평가(API와 Colab 노트북), 프로젝트·사용자·에이전트별 하루 입력·출력 토큰 한도, Looker의 사용자 평점·질의 검토 탭입니다.
- **무엇이 기록되나.** Cloud Monitoring에는 요청 수·지연·토큰 사용량 같은 집계 지표가, Cloud Trace에는 요청마다 단계별 스팬이 남습니다. BigQuery 대화 기록에는 대화 한 턴마다 입력·출력·생각(thought)·캐시·전체 토큰 수와 턴 전체 지연이 남습니다. ADK 플러그인은 도구 호출 실행 트리와 시계열 지표를 BigQuery로 바로 보낸다고 적혀 있습니다.
- **무엇이 빠지나.** 운영 지표와 정리된 1P 추적 스팬은 사용자 질문·모델 응답·내부 생각·생성된 SQL 같은 **고객 핵심 내용을 제외**합니다. 1P 대화 기록도 저수준 도구 인자와 내부 SQL은 **일부러 뺀다**고 밝혔습니다.
- **어디에 남나.** 대화 기록은 Storage Write API로 고객 소유 BigQuery 테이블(`agent_events`)에 쓰이고, 그 데이터셋의 IAM 권한·고객 관리 암호화 키(CMEK)·VPC 서비스 제어를 그대로 따릅니다.
- **릴리스 노트의 같은 흐름.** BigQuery 릴리스 노트에는 Data Engineering Agent에서도 관측을 켜면 토큰 소비·요청 수·모델 지연은 Cloud Monitoring에서, 실행 추적과 도구 호출은 Cloud Trace에서 볼 수 있다는 GA 항목이 올라왔습니다. 추적 데이터는 관측용 데이터셋에 30일 보관되고, 더 오래 두려면 BigQuery 데이터셋으로 옮기라고 안내합니다. 이 항목은 검색 결과에 실린 릴리스 노트 발췌로 확인했고, 원문 페이지는 이 글을 쓰는 환경에서 열지 못했습니다. 게시 날짜도 검색 요약마다 달라 확정하지 않았습니다.

## 동작 구조

```
사용자 질문
   │
   ▼
데이터 에이전트 (BigQuery·Looker 1P  /  ADK·LangGraph 3P)
   │  단계마다 스팬 기록: 계획 → 도구 호출 → SQL 실행 → 응답
   ├──▶ Cloud Monitoring : 요청 수 · 지연 · 토큰 (집계)
   ├──▶ Cloud Trace      : 요청별 단계 스팬 (질문·응답·SQL 내용은 제외)
   └──▶ BigQuery agent_events (고객 소유 테이블)
          : 턴별 입력·출력·생각·캐시 토큰, 턴 지연
          : 데이터셋 IAM · CMEK · VPC 서비스 제어를 그대로 적용
                │
                ▼
        SQL로 분석 · 대시보드 · 평가(미리 보기)
```

기록이 테이블에 쌓이면, 에이전트의 비용과 느린 질문을 보통 데이터처럼 SQL로 확인할 수 있습니다.

```sql
-- 예시: 에이전트별 하루 토큰과 느린 턴 비율 (열 이름은 설명용 가정)
select agent_id, date(event_ts) as day,
       sum(total_tokens) as tokens,
       countif(turn_latency_ms > 10000) / count(*) as slow_ratio
from agent_events
group by 1, 2
order by day desc, tokens desc;
```

| 항목 | 상태 (11/14 발표 기준) |
|---|---|
| BigQuery 대화 기록 · A2A 워크플로 | GA |
| Conversational Analytics API · 감사 로그 | GA |
| BigQuery Studio · Looker 모니터링 대시보드 | GA |
| BigQuery 안의 에이전트 평가 | 미리 보기 |
| 프로젝트·사용자·에이전트별 하루 토큰 한도 | 미리 보기 |

## 왜 중요한가 / 한계

- **에이전트 기록이 일반 데이터와 같은 규칙을 따릅니다.** 기록이 별도 서비스가 아니라 고객 데이터셋에 쌓이므로, 접근 권한·암호화·보관 기간을 기존 데이터 거버넌스로 관리할 수 있습니다. #20에서 본 호출 단위 권한 검사가 "막기"라면, 이번 기능은 "남기기"에 해당합니다.
- **비용을 지표로 잡을 수 있습니다.** #16(비용·지연 최적화)에서 본 캐시 효과나 모델 라우팅의 결과를, 턴별 캐시 토큰과 지연으로 직접 확인할 수 있게 됩니다. 다만 토큰 한도 자체는 아직 미리 보기입니다.
- **한계 1 — 내용을 빼면 디버깅이 어렵습니다.** 개인정보 보호를 위해 질문·응답·생성 SQL·도구 인자를 뺀다는 것은, 반대로 "왜 틀린 SQL을 만들었나"를 이 기록만으로는 알기 어렵다는 뜻입니다. 내용까지 남길지는 각 조직이 따로 정해야 합니다.
- **한계 2 — 관측은 정답을 알려 주지 않습니다.** 지연과 토큰은 측정되지만, 답이 맞았는지는 평가가 따로 필요하고 그 평가 기능은 아직 미리 보기입니다. #10에서 본 것처럼 정답 세트와 채점 기준은 사용자가 만들어야 합니다.
- **한계 3 — 상태 표기가 흩어져 있습니다.** 같은 묶음 안에서도 GA와 미리 보기가 섞여 있고, 릴리스 노트 항목의 날짜도 자료마다 엇갈려 도입 전에는 기능별로 문서를 확인해야 합니다.

## 내 프로젝트와 연결

- **한끼 Agent**(SSAFY)는 이벤트 버스 → 로깅 Agent → SQLite 구조로 분석·계획·실행·판정·응답과 도구 인자·지연·재계획 사유를 남겼고, 로깅 Agent는 모델을 쓰지 않고 중복 호출·계획 밖 호출·같은 도구 연속 실패·재계획 상한을 규칙으로 판정했습니다. 이번 발표의 스팬·턴 기록과 같은 목적입니다. 다만 저는 **토큰 수는 기록하지 않았고**, 기록을 SQLite 한 곳에만 두었습니다. 옮긴다면 턴별 토큰과 캐시 토큰을 추가하겠습니다.
- **공개 데이터 프로젝트**의 API Watch는 HTTP 200이어도 오래된 자료·빈 결과·구조 변경을 따로 판정했고, 포트폴리오에는 매일 수집 작업의 실제 실행 횟수와 실패 횟수를 GitHub Actions 기록에서 자동으로 세어 보여 줍니다. "돌아간다"를 기록으로 보여 주려는 같은 방향이지만, 에이전트의 단계별 추적까지는 하지 않았습니다.
- **데이터 에이전트**(MCP 서버)는 답에 들어간 숫자를 조회 결과와 대조했지만, 호출별 지연·비용 기록은 남기지 않았습니다. 이번 기능의 대화 기록 테이블 같은 저장소가 제 구현에 없던 부분입니다.

## 면접 질문

**Q. 사내 데이터 에이전트를 운영한다면 무엇을 기록하고, 그 기록을 어떻게 쓰겠습니까?**

> 요청마다 단계별 실행 기록과 도구 호출, 지연, 토큰을 남기고, 그 기록을 일반 데이터처럼 권한과 보관 기간을 정해 웨어하우스에 쌓겠습니다. 그러면 비용이 큰 질문 유형과 느린 단계를 SQL로 찾을 수 있습니다. 한끼 Agent에서는 로깅 Agent가 분석·계획·실행 단계와 도구 인자, 지연, 재계획 사유를 SQLite에 기록하고, 중복 호출이나 계획 밖 호출 같은 이상을 규칙으로 판정했습니다. 다만 토큰은 기록하지 않았기 때문에 비용 분석은 할 수 없었고, 그 부분을 먼저 보완하겠습니다. 답이 맞았는지는 기록만으로 알 수 없으므로 정답 세트로 하는 평가를 따로 두겠습니다.

## 출처

- Google Cloud Blog, [New AI agent observability and governance across BigQuery and Looker](https://cloud.google.com/blog/products/data-analytics/enterprise-ai-agent-observability-with-bigquery-and-looker) — 2026-11-14, GA·미리 보기 구분, 기록 항목과 저장 위치
- Google Cloud Docs, [BigQuery release notes](https://docs.cloud.google.com/bigquery/docs/release-notes) — Data Engineering Agent 관측 GA, 추적 30일 보관 (검색 결과의 발췌로 확인)
- Google Cloud Docs, [Create data agents](https://docs.cloud.google.com/bigquery/docs/create-data-agents)
- GitHub, [GoogleCloudPlatform/data-cloud-plugins — agent-analytics](https://github.com/GoogleCloudPlatform/data-cloud-plugins/blob/main/agent-analytics/README.md)
