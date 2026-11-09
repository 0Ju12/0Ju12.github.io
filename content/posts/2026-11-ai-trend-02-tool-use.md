---
title: "Tool use — 모델은 함수를 실행하지 않는다"
date: "2026-11-09"
summary: "Function calling의 실제 동작(모델은 호출 '요청'만 만들고 실행은 내 코드가 한다), strict 스키마와 Structured Outputs의 관계, 도구를 쓸 때와 출력 형식만 고정할 때를 구분했습니다."
tags: [Tool use, Function calling, Structured Outputs]
series: ai-trend
episode: 2
next_topic: "#3 MCP — 도구를 매번 새로 붙이지 않는 방법"
---

> **한 줄 요약** — "모델이 함수를 호출한다"는 말은 정확하지 않습니다. 모델은 **어떤 함수를 어떤 인자로 부르고 싶은지 구조화된 요청**을 만들 뿐이고, 실행·검증·권한 판단은 전부 애플리케이션 코드의 몫입니다.

## 핵심 개념

- **흐름**: ① 개발자가 도구 이름·설명·입력 스키마(JSON Schema)를 모델에 알려 줌 → ② 모델이 필요하다고 판단하면 `tool_use`(호출 요청)를 응답 → ③ 내 코드가 실제로 실행 → ④ 결과를 `tool_result`로 다시 넣어 주면 모델이 이어서 답합니다.
- **이름은 달라도 같은 구조**: OpenAI는 function calling, Anthropic은 tool use라고 부르지만 "모델은 요청, 실행은 코드"라는 구조는 같습니다. Anthropic 문서도 Claude가 직접 실행하는 일은 없다고 명시합니다(서버에서 대신 실행해 주는 '서버 도구'는 예외).
- **비유**: 모델은 주문서를 쓰는 점원이고, 주방(내 코드)이 주문서를 보고 요리할지, 재료가 있는지, 이 손님에게 팔아도 되는지를 결정합니다.

## 지금 무슨 일이 일어나고 있나

- **strict 스키마가 기본값이 되는 중입니다.** OpenAI 문서는 function calling에서 strict 모드를 "항상 켜라"고 권하며, 이때 모든 객체에 `additionalProperties: false`, 모든 필드를 required로 두고 선택 필드는 `null` 허용으로 표현해야 한다고 설명합니다. strict 모드는 내부적으로 Structured Outputs 기능을 씁니다.
- **API마다 기본 동작이 다릅니다.** 같은 문서 기준으로 Responses API는 strict를 생략하면 strict를 먼저 시도하고, Chat Completions는 기본이 non-strict입니다. "같은 모델이니 같겠지"라고 가정하면 안 되는 부분입니다.
- **병렬 호출은 짝 맞추기가 핵심입니다.** Anthropic 문서는 한 번에 여러 도구를 요청받으면 각 결과를 `tool_use_id`로 짝지어, 다음 메시지에 한꺼번에 돌려줘야 한다고 정해 둡니다. 실패한 호출은 `is_error`로 표시해 모델이 다른 방법을 찾게 할 수 있습니다.
- **도구 목록이 커지는 문제**: 도구가 수십~수백 개가 되면 설명만으로 컨텍스트가 찹니다. Anthropic은 필요한 도구만 검색해서 불러오는 tool search 도구를 문서에 따로 두고 있습니다. 이 "도구를 어떻게 연결·관리하나"가 다음 회차 MCP로 이어지는 문제입니다.

## 동작 구조

```
사용자 ──▶ 모델 ──(tool_use: get_book, {"isbn": "..."})──▶ 내 코드
                                                         ├ 스키마 검증
                                                         ├ 권한·한도 확인
                                                         └ 실제 실행 (DB/API)
          모델 ◀──(tool_result: {...} 또는 is_error)──────┘
          모델 ──▶ 최종 답변
```

