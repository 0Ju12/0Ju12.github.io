#!/usr/bin/env python3
"""이력서 잠금: docs/resume*.html · docs/resume*.pdf → 암호로만 여는 docs/cv.html + docs/cv/*.enc

CI(배포)에서 PDF 생성·점검이 끝난 뒤 실행합니다. 평문 이력서는 배포 결과와 git 어디에도 남기지 않습니다.
  RESUME_PASSWORD=... python3 scripts/lock_resumes.py     # 비우면 PRIVATE_PASSWORD 사용
암호가 없으면 평문만 지우고 '암호 미설정' 안내 페이지를 둡니다.
"""
import base64, json, os, re, sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ITER = 600_000
ITEMS = [
    {"name": "resume-1page", "label": "이력서 1장", "sub": "요약본 · 한국어"},
    {"name": "resume-data", "label": "직무별 1장 — 데이터 엔지니어", "sub": "한국어"},
    {"name": "resume-ai", "label": "직무별 1장 — AI·ML 엔지니어", "sub": "한국어"},
    {"name": "resume", "label": "상세 이력서", "sub": "3쪽 · 한국어"},
    {"name": "resume-1page-en", "label": "Resume (1 page)", "sub": "English"},
    {"name": "resume-en", "label": "Full CV", "sub": "English"},
]


def env():
    e = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html", "j2"]))
    import yaml
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import build
    e.globals["analytics"] = build.analytics()
    return e


def placeholder():
    """build.py 가 매번 쓰는 기본 페이지 (암호 없음 → 파일 없이 안내만)"""
    (DOCS / "cv.html").write_text(env().get_template("cv_lock.html.j2").render(box=None, items=ITEMS), encoding="utf-8")


def main():
    pw = os.environ.get("RESUME_PASSWORD") or os.environ.get("PRIVATE_PASSWORD")
    e = lambda b: base64.b64encode(b).decode()
    box = None
    if pw:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        salt = os.urandom(16)
        aes = AESGCM(PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode()))
        def seal(data):
            iv = os.urandom(12)
            return {"iv": e(iv), "ct": e(aes.encrypt(iv, data, None))}
        out = DOCS / "cv"
        out.mkdir(exist_ok=True)
        for it in ITEMS:
            for ext in ("html", "pdf"):
                src = DOCS / f"{it['name']}.{ext}"
                if not src.exists():
                    sys.exit(f"✗ {src.name} 없음 — build.py · pdf.js 를 먼저 실행하세요")
                (out / f"{it['name']}.{ext}.enc").write_text(json.dumps(seal(src.read_bytes())), encoding="utf-8")
        box = {"salt": e(salt), "iter": ITER, "check": seal(b"ok")}
    (DOCS / "cv.html").write_text(env().get_template("cv_lock.html.j2").render(box=box, items=ITEMS), encoding="utf-8")

    # 평문 이력서 제거 + 옛 주소는 cv.html 로 넘기는 안내 페이지
    stub = '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=cv.html"><a href="cv.html">이력서 · Resume</a>'
    for p in DOCS.glob("resume*.pdf"):
        p.unlink()
    for p in DOCS.glob("resume*.html"):
        p.write_text(stub, encoding="utf-8")
    # 사이트 곳곳의 이력서 링크 → cv.html
    pat = re.compile(r'((?:href|data-[a-z]+)=")((?:\.\./)*)resume(?:-[a-z0-9]+)*\.(?:pdf|html)(")')
    n = 0
    for p in list(DOCS.glob("*.html")) + list(DOCS.glob("*/*.html")):
        if p.name.startswith("resume") or p.parent.name == "cv":
            continue
        s = p.read_text(encoding="utf-8")
        t = pat.sub(lambda m: m.group(1) + m.group(2) + "cv.html" + m.group(3), s)
        t = re.sub(r'(href="(?:\.\./)*cv\.html"[^>]*?) download(?=[ >])', r"\1", t)
        if t != s:
            p.write_text(t, encoding="utf-8"); n += 1
    print(f"✔ 이력서 잠금 {'완료' if box else '(암호 없음: 파일 미포함)'} · 링크 고친 페이지 {n}개")


if __name__ == "__main__":
    main()
