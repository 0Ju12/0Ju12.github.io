"""준비 공간 → docs/study/index.html (공부 + 면접 + 지원을 한 화면으로, 노트와 같은 암호·같은 키로 잠김)

- 예전에는 강의 노트 앱(docs/study/)과 면접 준비 앱(docs/interview/)이 따로 있어 '오늘' 화면·간격 반복·기록·백업이
  두 벌이었음 → 하나로 합침. docs/interview/ 에는 예전 주소로 들어온 사람을 옮겨 주는 빈 안내 페이지만 남김
- 공부 자료(노트 목록·문제)는 study.build 가 만든 study.APP 을 받아 app["study"] 로 넣음

- 질문 은행: 면접 노트(content/private/interview.json, 배포 빌드에서는 잠긴 묶음을 PRIVATE_KEY 로 풂)
  + 포트폴리오 프로젝트에서 만든 답변 뼈대(digest·case_notes) + AI 트렌드 노트의 면접 질문
- 발표 자료: 직무별 경험 소개·직무·프로젝트별 5~10분 그림 발표 슬라이드 (발표자 메모 포함)
  PDF(브라우저 인쇄)·PPTX(브라우저에서 PptxGenJS 로 생성)는 잠금을 푼 화면에서만 만들어져 평문 파일이 docs/ 에 남지 않음
"""
import json, os, re
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "study"
OLD = ROOT / "docs" / "interview"   # 예전 주소 → 준비 공간으로 옮겨 주는 페이지
PRIVATE_JSON = ROOT / "content" / "private" / "interview.json"
BANK_JSON = ROOT / "content" / "private" / "interview_bank.json"
CATS = ["인성", "프로젝트", "전문지식", "기타", "OPIc"]
GROUP_CAT = {"인성 질문": "인성", "설계 판단 · 트레이드오프": "프로젝트", "RAG · 국보 입문 가이드": "프로젝트", "포트폴리오 기술 질문": "프로젝트"}
PHOTOS = ROOT / "docs" / "assets" / "photos"


_UNSEALED = None


def _private(name, path):
    """로컬 평문이 있으면 그것을, 없으면 잠긴 묶음(content/private_sealed)을 PRIVATE_KEY 로 풀어 씀"""
    global _UNSEALED
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")).get("questions", [])
    pem = os.environ.get("PRIVATE_KEY")
    if not pem:
        return []
    if _UNSEALED is None:
        import private_build
        _UNSEALED = dict(private_build.unseal_all(pem))
    return json.loads(_UNSEALED[name]).get("questions", []) if name in _UNSEALED else []


def _private_questions():
    return _private("interview.json", PRIVATE_JSON)


def _bank_questions():
    """질문 은행: interview_bank.json + 정기 작업이 추가한 interview_bank_<날짜>.json (각각 잠긴 묶음으로만 커밋)

    정기 작업 세션에는 평문 원본과 PRIVATE_KEY 가 없으므로, 새 질문은 별도 파일로 공개키 잠금만 해서 올리고
    배포 빌드가 여기서 모두 합칩니다 (같은 질문 문장은 한 번만)."""
    global _UNSEALED
    names = {f.name for f in (ROOT / "content" / "private").glob("interview_bank*.json")}
    pem = os.environ.get("PRIVATE_KEY")
    if pem:
        if _UNSEALED is None:
            import private_build
            _UNSEALED = dict(private_build.unseal_all(pem))
        names |= {n for n in _UNSEALED if n.startswith("interview_bank") and n.endswith(".json")}
    out, seen = [], set()
    for n in sorted(names):
        for q in _private(n, ROOT / "content" / "private" / n):
            if q.get("q") and q["q"] not in seen:
                seen.add(q["q"]); out.append(q)
    return out


def _group(g):
    g = re.sub(r"\s*\((강사님|Claude 추가)\)\s*", "", g or "개인 추가 질문").strip()
    return g or "개인 추가 질문"


def _projects(data):
    out = []
    for g in data.get("activities") or []:
        for p in g.get("projects") or []:
            if p.get("digest"):
                out.append((g, p))
    return out


