"""면접 준비 앱 → docs/interview/index.html (강의 노트와 같은 암호·같은 키로 잠김)

- 질문 은행: 면접 노트(content/private/interview.json, 배포 빌드에서는 잠긴 묶음을 PRIVATE_KEY 로 풂)
  + 포트폴리오 프로젝트에서 만든 답변 뼈대(digest·case_notes) + AI 트렌드 노트의 면접 질문
- 발표 자료: 직무별 1분 자기소개 + 프로젝트별 발표 슬라이드 (발표자 메모 포함)
  PDF(브라우저 인쇄)·PPTX(브라우저에서 PptxGenJS 로 생성)는 잠금을 푼 화면에서만 만들어져 평문 파일이 docs/ 에 남지 않음
"""
import json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "interview"
PRIVATE_JSON = ROOT / "content" / "private" / "interview.json"
BANK_JSON = ROOT / "content" / "private" / "interview_bank.json"
CATS = ["인성", "프로젝트", "전문지식", "기타"]
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
    import hashlib
    for b in _private("interview_bank.json", BANK_JSON):
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
    return qs


def decks(data, variants):
    prof, cases, out = data["profile"], data.get("case_notes") or {}, []
    projs = _projects(data)
    byid = {p["id"]: (g, p) for g, p in projs}
    for role, v in variants.items():
        order = [(g, p) for gid in v.get("order", []) for g, p in projs if g.get("id") == gid]
        top = order[:3]
        slides = [{"t": "title", "kicker": "1분 자기소개 · " + v.get("label", role), "h": prof["name"], "sub": v.get("headline") or prof["headline"],
                   "note": f"안녕하세요, {v.get('label', '')} 직무에 지원한 {prof['name']}입니다. {v.get('headline') or prof['headline']}."},
                  {"t": "stats", "h": "숫자로 보는 저", "items": [[x["value"], x["label"]] for x in v.get("highlights", [])[:4]],
                   "note": "제 경험을 숫자 네 개로 먼저 말씀드리겠습니다. " + " ".join(f"{x['value']}, {x['label']}." for x in v.get("highlights", [])[:4])}]
        for g, p in top:
            d = p["digest"]
            slides.append({"t": "bullets", "kicker": p.get("short") or "", "h": p.get("tagline") or p["title"],
                           "items": [d["problem"], d["role"]] + d.get("result", [])[:2], "img": _photo(p["id"]),
                           "note": f"{p.get('short')}에서는 {d['problem']} 저는 {d['role']}. 결과적으로 {d.get('result', [''])[0]}."})
        slides.append({"t": "end", "h": "감사합니다", "sub": "포트폴리오 0ju12.github.io · GitHub github.com/0Ju12",
                       "note": "자세한 내용은 포트폴리오와 GitHub에 정리해 두었습니다. 감사합니다."})
        out.append({"id": "intro-" + role, "title": f"1분 자기소개 · {v.get('label', role)}", "kind": "intro", "role": role, "min": 1, "slides": slides})
    for g, p in projs:
        d, cn = p["digest"], (cases.get(p["id"]) or {}).get("ko") or {}
        per = p.get("period") or {}
        when = f"{per.get('start', '')}–{per.get('end', '')}" if isinstance(per, dict) else str(per)
        img = _photo(p["id"])
        s = [{"t": "title", "kicker": p.get("type") or "프로젝트", "h": p["title"], "sub": f"{p.get('org', '')} · {when} · {p.get('role', '')}",
              "note": f"{p.get('short')} 프로젝트를 소개하겠습니다. {p.get('tagline', '')}."},
             {"t": "text", "kicker": "문제", "h": d["problem"], "img": img,
              "note": f"이 프로젝트에서 풀려던 문제는 이것입니다. {d['problem']}"},
             {"t": "bullets", "kicker": "내 역할과 한 일", "h": d["role"], "items": d.get("did", [])[:5],
              "note": f"저는 {d['role']}. 구체적으로 " + " ".join(d.get("did", [])[:3]) + "."}]
        if cn.get("tradeoffs"):
            s.append({"t": "bullets", "kicker": "설계 판단", "h": "무엇을 고민했고 어떻게 정했나", "items": [t.split("→")[0].strip() + (" → " + t.split("→", 1)[1].strip()[:110] if "→" in t else "") for t in cn["tradeoffs"][:3]],
                      "note": "가장 고민한 판단을 말씀드리면, " + cn["tradeoffs"][0]})
        s.append({"t": "stats" if len(d.get("result", [])) <= 4 else "bullets", "kicker": "결과", "h": p.get("key") or "결과",
                  "items": [[r, ""] for r in d.get("result", [])[:4]] if len(d.get("result", [])) <= 4 else d.get("result", []),
                  "note": "결과는 다음과 같습니다. " + " ".join(d.get("result", []))})
        if cn.get("next"):
            s.append({"t": "bullets", "kicker": "한계와 다음 단계", "h": "확신하는 것과 남은 것", "items": cn["next"][:3],
                      "note": "한계도 분명히 말씀드리겠습니다. " + cn["next"][0]})
        s.append({"t": "end", "h": "질문 받겠습니다", "sub": " · ".join(l["label"] for l in (p.get("links") or [])[:2]) or "0ju12.github.io",
                  "note": "이상입니다. 질문 주시면 답변드리겠습니다."})
        out.append({"id": p["id"], "title": p.get("short") or p["title"], "kind": "project", "min": 3, "slides": s,
                    "tagline": p.get("tagline", ""), "group": g.get("id")})
    return out


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
    html = env.get_template("interview.html.j2").render(app=app, **data)
    (OUT / "index.html").write_text(locker.page("면접 준비", html, "../index.html", pwa=False), encoding="utf-8")
    return {"questions": len(app["questions"]), "decks": len(app["decks"])} if locker.password else None
