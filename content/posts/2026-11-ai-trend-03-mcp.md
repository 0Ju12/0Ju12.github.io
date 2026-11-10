---
title: "MCP — 도구를 매번 새로 붙이지 않는 방법"
date: "2026-11-10"
summary: "지난 회차의 tool use를 앱마다 다시 만들지 않도록 '도구 서버'를 표준 규격으로 분리한 MCP의 구조(호스트·클라이언트·서버, tools·resources·prompts)와 최근 사양 변화, 보안상 약한 고리를 정리했습니다."
tags: [MCP, AI 에이전트, 프로토콜]
series: ai-trend
episode: 3
next_topic: "#4 에이전트 간 통신 — A2A는 MCP와 무엇이 다른가"
---

> **한 줄 요약** — 지난 회차에서 "모델은 호출을 요청하고 실행은 내 코드가 한다"고 정리했습니다. MCP는 그 '내 코드' 쪽을 **앱 밖의 서버로 떼어 내고, 연결 방식을 규격으로 맞춘 것**입니다. 도구를 한 번 서버로 만들면 여러 AI 앱이 같은 방식으로 붙여 쓸 수 있습니다.

## 핵심 개념

- **문제**: #2의 구조대로라면 앱마다 도구 정의·실행·인증 코드를 따로 씁니다. 앱이 M개, 연결할 시스템(DB·드라이브·이슈 트래커)이 N개면 M×N개의 연결을 만들게 됩니다.
- **MCP(Model Context Protocol)**: 그 연결을 **M+N**으로 줄이려는 공개 규격입니다. 시스템 쪽은 MCP 서버를 한 번 만들고, AI 앱은 MCP 클라이언트를 한 번 구현하면 서로 붙습니다.
- **비유**: 노트북마다 전용 충전기를 들고 다니다가 USB-C 하나로 맞춘 것과 비슷합니다. 단, 규격이 같아졌다고 아무 충전기나 믿고 꽂으면 안 된다는 점(보안)까지 비슷합니다.

## 지금 무슨 일이 일어나고 있나

- **관리 주체가 바뀌었습니다.** Anthropic은 2025년 12월 MCP를 Linux Foundation 산하의 Agentic AI Foundation(AAIF)에 기증했습니다. 이 재단은 Anthropic·Block·OpenAI가 함께 세웠고, Block의 goose, OpenAI의 AGENTS.md와 함께 MCP가 첫 프로젝트가 됐습니다. 한 회사의 규격이 아니라 중립 규격으로 가겠다는 신호입니다.
- **사양이 날짜 단위로 개정됩니다.** 2025-11-25 개정에서는 오래 걸리는 요청을 추적하는 **tasks**(실험 기능)와, 필요한 권한만 그때그때 더 요청하는 인증 방식이 들어갔습니다. 2026-07-28 개정에서는 tasks가 핵심 규격에서 빠져 공식 확장(`io.modelcontextprotocol/tasks`)으로 옮겨졌고, 인증 응답에 발급자(`iss`)를 넣어 클라이언트가 검증하게 하는 규칙(RFC 9207)이 추가됐습니다. 기능을 넣었다가 확장으로 빼는 식으로, 아직 규격이 굳는 중이라는 뜻입니다.
- **보안 연구가 빠르게 늘고 있습니다.** 2026년 arXiv 논문 두 편이 각각 Claude Code·Cursor·Gemini CLI 등 MCP 클라이언트 7종의 도구 오염(tool poisoning) 대응을 실험하고, 사양 자체의 약점(출처 인증 없는 sampling, 여러 서버를 붙였을 때 신뢰가 번지는 문제)을 분석했습니다. Cloud Security Alliance 연구 노트는 OWASP가 MCP Top 10에서 도구 오염을 3번째 항목으로 올렸다고 정리합니다. 블로그마다 "취약 서버 몇 %" 같은 수치가 돌지만 1차 출처가 확인되지 않는 것이 많아 여기서는 옮기지 않습니다.

## 동작 구조

```
┌─────────── 호스트 (Claude Desktop, IDE, 내 앱) ───────────┐
│  LLM                                                     │
│   ↕ tool_use / tool_result (#2와 같은 구조)               │
│  MCP 클라이언트 A ── JSON-RPC 2.0 ──▶ MCP 서버: 드라이브   │
│  MCP 클라이언트 B ── JSON-RPC 2.0 ──▶ MCP 서버: 사내 DB    │
└──────────────────────────────────────────────────────────┘
연결 방식: 같은 컴퓨터면 stdio, 원격이면 Streamable HTTP
```

서버가 내놓는 것은 세 종류입니다.