def _photo(pid):
    d = PHOTOS / pid
    if not d.exists():
        return ""
    for sub in (d / "card", d):
        fs = sorted([f for f in sub.glob("*.jpg")] + [f for f in sub.glob("*.png")]) if sub.exists() else []
        fs = [f for f in fs if not any(k in f.name for k in ("상장", "표지", "award", "Award"))]
        if fs:
            return "../" + fs[0].relative_to(ROOT / "docs").as_posix()
    return ""


def questions(data, trend_posts):
    qs = []
    for q in _private_questions():
        vs = q.get("versions") or []
        g = _group(q.get("group"))
        qs.append({"id": "n:" + q.get("id", ""), "c": GROUP_CAT.get(g, "기타"), "g": g, "q": q.get("title", ""),
                   "a": vs[-1]["text"] if vs else "", "guide": q.get("guide", ""), "kind": "mine"})
    # User-editable personal drafts remain in the existing private/sealed workflow.
    for b in _private("interview_drafts.json", ROOT / "content" / "private" / "interview_drafts.json"):
        if not b.get("q") or not b.get("a"):
            continue
        qid = b.get("id") or "draft:" + __import__("hashlib").sha256(b["q"].encode()).hexdigest()[:12]
        qs.append({"id": qid, "c": b.get("c") if b.get("c") in CATS else "기타",
                   "g": b.get("g") or "자료 기반 1분 초안", "q": b["q"], "a": b["a"],
                   "kind": "draft", "guide": b.get("guide", ""), "verify": b.get("verify", ""),
                   "tail": b.get("tail") or [], "sources": b.get("sources") or [],
                   "target_seconds": 60, "proposed_position": bool(b.get("proposed_position"))})
    import hashlib
    for b in _bank_questions():
        qs.append({"id": "b:" + hashlib.sha1(b["q"].encode()).hexdigest()[:10], "c": b["c"] if b.get("c") in CATS else "기타",
                   "g": b.get("g") or b["c"], "q": b["q"], "a": b.get("best", ""), "exp": b.get("exp", ""),
                   "intent": b.get("intent", ""), "tail": b.get("tail") or [], "guide": b.get("tip", ""), "kind": "bank"})
    cases = data.get("case_notes") or {}
    for g, p in _projects(data):
        d, short, cn = p["digest"], p.get("short") or p.get("title"), (cases.get(p["id"]) or {}).get("ko") or {}
        link = f"../projects/{p['id']}.html"
        a = "\n".join([f"상황 · {d['problem']}", f"역할 · {d['role']}"] + [f"한 일 · {x}" for x in d.get("did", [])[:3]]
                      + [f"결과 · {x}" for x in d.get("result", [])[:2]])
        qs.append({"id": f"p:{p['id']}:intro", "g": "프로젝트 · " + short, "q": f"{short} — 1분 안에 소개해 주세요.", "a": a,
                   "kind": "skeleton", "link": link, "proj": p["id"], "c": "프로젝트"})
        if cn.get("tradeoffs"):
            qs.append({"id": f"p:{p['id']}:trade", "g": "프로젝트 · " + short, "q": f"{short}에서 가장 고민한 설계 판단은 무엇이었나요?",
                       "a": "\n".join("· " + t for t in cn["tradeoffs"][:2]), "kind": "skeleton", "link": link, "proj": p["id"], "c": "프로젝트"})
        if cn.get("next"):
            qs.append({"id": f"p:{p['id']}:next", "g": "프로젝트 · " + short, "q": f"{short}의 한계는 무엇이고, 다시 한다면 무엇을 바꾸겠습니까?",
                       "a": "\n".join("· " + t for t in cn["next"][:2]), "kind": "skeleton", "link": link, "proj": p["id"], "c": "프로젝트"})
        if d.get("result"):
            qs.append({"id": f"p:{p['id']}:verify", "g": "프로젝트 · " + short, "q": f"{short}의 결과는 어떻게 확인했나요? 숫자로 말해 주세요.",
                       "a": "\n".join("· " + t for t in d["result"]), "kind": "skeleton", "link": link, "proj": p["id"], "c": "프로젝트"})
    for w in trend_posts:
        src = (ROOT / "content" / "posts" / f"{w['slug']}.md").read_text(encoding="utf-8")
        m = re.search(r"## 면접 질문\s+\*\*Q\.\s*(.+?)\*\*\s+((?:>.*\n?)+)", src)
        if m:
            ans = re.sub(r"^>\s?", "", m.group(2).strip(), flags=re.M).strip()
            qs.append({"id": "t:" + w["slug"], "c": "전문지식", "g": "AI 트렌드", "q": m.group(1).strip(), "a": ans, "kind": "trend",
                       "link": f"../posts/{w['slug']}.html", "src": f"AI 트렌드 노트 #{w.get('episode')}"})
    prep = _prep()
    op, types = prep.get("opic") or {}, {t["id"]: t for t in (prep.get("opic") or {}).get("types") or []}
    for i, o in enumerate(op.get("questions") or []):
        t = types.get(o["t"], {})
        qs.append({"id": f"o:{o['t']}:{i}", "c": "OPIc", "g": "OPIc · " + t.get("name", o["t"]), "q": o["q"], "a": (op.get("frames") or {}).get(o["t"], ""),
                   "guide": op.get("tip", "") if o["t"] == "intro" else "", "kind": "opic", "ot": o["t"], "sec": t.get("sec", 120)})
    return qs


