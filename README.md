# 이영주 · 데이터 엔지니어 · 데이터 분석가 포트폴리오

**🔗 https://0ju12.github.io**

[![Deploy portfolio](https://github.com/0Ju12/0Ju12.github.io/actions/workflows/deploy.yml/badge.svg)](https://github.com/0Ju12/0Ju12.github.io/actions/workflows/deploy.yml) — push할 때마다 빌드 → 점검(깨진 링크·이미지, 1쪽 이력서, 휴대폰·데스크톱 화면 넘침) → 통과하면 배포

공개 데이터를 모으고 정제해 검증할 수 있는 지표와 분석으로 만드는 데이터 엔지니어·분석가 이영주의 포트폴리오 사이트 소스입니다.

| | |
|---|---|
| 대표 프로젝트 | [공개 데이터 웨어하우스(dbt·Airflow)](https://github.com/0Ju12/data-projects) · [한끼 — 냉장고 생활 코치 Agent (SSAFY)](https://github.com/0Ju12/ai-agents) · [석사 연구 코드 gravmag-wcf](https://github.com/0Ju12/gravmag-wcf) |
| 연구 | SCIE SPE Journal 제1저자 · 논문 3편 · 학회 발표 6건 |
| 이력서 | [1장 요약 PDF](https://0ju12.github.io/resume-1page.pdf) · [상세 PDF](https://0ju12.github.io/resume.pdf) |
| 연락 | iyju990312@naver.com |

## 구성
`data/portfolio.yaml` 하나와 `content/posts/*.md`(블로그 글)를 고치면 웹사이트, PDF 이력서, 노션용 문서가 자동으로 만들어지고 GitHub Actions로 배포됩니다.

```
data/portfolio.yaml   모든 활동·학력·논문 데이터
content/posts/        기술 블로그 글 (Markdown)
templates/            사이트·이력서 템플릿 (Jinja2)
scripts/              build.py (HTML 생성) · pdf.js (PDF 생성)
docs/                 배포되는 결과물
```
빌드 방법은 [guides/00_빌드_사용법.md](guides/00_빌드_사용법.md)에 있습니다.
