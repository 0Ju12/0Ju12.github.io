---
title: "LLM 응답을 믿지 않는 파이프라인 설계"
date: "2026-11-02"
summary: "LLM에는 판단만 맡기고, 결과는 코드로 검증한다. 댓글 분석 파이프라인과 AI 도서 추천을 만들며 정한 네 가지 원칙."
tags: [LLM, 데이터 파이프라인, Django, 검증]
project: ssafy-16
repo: "https://github.com/0Ju12/ssafy-thread"
---

SSAFY 관통 프로젝트에서 LLM을 붙인 기능을 두 번 만들었습니다. 주식 커뮤니티 댓글을 수집해 정제·증강·요약하는 **데이터 파이프라인**(관통 5)과, 회원 정보를 보고 책을 골라 주는 **AI 도서 추천**(관통 4)입니다.

처음에는 "LLM에게 결과물을 통째로 만들게 하면 편하겠다"고 생각했습니다. 그런데 실제로 돌려 보니 LLM은 **가끔** 틀립니다. 개수를 하나 빼먹고, 없는 책을 지어내고, JSON 앞에 설명을 붙입니다. 문제는 '가끔'이라서, 테스트 몇 번으로는 드러나지 않는다는 점이었습니다.

그래서 설계 원칙을 하나로 정했습니다.

> **LLM에는 판단만 맡기고, 결과는 코드로 검증한다.**

## 1. 원본을 고치게 하지 말고, 번호만 받는다

부적절한 댓글을 걸러낼 때, LLM에게 "부적절한 댓글을 뺀 목록을 돌려줘"라고 하면 LLM이 남은 댓글을 **다시 써서** 돌려줍니다. 띄어쓰기가 바뀌거나 문장이 살짝 다듬어져 원본과 비교할 수 없게 됩니다.

대신 **제거할 댓글의 번호만** 받고, 실제 제거는 코드가 합니다.

```python
numbers = parse_json_array(response)
if numbers is None:
    # 형식 오류를 성공으로 취급하지 않는다
    raise LLMError('부적절 댓글 판정 응답이 유효한 JSON 배열이 아닙니다.')

# 정수이면서 실제 댓글 번호 범위 안인 값만 사용 (중복 제거 후 정렬)
to_remove = sorted({n for n in numbers if type(n) is int and 0 <= n < len(comments)})

# 앞에서부터 지우면 뒤쪽 번호가 밀리므로 뒤에서부터 제거
kept = list(comments)
for i in reversed(to_remove):
    removed.append(kept.pop(i))
```

여기에 검증이 세 겹 들어 있습니다.

- 응답이 JSON 배열이 아니면 **실패로 처리**합니다. 빈 배열로 간주하면 "부적절한 댓글이 없다"는 잘못된 결론이 됩니다.
- `type(n) is int`로 정수만 남깁니다. `"3"`이나 `3.0`, `true`(파이썬에서 `bool`은 `int`의 하위 클래스입니다)를 걸러냅니다.
- 범위 밖 번호와 중복 번호를 버립니다.

그리고 **뒤에서부터** 지웁니다. 앞에서부터 `pop(2)`, `pop(5)`를 하면 첫 번째 삭제 뒤 5번이 원래 6번 댓글을 가리키게 됩니다. 사소해 보이지만, 놓치면 에러 없이 엉뚱한 댓글이 지워지는 종류의 버그입니다.

## 2. 개수와 형식이 맞지 않으면 재시도한다

댓글 증강은 "같은 의미, 다른 표현"의 문장을 만드는 작업입니다. 결과가 원본과 **1:1로 짝**이 맞아야 학습 데이터로 쓸 수 있습니다.

```python
for attempt in range(1, max_attempts + 1):
    augmented = parse_json_array(run_llm(build_augment_prompt(comments)))
    if augmented is None:
        continue
    if len(augmented) != len(comments):          # 개수 불일치
        continue
    if any(not isinstance(a, str) or not a.strip() for a in augmented):
        continue                                  # null·숫자·빈 문장
    ...
    return [a.strip() for a in augmented]
return []
```

