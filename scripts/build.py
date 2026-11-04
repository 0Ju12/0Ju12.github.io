#!/usr/bin/env python3
"""data/portfolio.yaml 하나로 모든 포트폴리오 결과물을 생성합니다.

생성물
  docs/index.html   웹 포트폴리오 (GitHub Pages로 배포)
  docs/resume.html  인쇄용 이력서 (scripts/pdf.js 로 PDF 변환)
  out/notion.md     노션에 붙여넣을 포트폴리오 문서
  out/profiles.md   LinkedIn·원티드·리멤버용 프로필 문구
  out/warnings.md   보완이 필요한 항목 체크리스트
"""
import json
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
        for g in data.get("activities") or []
        for a in [g] + (g.get("projects") or [])
        for k in ("action", "result")
        for x in (a.get("star") or {}).get(k) or []
        if str(x).startswith("TODO")
    ]
    data["profile"]["links"] = clean_links(data["profile"].get("links"))
    acts = data.get("activities") or []
    photos = DOCS / "assets" / "photos"

    def prep(a):
        a["links"] = clean_links(a.get("links"))
        a.setdefault("star", {})
        for k in ("action", "result"):
            # 'TODO' 로 시작하는 항목은 결과물에 표시하지 않고 체크리스트로만 보냄
            a["star"][k] = [x for x in (a["star"].get(k) or []) if x and not str(x).startswith("TODO")]
        a["period_str"] = period_str(a.get("period"))
        # 사진 자동 연결: docs/assets/photos/<id>/*.jpg → gallery
        d = photos / a.get("id", "")
        a["gallery"] = [
            {"src": f"assets/photos/{a['id']}/{f.name}", "caption": f.stem.replace("_", " ")}
            for f in sorted(d.glob("*.jpg"))
        ] if d.is_dir() else []
        # 카드 전용 잘라낸 그림: docs/assets/photos/<id>/card/*.jpg (갤러리에는 넣지 않음)
        cards = sorted((d / "card").glob("*.jpg")) if (d / "card").is_dir() else []
        if cards:
            a["card_image"] = f"assets/photos/{a['id']}/card/{cards[0].name}"
            a["card_caption"] = cards[0].stem.replace("_", " ")

    for a in acts:
        prep(a)
        # 묶음 활동(projects): 하위 프로젝트를 각각 정리하고, 하위 내용을 모은 star 를 만들어
        # 하위 구조를 모르는 템플릿(노션·프로필 문구 등)에서도 내용이 빠지지 않게 함
        subs = a.get("projects") or []
        for sp in subs:
            prep(sp)
        a["projects"] = subs
        a["project_ids"] = [a["id"]] + [sp["id"] for sp in subs]
        if subs and not (a["star"]["action"] or a["star"]["result"]):
            short = lambda sp: sp.get("short") or sp["title"].split(" — ")[0]
            a["star"]["action"] = [f"[{short(sp)}] {x}" for sp in subs for x in sp["star"]["action"]]
            a["star"]["result"] = [f"[{short(sp)}] {x}" for sp in subs for x in sp["star"]["result"]]
            a["links"] = a["links"] or [l for sp in subs for l in sp["links"]]
    acts.sort(key=sort_key, reverse=True)
    data["activities"] = acts
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
    cn = DATA.parent / "case_notes.yaml"   # 프로젝트 상세 페이지용 트레이드오프·회고·데모·구조도
    notes = yaml.safe_load(cn.read_text(encoding="utf-8")) if cn.exists() else {}
    for g in data.get("activities") or []:
        for sp in g.get("projects") or []:
            sp["case"] = notes.get(sp.get("id")) or {}
    data["career_map"] = career_map()
    rv = DATA.parent / "resume_variants.yaml"   # 직무별 보기(사이트)·직무별 이력서 공용
    data["role_variants"] = yaml.safe_load(rv.read_text(encoding="utf-8")) if rv.exists() else {}
    pi = DATA.parent / "projects_index.yaml"   # 디자인 시안용 프로젝트 단위 목록
    data["projects_index"] = yaml.safe_load(pi.read_text(encoding="utf-8")) if pi.exists() else []
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

    for a in (x for g in data["activities"] for x in (g["projects"] or [g])):
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


