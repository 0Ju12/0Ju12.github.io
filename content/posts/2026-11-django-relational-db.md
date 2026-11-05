---
title: "책·쓰레드·댓글을 하나의 관계형 모델로 묶기"
date: "2026-11-05"
summary: "관통 6에서 회원·도서·쓰레드·댓글 관계를 설계하며 정한 것들 — 순환 참조 마이그레이션, 지워질 때 남길 것과 지울 것, 남의 글에 404를 주는 이유, 외부 도서 정보를 서명 토큰으로 묶은 방법."
tags: [Django, 데이터베이스, ORM, 설계]
project: ssafy-16
repo: "https://github.com/0Ju12/ssafy-thread/tree/main/06-relational-db"
---

SSAFY 관통 프로젝트 6회차는 **관계형 DB 설계**였습니다. 지난 회차까지는 도서 페이지, 회원 페이지가 따로 움직였는데, 이번에는 회원이 책을 등록하고, 그 책에 독서 기록(쓰레드)을 쓰고, 다른 회원이 좋아요와 댓글을 다는 흐름을 **하나의 데이터 모델**로 묶어야 했습니다.

2인 팀에서 백엔드와 DB를 맡았습니다. 화면을 만들기 전에 관계부터 그려 두니, 이후 뷰와 템플릿에서 고민할 거리가 확 줄었습니다.

```
User ─┬─ 1:N ─ Book ─ 1:N ─ Thread ─ 1:N ─ Comment
      ├─ M:N ─ User      (팔로우, 방향 있음)
      ├─ M:N ─ Thread    (좋아요)
      └─ M:N ─ Category  (선호 장르)
Category ─ 1:N ─ Book
```

## 1. 팔로우는 대칭이 아니다

Django에서 자기 자신을 가리키는 M:N(`'self'`)은 기본이 **대칭**입니다. A가 B를 추가하면 B도 A를 가진 것으로 취급합니다. 친구 관계라면 맞지만 팔로우는 아닙니다.

```python
followings = models.ManyToManyField(
    'self', symmetrical=False, related_name='followers', blank=True)
```

`symmetrical=False`를 주면 `user.followings`(내가 팔로우한 사람)와 `user.followers`(나를 팔로우한 사람)가 서로 다른 집합이 됩니다. 자기 자신을 팔로우하는 요청은 뷰에서 막았습니다.

## 2. 서로를 참조하는 두 모델과 마이그레이션 순서

회원은 선호 장르(`Category`)를 고르고, 도서는 작성자(`User`)를 가집니다. `accounts`가 `books`를, `books`가 `accounts`를 참조하는 구조라 초기 마이그레이션을 한 번에 만들면 **순환 의존**이 생깁니다.

그래서 마이그레이션을 세 단계로 나눴습니다.

1. `accounts/0001` — 선호 장르 **없이** User 생성
2. `books/0001` — Category·Book·Thread·Comment 생성 (User 참조)
3. `accounts/0002` — User에 `favorite_categories` 필드 추가 (Category 참조)

커스텀 User는 프로젝트 첫 마이그레이션 전에 `AUTH_USER_MODEL`로 지정해야 합니다. 기본 `auth.User`로 시작한 DB에 나중에 바꾸면 되돌리기 어렵기 때문에, 이 부분을 가장 먼저 정했습니다.

## 3. 지워질 때 무엇을 남길지

외래 키마다 `on_delete`를 정하는 건 "삭제되면 무엇이 같이 사라져야 하는가"를 정하는 일이었습니다.

| 관계 | 선택 | 이유 |
|---|---|---|
| 작성자 → 도서·쓰레드·댓글 | `CASCADE` | 탈퇴한 회원의 글은 남기지 않음 |
| 도서 → 쓰레드 → 댓글 | `CASCADE` | 대상이 사라진 기록은 의미가 없음 |
| 장르 → 도서 | `SET_NULL` | 장르를 정리해도 회원이 쓴 도서는 남아야 함 |

장르는 관리자가 바꿀 수 있는 **분류**이고, 도서는 회원이 만든 **데이터**입니다. 분류를 지웠다고 데이터가 사라지면 안 된다는 기준으로 나눴습니다.

## 4. 남의 글은 403이 아니라 404

수정·삭제는 이렇게 조회합니다.

```python
book = get_object_or_404(Book, pk=pk, user=request.user)
```

작성자가 아니면 "권한 없음"이 아니라 **"없음"**이 됩니다. 권한 확인을 따로 하지 않아도 되고, 남의 글이 존재하는지조차 드러나지 않습니다. 삭제·좋아요·팔로우·댓글처럼 상태를 바꾸는 요청은 `@require_POST`로 막아서, 링크를 누르거나 이미지 태그에 URL이 들어가는 것만으로는 아무 일도 일어나지 않게 했습니다.

## 5. 외부 도서 정보는 서명해서 넘긴다

알라딘에서 책을 검색해 등록 폼을 채우는 기능을 붙였습니다. 처음 떠오른 방법은 검색 결과의 ISBN·표지 URL을 hidden input에 넣는 것이었는데, 그러면 사용자가 값을 바꿔 제출해도 그대로 저장됩니다.

그래서 선택한 책 정보를 Django `signing`으로 서명한 토큰에 담아 넘기고, 저장할 때 다시 검증했습니다.

```python
selected = read_token(request.POST.get('aladin_token', ''))   # 위조·만료(1시간)면 None
...
if selected and book.title == selected['title'] and book.author == selected['author']:
    book.aladin_isbn13 = selected['isbn13'][:13]
    book.aladin_cover_url = selected['cover'][:500]
```

토큰이 깨졌으면 저장 자체를 거부하고, 사용자가 제목이나 저자를 바꿨다면 일반 등록으로 취급해 **외부 메타데이터를 붙이지 않습니다**. 검색 결과를 바로 DB에 넣지 않고, 사용자가 평점·장르를 정해 제출할 때만 저장되는 것도 같은 이유입니다.

## 6. 직접 돌려서 확인한 것

팀 작업 당시 환경에서는 Django를 설치하지 못해 실행 확인을 미뤄 둔 상태였습니다. 저장소에 올리기 전에 Python 3.13 · Django 5.2.19 환경에서 처음부터 다시 실행했습니다.

```
manage.py check                           → no issues
makemigrations --check --dry-run          → No changes detected
migrate                                   → 전체 적용
test accounts books                       → Ran 36 tests ... OK
```

테스트는 권한(남의 글 수정·삭제 404, 비로그인 변경 요청 차단, GET으로 삭제 405), 관계(팔로우 토글, 좋아요 토글, 댓글), 그리고 토큰 위조·만료 거부를 다룹니다. 외부 API는 mock으로만 확인했습니다. 저장소의 화면도 이때 로컬 서버를 띄워 직접 캡처한 것입니다.

## 정리

- 관계를 먼저 그리면 뷰는 거의 "조회 조건"만 남는다 — `user=request.user` 하나로 권한이 끝난다.
- `on_delete`는 기술 옵션이 아니라 "무엇이 데이터이고 무엇이 분류인가"에 대한 결정이다.
- 클라이언트를 거쳐 돌아오는 값은 서명하거나 다시 검증한다 — LLM 응답을 코드로 검증하던 관통 4·5의 원칙과 같은 이야기였다.
