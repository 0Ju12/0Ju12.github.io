---
title: "11/17 OpenAI GPT-6.2 Astra·Sol — 사이버보안 'Critical' 등급 모델을 내보내며 붙인 조건"
date: "2026-11-20"
summary: "OpenAI가 11월 17일 공개한 GPT-6.2 Astra·Sol은 시스템 카드에서 두 모델 모두 사이버보안 'Critical' 등급으로 평가됐습니다. 등급이 무엇을 뜻하는지, 공개하면서 어떤 접근 제한을 걸었는지, 자료끼리 엇갈리는 부분을 정리했습니다."
tags: [이슈 분석, AI 안전, 가드레일]
series: ai-trend
episode: 22
next_topic: "#23 11/17~20 Microsoft Ignite 2026 — Fabric HorizonDB·Database Hub·Fabric apps, 운영 DB와 분석 저장소를 한 플랫폼에 두기"
---

> **한 줄 요약** — 지난 회차는 에이전트의 행동을 "기록"하는 쪽이었습니다. 이번은 모델 회사가 공개 전에 "어디까지 할 수 있는 모델인가"를 평가하고 그에 맞춰 사용을 제한하는 쪽입니다. OpenAI는 11월 17일 GPT-6.2 Astra와 Sol을 내놓으면서, 시스템 카드에 **두 모델 모두 사이버보안 능력이 자체 기준의 가장 높은 단계(Critical)에 해당한다**고 적고, 위험도가 높은 보안 작업은 **검증된 사용자에게만 단계적으로 여는 조건**을 붙였습니다. #9(가드레일)와 #18(위험도별 규제)을 모델 공개 절차에서 보는 사례입니다.

## 핵심 개념

- **시스템 카드**: 모델을 공개할 때 함께 내는 문서로, 어떤 위험을 어떻게 평가했고 어떤 안전장치를 붙였는지 적습니다.
- **Preparedness Framework(대비 체계)**: OpenAI가 사이버보안·생물·화학·AI 자기 개선 같은 영역별로 모델 능력을 단계(High, Critical 등)로 평가하고, 단계마다 필요한 안전장치를 정해 둔 자체 기준입니다. 2025년 4월 공개된 2판은 "심각한 피해 위험을 충분히 줄이는 안전장치가 배포 전에 있어야 하고, Critical 능력이면 개발 단계에도 적용해야 한다"고 적고 있습니다.
- **사이버보안 Critical 기준**: 같은 문서는 높은 수준의 목표만 주어도 방어가 갖춰진 대상에 대한 새로운 공격 전략을 처음부터 끝까지 세우고 실행할 수 있는 수준 등을 Critical 조건으로 듭니다.
- **비유**: 공구상이 전동 공구를 팔 때 일반 매장에는 기본형만 두고, 강력한 절단기는 자격을 확인한 사람에게만 파는 것과 비슷합니다. 같은 물건이라도 누가 어떤 목적으로 쓰는지 확인한 뒤 기능을 여는 방식입니다.

## 지금 무슨 일이 일어나고 있나

- **공개.** 시스템 카드와 OpenAI 개발자 커뮤니티 공지는 11월 17일 자로, GPT-6.2 Astra와 Sol을 ChatGPT Work와 Codex에서 Plus·Pro·Enterprise·Edu 사용자에게 제공한다고 밝혔습니다. 시스템 카드 모음 페이지 한 곳에는 같은 카드가 11월 16일로 표시돼 있어 날짜가 하루 엇갈립니다.
- **평가 등급.** 시스템 카드에 따르면 두 모델 모두 사이버보안은 Critical, 생물·화학은 High입니다. AI 자기 개선 영역에서는 **Astra만 High**이고 Sol은 그 아래로, Astra는 이 영역에서 High로 평가된 채 외부에 공개된 첫 모델이라고 적혀 있습니다.
- **공개하면서 붙인 조건.**
  - 출시 시점의 생물·사이버 안전장치를 이전보다 보수적으로 설정했습니다.
  - 위험도가 높은 보안 작업에 대한 거절을 줄이려면 'Daybreak Red' 승인을 받고, 요청마다 Daybreak를 켜야 합니다.
  - 'Daybreak Blue' 승인만으로는 두 모델의 안전장치가 완화되지 않습니다. 정당한 보안 업무에 필요한 사람에게 신원을 확인한 뒤 더 허용적인 설정을 주는 '신뢰 접근(Trusted Access)' 방식입니다.
  - 외부 사용을 감시하는 모니터링 시스템을 함께 운영한다고 밝혔습니다.
- **내부 사용도 대상.** 시스템 카드는 Critical 능력이므로 OpenAI 내부에서 쓸 때도 안전장치가 적용돼야 한다고 적었습니다.
- **수치.** 시스템 카드의 내부 평가(ExploitBench)에서 임의 코드 실행 성공률은 Astra 53.5%, Sol 50.5%였고, 이전 GPT-6 Astra는 31.5%였습니다. OpenAI 자체 평가이며 외부에서 재현된 수치는 확인하지 못했습니다.
- **엇갈리는 점.** 이전 모델인 GPT-6 Astra에 대해서는 같은 안전 자료 모음 안에서도 "Critical로 취급할 필요는 없다"는 문구와 "Critical 기준에 해당한다"는 문구가 함께 검색됩니다. 이번 GPT-6.2 자료는 Critical로 일관됩니다.
- **확인 범위.** 이 글을 쓰는 환경에서는 OpenAI 페이지를 직접 열지 못했습니다. 위 내용은 OpenAI 공식 도메인으로 범위를 제한한 검색 결과에 실린 시스템 카드·공지·도움말 발췌로 확인했습니다.

## 동작 구조

