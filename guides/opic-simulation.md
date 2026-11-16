# OPIc 형식 독립 모의시험

확인일: 2026-11-16. 본 기능은 공식 시험이 아닌 독자적인 연습용 구현입니다.

## 공식 안내에서 확인한 절차

- 국내 공식 시험 소개: https://www.opic.co.kr/opics/servlet/controller.opic.site.about.AboutServlet?p_process=move-introduce-opic
- 국내 시험 관리 규정: https://www.opic.co.kr/opics/servlet/controller.opic.site.applyinfor.ActflTestRuleServlet?p_process=move-actfl_test_rule
- ACTFL 일반 안내: https://www.actfl.org/assessments/postsecondary-assessments/oral-proficiency-interview-computer-opic
- ACTFL Familiarization Guide: https://www.actfl.org/uploads/files/general/OPIc_Familiarization_Guide.pdf

국내 공개 안내는 사전 설문, 자기평가, 음성·녹음 점검, 샘플 질문의 오리엔테이션과 본시험으로 구분합니다. 오리엔테이션은 약 20분, 본시험은 40분이며 문항은 12~15개입니다. 문항별 답변시간 제한은 없고 질문은 두 번 청취할 수 있습니다. 첫 세션 약 7문항 후 난이도를 다시 고르며 이후 약 5~8문항을 진행합니다. 국제 일반 안내와 국내 운영 방식의 차이는 있을 수 있으므로 국내 절차를 시간·문항수의 기준으로 삼았습니다.

## 그대로 복제하지 않은 부분

- 공식 브랜드 화면·인물·문항·녹음·자기평가 음성 샘플을 복제하지 않았습니다.
- 간소화한 배경 설문과 6단계 연습 설명, 관련 문항 묶음·역할극·예상 밖 상황 프롬프트는 자체 연습 모형입니다. 실제 설문 항목과 선택 수, 난이도별 문항수 배정·출제 알고리즘을 안다고 주장하지 않습니다.
- 12/15문항 길이를 연습자가 선택합니다. 7문항 뒤 쉬운/비슷한/어려운 변화를 자체 모형에 적용합니다. 주제 선택을 바탕으로 문항을 만들되 회사 면접 질문은 섞지 않습니다.
- 질문 음성은 OS/브라우저의 영어 TTS입니다. 공식 녹음과 목소리·억양·속도가 같지 않습니다. 영어 음성이 없는 브라우저에서는 실전 모드 대신 명확히 구분한 텍스트 학습 모드를 제공합니다.
- 전체 40분은 질문 재생·재청취·난이도 조정·답변·다음 문항 전환 중 계속 흐릅니다. 문항별 2분 타이머는 사용하지 않습니다.
- 시험 중 일시정지·이전 문항 돌아가기·힌트·모범답변·자기채점은 제공하지 않습니다. 이동 제한은 집중 연습을 위한 시뮬레이터 정책으로 안내하며 비공개 실제 UI와 완전히 같다고 주장하지 않습니다.
- 공식 서버 전송·본인 인증·감독·공인 채점은 구현하지 않습니다. 공식 등급·IH/AL 예측 점수를 표시하지 않습니다. 시험 후 질문과 녹음을 복습하고 FACT(기능, 정확성, 맥락·내용, 발화 구성) 관점으로 스스로 점검하도록 안내합니다.

## 저장·오류 처리

마이크 사전 점검에서 목소리를 녹음·재생해 확인합니다. 본시험에서는 질문 재생 후 자동 녹음하고, 재청취 중에는 녹음을 일시적으로 멈춰 질문 음성이 답변에 섞이는 것을 줄입니다. 헤드폰 사용을 권장합니다. OS·브라우저 오디오 장치에 따라 실제 음질은 별도 확인이 필요합니다.

완료된 문항 녹음은 이 브라우저의 IndexedDB에 저장하고 재생·개별 다운로드·전체 ZIP 내보내기를 제공합니다. IndexedDB를 사용할 수 없으면 메모리 보관으로 표시하며 이 경우 탭을 닫으면 녹음이 사라집니다. 녹음은 외부 서버에 보내지 않습니다. 일반 진행 기록 JSON에는 오디오가 포함되지 않습니다.

새로고침·브라우저 종료 시 현재 문항은 유실될 수 있고 이미 저장된 문항만 복구할 수 있습니다. 화면 이탈은 확인 후 중단 처리하며 재개를 위해 시간을 멈추지 않습니다. 모의시험 기록·녹음 삭제 버튼을 제공합니다. 오디오 자체는 별도 ZIP으로 백업하세요.

## 검증

- `node --test tests/interview.test.cjs tests/opic.test.cjs`
- `python tests/render_interview_fixture.py`
- `node tests/opic-browser.cjs` (Playwright 설치 필요)

브라우저 검사는 가짜 마이크와 TTS로 12/15문항 전체 세션, 청취 2회 제한, 문항별 자동 종료가 없는 동작, 전체 시간 초과, 중간 난이도 조정, IndexedDB 영속성과 ZIP 다운로드를 검사합니다. 실제 사용자 OS 음성·마이크와 공식 시험 간 일치성은 이 검사로 증명하지 않습니다.

## 화면 참고

LTI의 HRSA 공개 발표 자료(2024) 22쪽 시험 화면을 참고해 왼쪽 인터뷰어, 오른쪽 문항 진행 표시·녹음 상태, 오른쪽 아래 Next 배치를 반영했습니다. 공식 아바타·상표·문항·음성은 복제하지 않았습니다. 이 자료만으로 2026년 국내 시험장 화면과 동일하다고 검증할 수 없습니다.
https://www.hrsa.gov/sites/default/files/hrsa/advisory-committees/national-health-service-corps/quinlan-son-language-test-international-nacnhsc-meeting-2024.pdf