20개를 넣었는데 19개가 돌아오면, 어느 하나가 빠졌는지 알 수 없습니다. 이때 앞에서부터 짝을 지으면 **모든 쌍이 한 칸씩 어긋난** 데이터가 조용히 저장됩니다. 그래서 개수가 다르면 그 결과는 버리고 다시 요청하고, 정해진 횟수 안에 성공하지 못하면 빈 결과를 돌려줘 화면에 실패를 알립니다.

금융 댓글이라는 특성도 반영했습니다. "-3% 하락"이 "3% 상승"으로 바뀌면 의미가 정반대가 되므로, 증강 전후로 **숫자·부호·상승/하락 방향·종목명**이 바뀐 문장이 있으면 그 결과도 재시도합니다.

## 3. 목록에 없는 것은 받아들이지 않는다

AI 도서 추천에서는 LLM에게 등록된 도서 목록(id, 제목, 저자 등)을 주고 몇 권을 고르게 했습니다. LLM은 종종 **목록에 없는 유명한 책**을 추천합니다. 그럴듯하지만 우리 서비스에는 없는 책입니다.

```python
by_id = {book.pk: book for book in books}
for item in data.get('recommendations', []):
    try:
        book_id = int(item.get('id'))
    except (TypeError, ValueError, AttributeError):
        continue
    # 목록에 없는 id(AI가 지어낸 책) · 중복은 버림
    if book_id in by_id and book_id not in seen:
        seen.add(book_id)
        results.append({'id': book_id, 'title': by_id[book_id].title, ...})
```

제목과 저자도 LLM 응답이 아니라 **DB의 값**으로 채웁니다. LLM이 제목을 살짝 틀리게 적어도 화면에는 정확한 정보가 나갑니다. LLM에게서 받는 것은 "어떤 id를, 왜 골랐는지"뿐입니다.

## 4. 실패해도 서비스는 멈추지 않는다

LLM API는 느리고, 가끔 실패합니다. 그래서 LLM 호출은 공통 함수 하나로 모으고, 실패를 구분해 다뤘습니다.

- 키가 없거나 호출이 실패해도 **도서 등록 자체는 저장**되고, "AI 작가 정보를 만들지 못했다"는 안내만 보여 줍니다.
- 30초 넘게 걸리는 댓글 분석은 단계별 진행 상황을 `StreamingHttpResponse`(NDJSON)로 보내 화면에 실시간으로 보여 주고, "회사 없음 / 댓글 없음 / LLM 실패"를 구분해 안내합니다.

## 검증은 테스트로 고정한다

이런 규칙은 말로만 정해 두면 금방 깨집니다. 그래서 LLM 호출을 `mock`으로 바꿔, **일부러 틀린 응답**을 주는 테스트를 만들었습니다.

- 번호에 범위 밖 값·문자열·중복이 섞인 응답
- 개수가 하나 모자란 증강 응답
- 목록에 없는 id가 섞인 추천 응답
- API 호출 자체가 실패하는 경우

외부 API 없이 실행되고, 관통 4·5를 합쳐 **자동 테스트 86개**가 이 규칙들을 지키고 있습니다.

## 정리

LLM은 "무엇이 부적절한지", "어떤 책이 어울리는지" 같은 **판단**을 잘합니다. 하지만 원본을 보존하고, 개수를 맞추고, 존재하는 데이터만 쓰는 일은 코드가 훨씬 정확합니다. 역할을 이렇게 나누고 나니, LLM 응답이 가끔 틀려도 서비스의 데이터는 틀리지 않게 되었습니다.

데이터 파이프라인에 LLM을 넣을 때도 같은 원칙을 적용하려고 합니다. **LLM의 출력은 입력 데이터처럼 검증한다.**