def load_posts(acts):
    """content/posts/*.md (YAML front matter + Markdown) → 글 목록"""
    import markdown
    titles = {a.get("id"): a.get("title") for g in acts for a in [g] + (g.get("projects") or [])}
    posts = []
    for f in sorted((ROOT / "content" / "posts").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        _, fm, body = raw.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        if meta.get("draft"):
            continue
        meta["slug"] = f.stem
        meta["html"] = markdown.markdown(body, extensions=["fenced_code", "tables"])
        meta["project_title"] = titles.get(meta.get("project"))
        posts.append(meta)
    return sorted(posts, key=lambda p: (str(p.get("date", "")), p["slug"]), reverse=True)


def _equal_earth(lon, lat, k, tx, ty):
    """d3.geoEqualEarth 와 같은 공식 — data/geo/basemap.json 의 k·tx·ty 로 화면 좌표 계산"""
    import math
    A1, A2, A3, A4, M = 1.340264, -0.081106, 0.000893, 0.003796, math.sqrt(3) / 2
    lam, phi = math.radians(lon), math.radians(lat)
    l = math.asin(M * math.sin(phi)); l2 = l * l; l6 = l2 * l2 * l2
    x = lam * math.cos(l) / (M * (A1 + 3 * A2 * l2 + l6 * (7 * A3 + 9 * A4 * l2)))
    y = l * (A1 + A2 * l2 + l6 * (A3 + A4 * l2))
    return round(x * k + tx, 1), round(-y * k + ty, 1)


def _mercator(lon, lat, k, tx, ty):
    import math
    lam, phi = math.radians(lon), math.radians(lat)
    return round(lam * k + tx, 1), round(-math.log(math.tan(math.pi / 4 + phi / 2)) * k + ty, 1)


def career_map():
    """data/career_map.yaml + data/geo/basemap.json → 템플릿용 지도 데이터 (없으면 None)"""
    f, g = DATA.parent / "career_map.yaml", DATA.parent / "geo" / "basemap.json"
    if not (f.exists() and g.exists()):
        return None
    base = json.loads(g.read_text(encoding="utf-8"))
    w, kr = base["world"], base["korea"]
    places = yaml.safe_load(f.read_text(encoding="utf-8")) or []
    for pl in places:
        pl["x"], pl["y"] = _equal_earth(pl["lon"], pl["lat"], w["k"], w["tx"], w["ty"])
        if pl.get("inset"):
            pl["ix"], pl["iy"] = _mercator(pl["lon"], pl["lat"], kr["k"], kr["tx"], kr["ty"])
    # 세계 지도에서 가까운 점(30px 이내)은 하나의 묶음 표시로 — 휴대폰에서도 누를 수 있게
    rank = {"stay": 0, "partner": 1, "data": 2}
    groups = []
    for pl in sorted((p for p in places if not p.get("inset")), key=lambda p: rank[p["layer"]]):
        for gr in groups:
            if ((gr["x"] - pl["x"]) ** 2 + (gr["y"] - pl["y"]) ** 2) ** 0.5 <= 30:
                gr["members"].append(pl["id"]); break
        else:
            groups.append({"x": pl["x"], "y": pl["y"], "members": [pl["id"]], "layer": pl["layer"], "label": pl.get("label")})
    byid = {p["id"]: p for p in places}
    for gr in groups:
        gr["layers"] = sorted({byid[m]["layer"] for m in gr["members"]}, key=rank.get)
        gr["label"] = gr["label"] or any(byid[m].get("label") for m in gr["members"])
    return {"base": base, "places": places, "groups": groups}


def evidence_index(data, en=False):
    """기술 태그 → 근거 연결용: 하위 프로젝트(상세 페이지)와 글의 검색용 텍스트. 사이트 JS가 태그와 대조."""
    stacks = {}
    for x in data.get("projects_index") or []:   # 시안용 프로젝트 목록의 도구 이름도 해당 하위 프로젝트의 근거로
        stacks.setdefault(x.get("activity"), []).extend(x.get("stack") or [])
    items = []
    for g in data.get("featured") or []:
        for sp in g.get("projects") or []:
            st = sp.get("star") or {}
            words = [sp.get("title", ""), sp.get("summary", ""), st.get("situation", ""), st.get("task", "")]
            words += (st.get("action") or []) + (st.get("result") or []) + (sp.get("tags") or [])
            if not en:
                words += stacks.get(sp.get("id"), [])
            items.append({"k": "p", "t": sp.get("title", ""), "u": f"projects/{sp['id']}{'-en' if en else ''}.html",
                          "s": " ".join(str(w) for w in words).lower()})
    for w in data.get("posts") or []:
        words = [w.get("title", ""), w.get("summary", "")] + list(w.get("tags") or [])
        items.append({"k": "w", "t": w.get("title", ""), "u": f"posts/{w['slug']}.html",
                      "s": " ".join(str(x) for x in words).lower()})
    return items


def _plain(md_text):
    """Markdown → 검색용 평문 (코드 블록·표·링크 문법 제거)"""
    t = re.sub(r"```.*?```", " ", md_text, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[`*_>#|]+", " ", t)
    t = re.sub(r"^\s*[-:]{3,}\s*$", " ", t, flags=re.M)
    return re.sub(r"\s+", " ", t).strip()


def search_index(data, en=False):
    """'포트폴리오에 질문하기'용 문단 색인 → docs/search.json (영문 search-en.json). 브라우저에서 BM25로 검색."""
    sfx = "-en" if en else ""
    home = "en.html" if en else "index.html"
    L = (lambda ko, e: e if en else ko)
    out = []
    def add(text, title, url, sec):
        text = re.sub(r"\s+", " ", str(text or "")).strip()
        if len(text) >= 8:
            out.append({"x": text, "t": title, "u": url, "s": sec})
    prof = data.get("profile") or {}
    add(prof.get("summary"), L("소개", "About"), home + "#top", L("소개", "About"))
    av = prof.get("availability") or {}
    if av.get("role"):
        add(L(f"희망 직무 {av.get('role')} · 입사 가능 {av.get('start','')} · 근무 지역 {av.get('location','')}",
              f"Looking for {av.get('role')} · available {av.get('start','')} · location {av.get('location','')}"),
            L("지원 정보", "Availability"), home + "#top", L("지원 정보", "Availability"))
    for g in data.get("featured") or []:
        add(f"{g.get('title','')} — {g.get('summary','')}", g.get("title", ""), home + "#work", g.get("type", ""))
        for sp in g.get("projects") or []:
            u = f"projects/{sp['id']}{sfx}.html"
            st = sp.get("star") or {}
            add(sp.get("summary"), sp["title"], u, L("요약", "Summary"))
            add(st.get("situation"), sp["title"], u, L("문제", "Problem"))
            add(st.get("task"), sp["title"], u, L("역할", "Role"))
            for x in st.get("action") or []:
                add(x, sp["title"], u, L("한 일", "What I did"))
            for x in st.get("result") or []:
                add(x, sp["title"], u, L("결과", "Results"))
            cl = ((sp.get("case") or {}).get("en" if en else "ko")) or {}
            for x in cl.get("tradeoffs") or []:
                add(x, sp["title"], u + "#tradeoffs", L("설계 판단", "Decisions"))
            for x in cl.get("next") or []:
                add(x, sp["title"], u + "#next", L("돌아보면", "Looking back"))
            if sp.get("tags"):
                add(L("사용 기술: ", "Tools: ") + ", ".join(sp["tags"]), sp["title"], u, L("기술", "Tools"))
    for w in data.get("posts") or []:
        src = (ROOT / "content" / "posts" / f"{w['slug']}.md").read_text(encoding="utf-8").split("---", 2)[-1]
        u = f"posts/{w['slug']}.html"
        add(w.get("summary"), w["title"], u, L("글 요약", "Post"))
        for part in re.split(r"^## ", src, flags=re.M)[1:]:
            head, _, body = part.partition("\n")
            body = _plain(body)
            for i in range(0, len(body), 520):          # 긴 절은 520자 단위로 나눔
                add(body[i:i + 560], w["title"], u, head.strip())
    for x in data.get("papers") or []:
        add(f"{x.get('title','')} — {x.get('venue','')} {x.get('year','')}", L("논문", "Publications"), home + "#about", L("논문", "Paper"))
    for x in data.get("talks") or []:
        add(f"{x.get('title','')} ({x.get('year','')})", L("학회 발표", "Talks"), home + "#about", L("학회 발표", "Talk"))
    for e in data.get("education") or []:
        add(f"{e.get('school','')} {e.get('major','')} {e.get('degree','')} {e.get('period_str','')} " + " ".join(e.get("notes") or []),
            L("학력", "Education"), home + "#about", L("학력", "Education"))
    for x in (data.get("awards") or []) + (data.get("certifications") or []):
        add(f"{x.get('name','')} — {x.get('org','')} {x.get('date','')}", L("수상·자격", "Awards"), home + "#about", L("수상·자격", "Awards"))
    for sk in data.get("skills") or []:
        add(f"{sk.get('category','')}: " + ", ".join(sk.get("items") or []), L("기술", "Skills"), home + "#about", L("기술", "Skills"))
    return out


def project_pages(env, data, en=False):
    """대표 활동의 하위 프로젝트마다 상세 페이지: docs/projects/<id>.html (영문은 <id>-en.html). 생성된 HTML 사전 반환."""
    subs = [(g, sp) for g in data.get("featured") or [] for sp in (g.get("projects") or [])]
    out = {}
    for i, (g, sp) in enumerate(subs):
        prev = subs[i - 1][1] if i > 0 else None
        nxt = subs[i + 1][1] if i + 1 < len(subs) else None
        related = [w for w in data.get("posts") or [] if w.get("project") == sp.get("id")]
        html = env.get_template("project.html.j2").render(
            sp=sp, group=g, prev=prev, next=nxt, related=related, en=en, **data)
        out[f"{sp['id']}{'-en' if en else ''}.html"] = html
    return out


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
    data["posts"] = load_posts(data.get("activities", []))
    data["evidence"] = evidence_index(data)
    (DOCS / "posts").mkdir(exist_ok=True)
    import study
    data["study_notes"] = study.build(env, data)
    import private_build
    data["private_ready"] = private_build.build(env, data)
    for post in data["posts"]:
        (DOCS / "posts" / f"{post['slug']}.html").write_text(
            env.get_template("post.html.j2").render(post=post, **data), encoding="utf-8")
    site_tpl = env.get_template("site.html.j2")
    theme = (data.get("site") or {}).get("theme", "minimal")
    layout = (data.get("site") or {}).get("layout")  # sidebar | bento | showcase (templates/layouts/)
    if layout:
        html = env.get_template(f"layouts/{layout}.html.j2").render(alt_lang={"url": "en.html", "label": "EN", "code": "en"}, **data)
    else:
        html = site_tpl.render(theme=theme, **data)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    # 디자인 비교용 미리보기: python3 scripts/build.py --previews  → docs/design-<테마>.html
    for t in [] if "--previews" not in sys.argv else sorted(x.stem for x in (TEMPLATES / "themes").glob("*.css")):
        (DOCS / f"design-{t}.html").write_text(site_tpl.render(theme=t, **data), encoding="utf-8")
    (DOCS / "search.json").write_text(json.dumps(search_index(data), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DOCS / "projects").mkdir(exist_ok=True)
    for name, html in project_pages(env, data).items():
        (DOCS / "projects" / name).write_text(html, encoding="utf-8")
    (DOCS / "resume.html").write_text(env.get_template("resume.html.j2").render(**data), encoding="utf-8")
    (DOCS / "resume-1page.html").write_text(env.get_template("resume-1page.html.j2").render(**data), encoding="utf-8")
    # 직무별 1쪽 이력서: data/resume_variants.yaml → docs/resume-<key>.html (사실은 portfolio.yaml 것만 재배치)
    variants_file = ROOT / "data" / "resume_variants.yaml"
    for key, v in (yaml.safe_load(variants_file.read_text(encoding="utf-8")) if variants_file.exists() else {}).items():
        by_id = {a.get("id"): a for a in data["featured"]}
        featured = [dict(by_id[i], brief=(v.get("brief") or {}).get(i) or by_id[i].get("brief")) for i in v["order"] if i in by_id]
        vd = dict(data, featured=featured, profile=dict(data["profile"], headline=v["headline"]),
                  highlights=v.get("highlights") or data["highlights"], skills=v.get("skills") or data["skills"],
                  variant_label=v.get("label"))
        (DOCS / f"resume-{key}.html").write_text(env.get_template("resume-1page.html.j2").render(**vd), encoding="utf-8")
    import build_en
    build_en.main()
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