```python
call = response.tool_use                      # 모델이 만든 '요청'
args = BookQuery.model_validate(call.input)   # 1) 스키마 검증 (실패하면 is_error 로 돌려줌)
if not allowed(user, call.name):              # 2) 이 사용자가 이 도구를 써도 되나
    return tool_error(call.id, "not allowed")
result = TOOLS[call.name](**args.model_dump())# 3) 실행은 항상 내 코드
return tool_result(call.id, result)
```

## 도구를 쓸 때 vs 형식만 고정할 때

| 상황 | 쓸 것 |
|---|---|
| 출력 모양이 이미 정해져 있다 (분류 결과, 점수, 판정) | **Structured Outputs** (`response_format` / `text.format` + strict 스키마) |
| 모델이 여러 행동 중 고르거나, 행동할지 말지를 정해야 한다 | **Tool use** |
| 결과를 보고 다음 행동을 이어 가야 한다 | Tool use + 루프 (= 지난 회차의 에이전트) |

## 왜 중요한가 / 한계

- **중요한 이유**: LLM이 바깥 세계(DB, 검색, 결제, 파일)와 닿는 유일한 통로가 이 구조입니다. 에이전트의 신뢰성은 결국 "도구 호출 요청을 코드가 얼마나 잘 걸러 내는가"로 결정됩니다.
- **한계**: 스키마는 **형식**만 보장합니다. `{"isbn": "123"}`처럼 형식은 맞지만 틀린 값, 혹은 사용자가 시킨 적 없는 행동 요청(프롬프트 인젝션)은 스키마로 막을 수 없습니다. 의미 검증과 권한 확인은 코드에 따로 있어야 합니다.
- **비용·지연**: 도구 한 번마다 왕복이 생깁니다. 루프가 길어지면 사용자 화면의 응답 시간이 빠르게 늘어납니다.

## 내 프로젝트와 연결

- **관통 7 AI 프록시**의 Guardrail·라우트·점수는 표의 첫 줄, 즉 **Structured Outputs** 쪽이었습니다. 행동을 고르는 게 아니라 정해진 모양의 판정이 필요했기 때문에 `strict: true` 스키마로 받고, 코드에서 타입·범위·enum을 한 번 더 확인했습니다. 형식이 깨지면 통과가 아니라 503으로 막았습니다.
- **관통 4·5**에서는 LLM이 "부적절한 댓글 번호", "추천 도서 id"만 내놓게 하고, 번호 범위·등록된 id인지를 코드가 확인한 뒤에만 반영했습니다. 위 의사코드의 1)·2)에 해당하는 일을 도구 없이 해 본 셈입니다.
- 이 경험을 tool use로 옮긴다면, 도구 인자 검증 실패를 예외로 끝내지 않고 `is_error` 결과로 모델에게 돌려줘 스스로 고치게 하는 부분을 더하겠습니다.

## 면접 질문

**Q. Function calling에서 모델이 잘못된 인자를 만들면 어떻게 처리하나요?**

> 모델은 호출 요청만 만들고 실행은 제 코드가 하므로, 실행 전에 세 단계를 둡니다. 스키마 검증(strict 스키마 + Pydantic), 의미 검증(존재하는 id인지, 범위 안인지), 권한 확인입니다. 실패하면 서버 오류로 끝내지 않고 오류 내용을 도구 결과로 돌려줘 모델이 다시 시도하게 하고, 재시도 횟수는 제한합니다. 출력 모양만 필요한 판정은 도구가 아니라 Structured Outputs로 받는데, 관통 7 프록시에서 Guardrail을 그렇게 만들고 형식이 깨지면 막도록 했습니다.

## 출처

- OpenAI, [Function calling](https://developers.openai.com/api/docs/guides/function-calling) · [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs) · [Introducing Structured Outputs in the API](https://openai.com/index/introducing-structured-outputs-in-the-api/)
- Anthropic (Claude Platform Docs), [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) · [How tool use works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works) · [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) · [Tool search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
