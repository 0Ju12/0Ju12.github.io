#!/usr/bin/env python3
"""배포 전 사이트 점검 — 깨진 링크·이미지, 1쪽 이력서, 필수 파일, 링크 미리보기 태그, 영문 페이지 한국어 잔여

    python3 scripts/check_site.py      # 문제가 있으면 목록을 출력하고 종료 코드 1
build.py / pdf.js 실행 뒤에 돌립니다. GitHub Actions(deploy.yml)에서 배포 전에 자동 실행됩니다.
"""
import re, sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
errors, warnings = [], []

# 1) 모든 HTML의 로컬 링크·이미지가 실제 파일을 가리키는지
pages = sorted(p for p in DOCS.rglob("*.html") if "design-" not in p.name)
# 강의 노트(study/notes)는 예제 코드 속 경로(style.css, {% url %} 등)가 그대로 들어 있어 링크 검사에서 제외
link_pages = [p for p in pages if "study/notes" not in p.as_posix()]
for page in link_pages:
    html = page.read_text(encoding="utf-8", errors="ignore")
    for url in set(re.findall(r'(?:src|href)="([^"]+)"', html)):
        if url.startswith(("http:", "https:", "mailto:", "tel:", "data:", "#", "javascript:")) or "{{" in url:
            continue
        path = url.split("#")[0].split("?")[0]
        if not path:
            continue
        target = (page.parent / path).resolve()
        if path.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            errors.append(f"깨진 링크: {page.relative_to(DOCS)} → {url}")

# 2) 1쪽 이력서는 반드시 1쪽
try:
    from pypdf import PdfReader
    for name in ["resume-1page", "resume-1page-en", "resume-data", "resume-ai"]:
        f = DOCS / f"{name}.pdf"
        if not f.exists():
            errors.append(f"이력서 없음: {name}.pdf")
            continue
        n = len(PdfReader(str(f)).pages)
        if n != 1:
            errors.append(f"{name}.pdf 가 {n}쪽입니다 (1쪽이어야 함)")
except ImportError:
    warnings.append("pypdf 가 없어 이력서 쪽수를 확인하지 못했습니다 (pip install pypdf)")

# 3) 꼭 있어야 하는 파일
for rel in ["index.html", "en.html", "resume.pdf", "resume-en.pdf", "og.png", "og-en.png", "favicon.svg",
            "apple-touch-icon.png", "study/index.html", "private/index.html"]:
    if not (DOCS / rel).exists():
        errors.append(f"필수 파일 없음: {rel}")
if not list((DOCS / "projects").glob("*.html")):
    errors.append("프로젝트 상세 페이지(docs/projects/*.html)가 없습니다")

# 4) 링크 미리보기(Open Graph) 태그
for rel in ["index.html", "en.html"] + [f"projects/{p.name}" for p in (DOCS / "projects").glob("*.html")]:
    html = (DOCS / rel).read_text(encoding="utf-8") if (DOCS / rel).exists() else ""
    for prop in ["og:title", "og:description", "og:image"]:
        if f'property="{prop}"' not in html:
            errors.append(f"{rel}: {prop} 태그 없음")

# 5) 영문 페이지에 번역되지 않은 한국어 (경고만)
ALLOW = {"한국어"}
for f in [DOCS / "en.html"] + sorted((DOCS / "projects").glob("*-en.html")):
    text = re.sub(r"<style.*?</style>|<script.*?</script>|<!--.*?-->|(?:src|href|alt|title)=\"[^\"]*\"", "",
                  f.read_text(encoding="utf-8"), flags=re.S)
    left = sorted({m.strip() for m in re.findall(r"[가-힣][가-힣 ·]*", text)} - ALLOW)
    if left:
        warnings.append(f"{f.relative_to(DOCS)}: 번역 안 된 한국어 {left[:5]}")

for w in warnings:
    print("⚠", w)
for e in errors:
    print("✗", e)
print(f"점검한 페이지 {len(pages)}개 · 오류 {len(errors)} · 경고 {len(warnings)}")
sys.exit(1 if errors else 0)