def _prep():
    import yaml
    f = ROOT / "data" / "prep.yaml"
    return (yaml.safe_load(f.read_text(encoding="utf-8")) or {}) if f.exists() else {}


def decks(data, variants):
    from career_content import rebuild_decks
    return rebuild_decks(data, variants, _projects(data))


def cv(data):
    """맞춤 이력서용 데이터 (포트폴리오에 있는 사실만)"""
    def per(x):
        x = x or {}
        return f"{x.get('start', '')} – {x.get('end', '')}" if isinstance(x, dict) else str(x)
    prof = data["profile"]
    acts = []
    for g in data.get("activities") or []:
        brief = list(g.get("brief") or [])
        if not brief:
            continue
        acts.append({"title": g.get("card_title") or g.get("title"), "period": per(g.get("period")), "role": g.get("role", ""),
                     "brief": brief, "max": 3 if len(brief) >= 3 else len(brief)})
    pubs = [f"{p_['title']} — {p_['venue']} ({p_['year']})" for p_ in data.get("publications") or [] if p_.get("kind") == "논문"]
    talks = [p_ for p_ in data.get("publications") or [] if p_.get("kind") != "논문"]
    if talks:
        pubs.append(f"학회 발표 {len(talks)}건")
    return {"profile": {"name": prof["name"], "title": prof.get("title", ""), "headline": prof.get("headline", ""), "email": prof.get("email", ""),
                        "links": [l for l in prof.get("links") or [] if "github" in l["url"] or "linkedin" in l["url"]]},
            "acts": acts,
            "edu": [{"school": e["school"], "major": e.get("major", ""), "degree": e.get("degree", ""), "period": per(e.get("period"))} for e in data.get("education") or []],
            "pubs": pubs,
            "awards": [f"{a['name']} ({a.get('date', '')})" for a in data.get("awards") or []],
            "certs": [f"{c['name']} ({c.get('date', '')})" for c in data.get("certifications") or []],
            "skills": data.get("skills") or []}


