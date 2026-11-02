# 이영주 · 데이터·AI 엔지니어 포트폴리오

**🔗 https://0ju12.github.io**

복잡한 지구과학 데이터를 딥러닝과 분석으로 풀어내는 데이터·AI 엔지니어 이영주의 포트폴리오 사이트 소스입니다.

| | |
|---|---|
| 대표 프로젝트 | [산불 확산 예측 U-LSTM](https://github.com/0Ju12/wildfire-spread-prediction) · [SSAFY 관통 프로젝트 ThRead](https://github.com/0Ju12/ssafy-thread) · FLAN-T5+RAG 영어 교정(포스코 AI 아카데미) |
| 연구 | SCIE SPE Journal 제1저자 · 논문 3편 · 학회 발표 10건 |
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