```
요청 (보안 관련 작업)
   │
   ▼
① 기본 안전장치 ── 위험도 높은 보안 도움은 거절 (출시 시점에 더 보수적으로)
   │
   ├─ 사용자에게 Daybreak Red 승인이 있고, 이 요청에 Daybreak를 켰는가?
   │      아니오 → 기본 안전장치 유지 (Blue 승인만으로는 완화 안 됨)
   │      예     → 완화된 설정으로 응답
   ▼
② 외부 사용 모니터링 ── 사용 기록을 감시
```

이 흐름을 일반 서비스의 권한 검사로 옮기면 다음과 같습니다.

```python
def allow_high_risk_cyber(user, request):
    if not user.has_approval("red"):        # 신원·업무를 확인한 승인 등급
        return False
    if not request.flags.get("daybreak"):    # 승인이 있어도 요청마다 명시적으로 켜야 함
        return False
    return True                              # 이 경우에만 완화된 설정, 사용 기록은 계속 감시
```

| 영역 | GPT-6.2 Astra | GPT-6.2 Sol |
|---|---|---|
| 사이버보안 | Critical | Critical |
| 생물·화학 | High | High |
| AI 자기 개선 | High | High 미만 |

## 왜 중요한가 / 한계

- **위험도별 의무가 모델 공개 절차에 들어갔습니다.** #18에서 본 EU AI Act와 한국 AI 기본법은 위험도에 따라 의무를 나눴습니다. 이번 사례는 모델 회사가 스스로 정한 단계에 따라 "누구에게 어떤 기능을 열지"를 공개 조건으로 정한 것입니다.
- **가드레일이 사용자 등급과 요청 단위로 갈립니다.** #9에서 본 입력·출력 검사에 더해, 사용자의 승인 등급과 요청마다 켜는 표시가 둘 다 있어야 기능이 열립니다. #20의 원격 dbt MCP가 호출마다 권한을 확인한 것과 같은 방향입니다.
- **코딩 에이전트와 직접 닿습니다.** 이번 모델은 Codex에서도 제공됩니다. #11에서 본 코딩 에이전트가 쓰는 모델의 보안 능력이 높아질수록, 개발 도구 쪽에서도 어떤 작업을 허용할지 정해야 합니다.
- **한계 1 — 등급은 회사의 자체 평가입니다.** Critical·High 판정과 ExploitBench 수치는 OpenAI 내부 평가이고, 외부 기관의 재현 결과는 확인하지 못했습니다.
- **한계 2 — 문서끼리의 불일치.** 공개 날짜(16일·17일)와 이전 모델의 등급 표기가 자료마다 다릅니다. 인용할 때는 시스템 카드 원문의 날짜와 판정을 기준으로 삼아야 합니다.
- **한계 3 — 접근 제한은 오남용을 줄일 뿐 없애지 못합니다.** 승인을 받은 계정이 탈취되거나, 위험한 작업을 무해한 작업처럼 나눠 요청하는 경우는 모니터링이 잡아야 하는 영역으로 남습니다.

## 내 프로젝트와 연결

- **한끼 Agent**에서는 모델이 고른 도구가 등록 목록에 없으면 코드가 버리고, 키와 원문 예외는 사용자 응답과 실행 기록에서 뺐습니다. 모델의 능력이 아니라 "허용된 작업 목록"으로 범위를 정한 방식이라, 이번 사례의 기능별 승인과 같은 방향입니다. 다만 Daybreak처럼 **사용자 등급에 따라 기능을 여는 단계는 없었습니다.** 붙인다면 위 의사코드처럼 승인 등급과 요청 표시를 함께 확인하겠습니다.
- **데이터 에이전트**는 SQL을 읽기 전용으로 막았지만 사용자별 권한은 나누지 않았습니다.

## 면접 질문

**Q. 보안 능력이 높은 모델을 사내 도구에 붙인다면, 어떤 통제를 먼저 두겠습니까?**

> 기능을 사용자 등급과 요청 단위로 나눠 열겠습니다. 기본값은 위험한 작업을 거절하는 쪽으로 두고, 업무상 필요한 사람만 승인을 받게 하되 승인이 있어도 요청마다 명시적으로 켜게 하고, 사용 기록은 계속 남기겠습니다. 한끼 Agent에서는 등록되지 않은 도구 호출을 코드가 버렸고, 데이터 에이전트에서는 SQL을 읽기 전용으로 막았습니다. 사용자 등급별 권한은 구현하지 않았기 때문에, 그 부분을 도구 호출 앞단에 추가하는 것부터 하겠습니다.

## 출처

- OpenAI Deployment Safety Hub, [GPT-6.2 System Card](https://deploymentsafety.openai.com/gpt-6-2-astra-sol) · [PDF](https://deploymentsafety.openai.com/gpt-6-2-astra-sol/gpt-6-2-astra-sol.pdf) — 2026-11-17, 영역별 등급, Daybreak 조건, ExploitBench (공식 도메인 검색 발췌로 확인)
- OpenAI, [Introducing GPT-6.2 Astra and Sol](https://openai.com/index/introducing-gpt-6-2-astra-sol/)
- OpenAI Developer Community, [GPT-6.2 Astra and Sol are now available](https://community.openai.com/t/gpt-6-2-astra-and-sol-are-now-available/1417531)
- OpenAI Help Center, [OpenAI Daybreak — Trusted Access for Cyber overview](https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview)
- OpenAI, [Preparedness Framework v2 (2025-04-15)](https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf) — 배포 전 안전장치, Critical 사이버 기준
- OpenAI Deployment Safety Hub, [GPT-6 Astra System Card](https://deploymentsafety.openai.com/gpt-6-astra) — 이전 모델 등급 표기 비교