MOVED = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>준비 공간으로 옮겼습니다</title>
<style>body{margin:0;padding:40px 16px;font:16px/1.6 system-ui,sans-serif;background:#f7f7f8;color:#18181b}@media (prefers-color-scheme:dark){body{background:#0e1116;color:#eef1f5}a{color:#9db8dd}}</style>
<script>location.replace('../study/index.html'+(location.hash||''))</script></head>
<body><p>강의 노트와 면접 준비를 <a href="../study/index.html">준비 공간</a> 하나로 합쳤습니다.</p></body></html>
"""


def build(env, data):
    import yaml, study
    OUT.mkdir(parents=True, exist_ok=True)
    locker = getattr(study, "LOCKER", None) or study.Locker(env, os.environ.get("STUDY_PASSWORD") or os.environ.get("PRIVATE_PASSWORD"))
    variants = yaml.safe_load((ROOT / "data" / "resume_variants.yaml").read_text(encoding="utf-8")) or {}
    data = dict(data)
    data["case_notes"] = yaml.safe_load((ROOT / "data" / "case_notes.yaml").read_text(encoding="utf-8")) or {}
    app = {"questions": questions(data, data.get("trend_posts") or []), "decks": decks(data, variants),
           "roles": {k: v.get("label", k) for k, v in variants.items()}, "name": data["profile"]["name"], "cats": CATS,
           "recruit": yaml.safe_load((ROOT / "data" / "recruit.yaml").read_text(encoding="utf-8")) or {}}
    app["cv"] = cv(data)
    app["pitch"] = data.get("pitch") or {}
    seed_f = ROOT / "data" / "algo_solved.yaml"
    seed = (yaml.safe_load(seed_f.read_text(encoding="utf-8")) or {}) if seed_f.exists() else {}
    app["algo_seed"] = {"source": seed.get("source", ""), "updated": seed.get("updated", ""), "repo": seed.get("repo", ""), "tested": seed.get("tested", ""),
                        "items": [{"id": i["id"], "d": i["d"], "s": "SWEA", "n": i["n"], "l": "", "r": i.get("r", "ok"), "m": 0,
                                   "t": i.get("t") or [], "note": i.get("note", ""), "file": i.get("file", ""), "fid": i.get("fid", ""), "gh": i.get("gh", ""), "idea": i.get("idea", ""), "cx": i.get("cx", ""), "src": "drive"}
                                  for i in seed.get("items") or []]}
    prep = _prep()
    app["prep"] = {k: prep.get(k) for k in ("updated", "goals", "weekly", "experiences", "essays")}
    from career_content import prepare_essays
    app["prep"]["essays"] = prepare_essays(prep, data)
    app["prep"]["opic_types"] = (prep.get("opic") or {}).get("types") or []
    app["prep"]["opic_tip"] = (prep.get("opic") or {}).get("tip", "")
    built_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    release = {"version": uuid4().hex, "built_at": built_at}
    app["metadata"] = dict(release, sources=[
        {"name": "면접 노트·질문은행", "path": "content/private/ · content/private_sealed/",
         "updated": "", "description": "개인 답변과 질문은행을 이번 빌드에서 합쳤습니다. 원본별 확인일은 별도로 제공되지 않습니다."},
        {"name": "포트폴리오 프로젝트", "path": "data/portfolio.yaml · data/case_notes.yaml",
         "updated": "", "description": "프로젝트 사실·성과·설계 판단을 답변과 발표 자료에 반영합니다."},
        {"name": "준비 계획·OPIc", "path": "data/prep.yaml", "updated": prep.get("updated", ""),
         "description": "목표 일정, 주간 계획, 자소서·OPIc 문항의 자료 확인일입니다."},
        {"name": "공채 정보", "path": "data/recruit.yaml", "updated": app["recruit"].get("checked", ""),
         "description": "지원 조건과 면접 정보는 해당 확인일의 스냅샷입니다. 지원 전 공식 공고를 확인하세요."},
        {"name": "알고리즘 기록", "path": "data/algo_solved.yaml", "updated": seed.get("updated", ""),
         "description": "드라이브 풀이 기록을 빌드 시 가져온 자료입니다."},
    ])
    # Public metadata contains no questions, answers or private file contents.
    (OUT / "version.json").write_text(json.dumps(release), encoding="utf-8")
    app["study"] = getattr(study, "APP", None)
    html = env.get_template("interview.html.j2").render(app=app, **data)
    (OUT / "index.html").write_text(locker.page("준비 공간", html, "../index.html", pwa=True), encoding="utf-8")
    study.pwa(OUT, [])
    OLD.mkdir(parents=True, exist_ok=True)
    (OLD / "index.html").write_text(MOVED, encoding="utf-8")
    old_ver = OLD / "version.json"
    if old_ver.exists():
        old_ver.unlink()
    return {"questions": len(app["questions"]), "decks": len(app["decks"])} if locker.password else None
