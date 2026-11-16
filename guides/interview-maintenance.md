# 면접 준비 앱: 기록·녹음·자료 상태 개선

## 변경 내용

- `templates/interview/`에 저장·백업 병합, 질문, 모의 면접, 발표, 자소서, 공채, 이력서, 알고리즘, NCS, 음성 분석, 자료 상태 모듈 분리.
- 모듈은 Jinja include로 빌드 시 합쳐집니다. 개인 질문·답변을 외부 JS 파일로 내보내지 않습니다.
- 기존 `interview-app-v1` 기록과 v1 백업 유지. 별표 변경 시각, 빈 메모, 지원 카드·수동 알고리즘 기록의 삭제 이력을 보존합니다. 백업은 검증 후 복사본에 병합하여 실패 시 기존 기록을 유지합니다.
- 전체 초기화 이전 백업의 의도치 않은 복원을 차단합니다. 예전 백업을 의도적으로 복원해야 하면 초기화하지 않은 별도 브라우저에서 가져오세요.
- 같은 브라우저의 다른 탭에서 변경한 기록은 storage 이벤트로 병합합니다. 다른 기기 사이에는 여전히 백업 파일이 필요하며 클라우드 동기화 서버는 추가하지 않습니다.
- 녹음은 dataavailable/stop 이벤트 후 재생합니다. 권한 승인을 기다리는 동안 취소하거나 화면을 바꾸면 나중에 열린 마이크도 종료합니다. 녹음별 스트림·청크를 격리합니다. 브라우저가 종료 이벤트를 보내지 않으면 8초 후 자원을 해제하고 녹음 없이 진행합니다.
- 음성 받아쓰기는 최종 종료 이벤트를 기다립니다(브라우저가 응답하지 않으면 2초 후 현재 결과 사용). 음성 인식은 브라우저 제공자의 서버 처리가 포함될 수 있습니다.
- `자료 현황`에 빌드 시각, 원본별 확인일, 최신 배포 여부 표시. 7일이 지난 확인일은 재확인 안내. 분석 방식은 규칙 기반이며 AI 채점·OPIc 등급 판정이 아님을 표시합니다.
- `docs/interview/version.json`은 배포 버전과 빌드 시각만 담습니다. 개인 본문이나 질문 수는 포함하지 않습니다. 실시간 원본 동기화 기능은 아닙니다.

## 적용

1. 배포 전 현재 앱의 `도구 → 기록 · 기기 옮기기`에서 백업하세요.
2. 패치 파일을 저장소 루트에서 `git apply interview-improvements.patch`로 적용하거나 ZIP의 `changes/` 파일을 동일한 경로에 복사하세요. 패치는 함께 제공한 BASE_COMMIT.txt 기준입니다. 다른 수정과 충돌하면 `git apply --check`로 먼저 확인하세요.
3. 커밋 후 main에 반영하면 기존 GitHub Actions가 테스트·빌드·암호화·배포합니다. `PRIVATE_KEY`, `STUDY_PASSWORD` 또는 `PRIVATE_PASSWORD`는 기존 설정을 사용합니다. 비밀 값을 공유할 필요가 없습니다.
4. 배포 후 `/interview/index.html`에서 잠금을 해제하고 `자료 현황`을 열어 새 빌드 시각을 확인하세요. 생성된 docs 파일을 수동으로 덮어쓸 필요가 없습니다.

## 검증 명령

Python: `pip install jinja2 pyyaml markdown cryptography pypdf`

- `node --test tests/interview.test.cjs`
- `python -m unittest discover -s tests -p 'test_*.py'`
- `python tests/render_interview_fixture.py`
- `npm install playwright@1.47.2 && npx playwright install --with-deps chromium`
- `node tests/interview-browser.cjs`

설치된 Chromium을 쓰려면 `CHROMIUM_PATH=/usr/bin/chromium`을 지정합니다. 브라우저 테스트는 합성 질문 한 개로 실행하며 개인키·실제 개인 답변을 읽지 않습니다. 음성 장치 이벤트는 단위 테스트에서 모의합니다. 실제 마이크와 브라우저 제공자 음성 인식 품질은 사용자 기기에서 확인해야 합니다.

## 자료 기반 1분 답변 초안

패치에 `content/private_sealed/interview_drafts_json.sealed.json`이 포함되어 있습니다. 이 파일은 저장소의 기존 공개키로 잠갔으며, 배포가 기존 PRIVATE_KEY로 풀어 질문에 합칩니다. 비밀번호나 개인키를 공유하지 않아도 됩니다.

초안을 로컬에서 다시 수정할 때 개인 초안 파일은 공개 저장소에 평문으로 커밋하지 않습니다. 별도 다운로드한 `interview_drafts.json`을 로컬 `content/private/interview_drafts.json`에 넣고 `python scripts/private_seal.py interview_drafts.json`으로 잠근 결과만 커밋하세요. 빌드에서 기존 `PRIVATE_KEY`로 복호화해 다른 질문과 합칩니다.

앱의 `내 답변 초안`에서 답변을 편집하면 브라우저에 자동 저장되고 모의 면접의 비교 답변에도 반영됩니다. `원래 초안으로`는 배포에 포함된 초안으로 되돌립니다. 편집 내용은 기존 기록 백업에 포함되며 JSON/Markdown으로 별도 내보낼 수도 있습니다. JSON 가져오기는 ID 또는 정확히 같은 질문으로 매칭한 답변만 바꾸며, 알 수 없는 질문은 건너뛰었다고 표시합니다.

기존 암호화된 개인 질문은행의 원문 전체를 읽은 것은 아닙니다. 이번 새 초안집은 공개 포트폴리오·회고·AI 글·회사별 준비 자료를 기반으로 작성했습니다. 실전 답변 전에 본인의 의사, 역할, 최신 자격과 채용 정보를 확인하세요. 예상 소요 시간은 글자 수 기반의 참고값입니다.

## OPIc 실전 모드

기존 유형별 2분 랜덤 연습 대신 `OPIc 실전` 메뉴를 사용하세요. 사전 설문·난이도·장치 확인 뒤 40분 전체 타이머, 두 번 청취, 7문항 후 난이도 재조정, 시험 종료 후 녹음 복습·ZIP 내보내기를 제공합니다. 공식과의 차이와 저장 방식은 `guides/opic-simulation.md`에 명시했습니다.