| 종류 | 누가 쓰나 | 예 |
|---|---|---|
| **tools** | 모델이 고름 (#2의 도구) | `search_issues`, `create_page` |
| **resources** | 앱이 컨텍스트로 넣음 | 파일 내용, DB 스키마 |
| **prompts** | 사용자가 고름 | "이 PR 리뷰해 줘" 같은 템플릿 |

반대 방향으로 서버가 클라이언트에 요청하는 기능도 있습니다. 모델 호출을 대신 부탁하는 **sampling**, 사용자에게 추가 입력을 받는 **elicitation** 등입니다. 위 보안 논문들이 짚은 지점이 바로 이 sampling 쪽입니다.

```python
# 클라이언트 쪽 흐름 (개념)
tools = mcp_client.list_tools()              # 서버가 가진 도구 목록과 입력 스키마
resp = llm.create(messages, tools=tools)     # #2와 동일: 모델은 '요청'만 만듦
if resp.tool_use:
    if not policy.allows(resp.tool_use):     # 호스트가 권한·사용자 확인을 맡음
        return deny()
    result = mcp_client.call_tool(resp.tool_use.name, resp.tool_use.input)
```

## 왜 중요한가 / 한계

- **중요한 이유**: 도구를 한 번 만들면 여러 AI 앱에서 재사용할 수 있고, 키·권한 같은 민감한 부분을 서버 쪽 경계 안에 둘 수 있습니다. 에이전트가 쓸 수 있는 도구의 수가 늘어나는 기반이 됩니다.
- **한계 1 — 서버를 믿는 문제**: 도구 설명문은 모델이 그대로 읽습니다. 설명에 "이 도구를 쓰기 전에 ~ 파일 내용을 함께 보내라" 같은 지시가 숨어 있으면(도구 오염) 모델이 따라갈 수 있습니다. 규격이 같다는 것과 그 서버를 믿어도 된다는 것은 별개입니다.
- **한계 2 — 규격 변화**: 위에서 본 것처럼 tasks가 1년 안에 들어왔다가 확장으로 옮겨졌습니다. 서버·클라이언트가 지원하는 사양 버전을 확인하지 않으면 같은 MCP여도 동작이 다릅니다.
- **한계 3 — 도구가 많아질 때**: 서버를 여러 개 붙이면 도구 목록 자체가 컨텍스트를 차지합니다. #2에서 본 tool search처럼 필요한 도구만 불러오는 방식이 함께 쓰입니다.

## 내 프로젝트와 연결

- MCP를 직접 구현해 본 적은 없습니다. 다만 **관통 7 AI 프록시**는 같은 문제의식에서 나온 구조였습니다. Django가 모델 키·모델 선택·응답 검증을 직접 갖지 않고, FastAPI 프록시 한곳에 모아 경계를 만들었습니다. MCP 서버가 "도구 실행과 비밀"을 앱 밖으로 떼어 내는 것과 같은 방향입니다.
- 프록시에서 Guardrail 응답 형식이 깨지면 통과시키지 않고 503으로 막았던 **fail-closed** 원칙은, MCP에서 출처를 확인하지 못한 서버 요청(sampling 등)을 기본 거부하는 정책으로 옮길 수 있다고 봅니다.
- **국보 RAG 가이드**에서 위키 문서를 가져와 ChromaDB에 넣던 부분을 MCP로 다시 만든다면, 위키·오픈API 수집을 resources/tools 서버로 분리하고 답변 쪽(LangGraph)은 클라이언트로 두는 구성이 됩니다. 근거 번호를 코드로 검증하는 단계는 여전히 호스트 쪽에 남아야 합니다.

## 면접 질문

**Q. MCP를 쓰면 function calling은 필요 없나요?**

> 아닙니다. MCP는 function calling을 대체하는 것이 아니라 그 바깥을 표준화한 것입니다. 모델이 도구 호출을 요청하는 부분은 그대로이고, MCP는 그 도구를 어디서 어떤 형식으로 가져오고 실행할지를 맞춥니다. 그래서 MCP를 써도 권한 확인과 결과 검증은 호스트가 해야 합니다. 특히 도구 설명문은 모델이 그대로 읽기 때문에, 신뢰하지 않는 서버의 도구는 허용 목록으로 제한하고 민감한 호출은 사용자 확인을 받도록 하겠습니다. 관통 7에서 키와 검증을 프록시 한곳에 모으고 형식이 깨지면 막았던 것과 같은 원칙입니다.

## 출처

- Model Context Protocol, [Specification changelog (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/changelog) · [Specification changelog (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- Anthropic, [Donating the Model Context Protocol and establishing the Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) · MCP Blog, [MCP joins the Agentic AI Foundation](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/)
- arXiv, [Are AI-assisted Development Tools Immune to Prompt Injection? (2603.21642)](https://arxiv.org/abs/2603.21642) · [arXiv 2601.17549](https://arxiv.org/abs/2601.17549)
- Cloud Security Alliance, [MCP Attack Surface: Tool Poisoning and IDE Auto-Execution](https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-tool-poisoning-auto-execution-20260701/)
