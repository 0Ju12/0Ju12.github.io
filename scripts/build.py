#!/usr/bin/env python3
"""data/portfolio.yaml 하나로 모든 포트폴리오 결과물을 생성합니다.

생성물
  docs/index.html   웹 포트폴리오 (GitHub Pages로 배포)
  docs/resume.html  인쇄용 이력서 (scripts/pdf.js 로 PDF 변환)
  out/notion.md     노션에 붙여넣을 포트폴리오 문서
  out/profiles.md   LinkedIn·원티드·리멤버용 프로필 문구
  out/warnings.md   보완이 필요한 항목 체크리스트
"""
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "portfolio.yaml"
TEMPLATES = ROOT / "templates"
DOCS = ROOT / "docs"
OUT = ROOT / "out"

NUMBER = re.compile(r"\d")


def clean_links(links):
    return [l for l in (links or []) if l.get("url")]


def period_str(p):
    if not p:
        return ""
    start, end = p.get("start", ""), p.get("end", "")
    if start and end:
        return f"{start} – {end}"
    return f"~ {end}" if end else start


def sort_key(a):
    # 최근에 끝난(또는 진행 중인) 활동이 먼저 오도록: 종료일 → 시작일 내림차순
    p = a.get("period") or {}
    end = str(p.get("end", ""))
    if not end or not end[:1].isdigit():  # "재학 중", "현재" 등
        end = "9999"
    return (end, str(p.get("start", "")))


def normalize(data):
    data["_todos"] = [
        f'{a.get("title")} — {x}'
        for a in data.get("activities") or []
        for k in ("action", "result")
        for x in (a.get("star") or {}).get(k) or []
        if str(x).startswith("TODO")
    ]
    data["profile"]["links"] = clean_links(data["profile"].get("links"))
    acts = data.get("activities") or []
    for a in acts:
        a["links"] = clean_links(a.get("links"))
        a.setdefault("star", {})
        for k in ("action", "result"):
            # 'TODO' 로 시작하는 항목은 결과물에 표시하지 않고 체크리스트로만 보냄
            a["star"][k] = [x for x in (a["star"].get(k) or []) if x and not str(x).startswith("TODO")]
        a["period_str"] = period_str(a.get("period"))
    acts.sort(key=sort_key, reverse=True)
    data["activities"] = acts
    # 사진 자동 연결: docs/assets/photos/<활동 id>/*.jpg → gallery, profile.jpg → 프로필
    photos = DOCS / "assets" / "photos"
    for a in acts:
        d = photos / a.get("id", "")
        a["gallery"] = [
            {"src": f"assets/photos/{a['id']}/{f.name}", "caption": f.stem.replace("_", " ")}
            for f in sorted(d.glob("*.jpg"))
        ] if d.is_dir() else []
    if not data["profile"].get("photo") and (photos / "profile.jpg").exists():
        data["profile"]["photo"] = "assets/photos/profile.jpg"
    data["featured"] = sorted((a for a in acts if a.get("featured")), key=lambda a: a.get("priority", 99))
    data["types"] = sorted({a.get("type", "기타") for a in acts})
    for e in data.get("education") or []:
        e["period_str"] = period_str(e.get("period"))
    pubs = sorted(data.get("publications") or [], key=lambda x: str(x.get("year", "")), reverse=True)
    data["papers"] = [x for x in pubs if x.get("kind") == "논문"]
    data["talks"] = [x for x in pubs if x.get("kind") != "논문"]
    data["skills"] = [s for s in data.get("skills") or [] if s.get("items")]
    data["certifications"] = data.get("certifications") or []
    data["highlights"] = data.get("highlights") or []
    data["awards"] = data.get("awards") or []
    return data


def collect_warnings(data):
    w = []
    p = data["profile"]
    if "입력하세요" in p.get("name", ""):
        w.append("profile.name — 이름을 입력하세요")
    if "입력하세요" in p.get("title", ""):
        w.append("profile.title — 희망 직무를 입력하세요 (직무에 맞춰 활동 강조점이 달라집니다)")
    for e in data.get("education") or []:
        if "입력하세요" in e.get("major", ""):
            w.append("education.major — 전공을 입력하세요")

    text = yaml.safe_dump({k: v for k, v in data.items() if k != "_todos"}, allow_unicode=True)
    n_sample = text.count("[예시]")
    if n_sample:
        w.append(f"[예시] 샘플 문구가 {n_sample}곳 남아 있습니다")

    for t in data["_todos"]:
        w.append(f"{t}")

    if not data["featured"]:
        w.append("featured: true 인 대표 활동이 없습니다 (3~5개 권장)")
    elif len(data["featured"]) > 5:
        w.append(f"대표 활동이 {len(data['featured'])}개 — 3~5개로 줄이면 더 효과적입니다")

    for a in data["activities"]:
        name = a.get("title", a.get("id"))
        s = a["star"]
        if not s.get("situation") or not s.get("task"):
            w.append(f"{name} — STAR의 상황/과제가 비어 있습니다")
        if not s.get("action"):
            w.append(f"{name} — 내가 한 일(action)이 비어 있습니다")
        if not s.get("result"):
            w.append(f"{name} — 결과(result)가 비어 있습니다")
        elif not any(NUMBER.search(r) for r in s["result"]):
            w.append(f"{name} — 결과에 숫자(성과 지표)가 없습니다")
        if a.get("featured") and not a["links"]:
            w.append(f"{name} — 대표 활동인데 증빙 링크(GitHub·발표자료 등)가 없습니다")
    return w


def main():
    data = normalize(yaml.safe_load(DATA.read_text(encoding="utf-8")))
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html", "j2"], default_for_string=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    md_env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, lstrip_blocks=True)

    DOCS.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    site_tpl = env.get_template("site.html.j2")
    theme = (data.get("site") or {}).get("theme", "minimal")
    layout = (data.get("site") or {}).get("layout")  # sidebar | bento | showcase (templates/layouts/)
    if layout:
        html = env.get_template(f"layouts/{layout}.html.j2").render(**data)
    else:
        html = site_tpl.render(theme=theme, **data)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    # 디자인 비교용 미리보기: python3 scripts/build.py --previews  → docs/design-<테마>.html
    for t in [] if "--previews" not in sys.argv else sorted(x.stem for x in (TEMPLATES / "themes").glob("*.css")):
        (DOCS / f"design-{t}.html").write_text(site_tpl.render(theme=t, **data), encoding="utf-8")
    (DOCS / "resume.html").write_text(env.get_template("resume.html.j2").render(**data), encoding="utf-8")
    (DOCS / "resume-1page.html").write_text(env.get_template("resume-1page.html.j2").render(**data), encoding="utf-8")
    (OUT / "notion.md").write_text(md_env.get_template("notion.md.j2").render(**data), encoding="utf-8")
    (OUT / "profiles.md").write_text(md_env.get_template("profiles.md.j2").render(**data), encoding="utf-8")

    warnings = collect_warnings(data)
    report = "# 보완 체크리스트\n\n" + (
        "\n".join(f"- [ ] {x}" for x in warnings) if warnings else "모든 항목이 채워졌습니다. 🎉"
    ) + "\n"
    (OUT / "warnings.md").write_text(report, encoding="utf-8")

    print("✔ docs/index.html, docs/resume.html, out/notion.md, out/profiles.md 생성 완료")
    print(f"⚠ 보완 필요 {len(warnings)}건 → out/warnings.md" if warnings else "✔ 보완 필요 항목 없음")
    if "--strict" in sys.argv and warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
