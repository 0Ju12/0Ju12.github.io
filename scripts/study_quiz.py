"""강의 노트 → 학습 앱 문제·개념 데이터

- content/study/quiz/lessons.json (따로 정리한 Django 개념 카드·문제, 커밋 금지 · 노트와 함께 잠금)
- lessons.json 에 없는 노트는 노트 안의 '확인 문제' 목록 + '정답 및 해설' 표에서 문제를 뽑음
- 결과는 노트(slug)별 단위로 묶어 study.py 가 잠긴 허브 페이지에 넣음 (평문으로 docs/ 에 남지 않음)

문제 형식: M 객관식(answer = 보기 번호) · S 단답(정확히 비교) · W 서술(모범답안과 비교 후 스스로 채점)
"""
import html, json, re
from pathlib import Path

CIRCLED = "①②③④⑤⑥"
GENERIC_EXPL = "노션 원본 강의노트의 정답 및 해설입니다. 원문과 비교해 스스로 점검하세요."


def _text(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("​", "").replace("︎", "")
    return re.sub(r"\s+", " ", s).strip()


def _options(t):
    """'질문 ① a ② b' 또는 '질문 a) x b) y' → (질문, [보기])"""
    if re.search(r"\s①\s", " " + t):
        parts = re.split(r"\s*[①②③④⑤⑥]\s*", t)
        return parts[0].strip(), [p.strip() for p in parts[1:] if p.strip()]
    m = re.search(r"\sa\)\s", t)
    if m and re.search(r"\sb\)\s", t):
        parts = re.split(r"\s[a-f]\)\s", " " + t[m.start():] + " ")
        return t[:m.start()].strip(), [p.strip() for p in parts[1:] if p.strip()]
    return t, []


def _answer_index(a, n):
    a = a.strip()
    if a and a[0] in CIRCLED:
        i = CIRCLED.index(a[0])
    else:
        m = re.match(r"^\(?([a-f])(?:\)|\s*[–—\-.:]|\s*\(|\s*$)", a)    # 'c)', 'c – 해설', 'c', '(c)'
        if not m:
            return None
        i = ord(m.group(1)) - 97
    return i if i < n else None


def _top_level_items(ol_body):
    items, cur, depth = [], "", 0
    for tok in re.split(r"(<li[^>]*>|</li>|<[ou]l[^>]*>|</[ou]l>)", ol_body):
        if not tok:
            continue
        if tok.startswith("<li"):
            if depth == 0:
                cur = ""
            else:
                cur += tok
            depth += 1
        elif tok == "</li>":
            depth -= 1
            if depth == 0:
                items.append(cur)
            else:
                cur += tok
        else:
            cur += tok
    return items


def _split_answer(a):
    """'c – 해설' → 해설 부분 (보기 번호만 있으면 빈 문자열)"""
    m = re.match(r"^\(?[a-f①-⑥]\)?\s*(?:\)\s*)?(?:[–—\-:]\s*)?(.*)$", a.strip(), re.S)
    return m.group(1).strip() if m else ""


def as_choice(q):
    """서술형으로 들어왔지만 질문에 a) b) 보기가 있고 정답이 보기 번호면 객관식으로 바꿈"""
    if q.get("type", "W") != "W" or q.get("options"):
        return q
    stem, opts = _options(q.get("prompt", ""))
    k = _answer_index(str(q.get("answer", "")), len(opts)) if len(opts) >= 2 else None
    if k is None:
        return q
    extra = _split_answer(str(q["answer"]))
    expl = q.get("explanation", "")
    if extra and extra not in expl:
        expl = (extra + (" / " + expl if expl and expl != GENERIC_EXPL else "")).strip()
    return {**q, "type": "M", "prompt": stem, "options": opts, "answer": str(k), "explanation": expl}


def from_note(raw):
    """노트 HTML 의 마지막 '확인 문제' 절 → 문제 목록 (질문 수와 정답 행 수가 다르면 빈 목록)"""
    heads = [m for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", raw, re.S) if "확인 문제" in _text(m.group(1))]
    if not heads:
        return []
    seg = raw[heads[-1].end():]
    t = seg.find("<table")
    if t < 0:
        return []
    qpart, apart = seg[:t], seg[t:seg.find("</table>", t)]
    items = [li for ol in re.finditer(r"<ol[^>]*>(.*?)</ol>", qpart, re.S) for li in _top_level_items(ol.group(1))]
    rows = re.findall(r"<tr[^>]*>\s*<td[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>", apart, re.S)
    if not items or len(items) != len(rows):
        return []
    out = []
    for li, (ans, expl) in zip(items, rows):
        q = _text(li)
        stem, opts = _options(q)
        a = _text(ans)
        k = _answer_index(a, len(opts)) if len(opts) >= 2 else None
        if k is not None:
            extra, ex = _split_answer(a), _text(expl)
            if extra and extra not in ex:
                ex = extra + (" / " + ex if ex else "")
            out.append({"type": "M", "prompt": stem, "options": opts, "answer": str(k), "explanation": ex})
        else:
            out.append({"type": "W", "prompt": q, "options": [], "answer": a, "explanation": _text(expl)})
    return out


def _qid(slug, prompt):
    h = 5381
    for ch in prompt:
        h = (h * 33 + ord(ch)) & 0xFFFFFFFF
    return f"{slug}:{h:08x}"


def build(notes, lessons_path):
    """notes: study.parse() 결과 목록 → {slug: {concepts, code, questions}}"""
    lessons = []
    if lessons_path and Path(lessons_path).exists():
        lessons = json.loads(Path(lessons_path).read_text(encoding="utf-8"))
    by_file = {u.get("source"): u for u in lessons}
    units = {}
    for n in notes:
        u = by_file.get(n["file"])
        qs = (u or {}).get("questions") or from_note(n["raw"])
        clean = []
        seen = set()
        for q in map(as_choice, qs):
            if not q.get("prompt"):
                continue
            qid = _qid(n["slug"], q["prompt"])
            if qid in seen:
                continue
            seen.add(qid)
            item = {"id": qid, "t": q.get("type", "W"), "q": q["prompt"], "a": q.get("answer", ""),
                    "e": "" if q.get("explanation") == GENERIC_EXPL else q.get("explanation", "")}
            if q.get("options"):
                item["o"] = q["options"]
            clean.append(item)
        concepts = [{"name": c[0], "core": c[1], "detail": c[2] if len(c) > 2 else "", "code": c[3] if len(c) > 3 else "",
                     "note": c[4] if len(c) > 4 else ""} for c in (u or {}).get("concepts", [])]
        units[n["slug"]] = {"questions": clean, "concepts": concepts, "code": (u or {}).get("code", "")}
    return units


# ---------------------------------------------------------------- 핵심 키워드 · 절(section) · 검색 색인
SKIP_SEC = ("확인 문제", "핵심 키워드")


def sections(raw):
    """노트의 h2 절 → [{id, title, text}] (확인 문제·키워드 절 제외). 본문 검색과 '이 절 다시 읽기' 링크에 씀"""
    hs = list(re.finditer(r'<h2([^>]*)>(.*?)</h2>', raw, re.S))
    out = []
    for i, m in enumerate(hs):
        title = re.sub(r"^\d+\.\s*", "", _text(m.group(2)))
        idm = re.search(r'id="([^"]+)"', m.group(1))
        if not idm or title.startswith(SKIP_SEC):
            continue
        body = raw[m.end():hs[i + 1].start() if i + 1 < len(hs) else len(raw)]
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S)
        out.append({"id": idm.group(1), "title": title, "text": _text(body)})
    return out


def keywords(raw):
    """'핵심 키워드 정리' 표 → ([{term, desc, ex}], 한 줄 정리)"""
    hs = list(re.finditer(r'<h2[^>]*>(.*?)</h2>', raw, re.S))
    k = [i for i, m in enumerate(hs) if "핵심 키워드" in _text(m.group(1))]
    if not k:
        return [], ""
    i = k[-1]
    seg = raw[hs[i].end():hs[i + 1].start() if i + 1 < len(hs) else len(raw)]
    t0, t1 = seg.find("<table"), seg.find("</table>")
    if t0 < 0:
        return [], ""
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", seg[t0:t1], re.S)
    head = [_text(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", seg[t0:t1], re.S)]
    lead = bool(head) and head[0] in ("차시", "주제", "구분", "분류", "번호", "단원")   # 앞 열이 묶음 이름이면 한 칸 밀어 읽음
    out, seen = [], set()
    for r in rows:
        cells = [_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        group = ""
        if lead and len(cells) >= 3:
            group, cells = cells[0], cells[1:]
        if len(cells) >= 2 and cells[0] and cells[1] and cells[0] not in seen:
            seen.add(cells[0])
            ex = cells[2] if len(cells) > 2 else ""
            if group and not group.isdigit():
                ex = (group + (" · " + ex if ex else ""))
            out.append({"term": cells[0], "desc": cells[1], "ex": ex})
    tail = _text(seg[t1:])
    one = ""
    m = re.search(r"한 줄 정리\s*:?\s*(.+)", tail)
    if m:
        one = m.group(1)[:300]
    return out, one


def _tokens(s):
    return {w.lower() for w in re.findall(r"[A-Za-z_][A-Za-z0-9_.]{1,}|[가-힣]{2,}", s)}


def best_section(text, secs):
    """질문·정답 낱말과 가장 많이 겹치는 절 id (겹침이 2개 미만이면 빈 문자열)"""
    q = _tokens(text)
    best, score = "", 1
    for s in secs:
        sc = len(q & _tokens(s["title"] + " " + s["text"][:4000]))
        if sc > score:
            best, score = s["id"], sc
    return best


def keyword_questions(slug, kws, secs):
    """키워드 표로 객관식 만들기: 설명을 보여 주고 같은 노트의 다른 개념 3개와 섞어 고르게 함(설명 속 정답 낱말은 가림)"""
    import random
    if len(kws) < 4:
        return []
    rnd = random.Random(slug)
    out = []
    terms = [k["term"] for k in kws]
    for k in kws:
        desc = k["desc"]
        for part in re.split(r"\s*[/·,()]\s*", k["term"]):
            if len(part) >= 2:
                desc = desc.replace(part, "○○")
        others = [t for t in terms if t != k["term"]]
        opts = rnd.sample(others, 3) + [k["term"]]
        rnd.shuffle(opts)
        sec = next((s["id"] for s in secs if k["term"].split(" ")[0] in s["text"]), "") or best_section(k["term"] + " " + k["desc"], secs)
        out.append({"id": _qid(slug, "kw:" + k["term"]), "t": "M", "kw": 1, "q": "다음 설명에 해당하는 개념은?\n" + desc,
                    "o": opts, "a": str(opts.index(k["term"])), "e": k["term"] + " — " + k["desc"] + (f" (예: {k['ex']})" if k["ex"] else ""), "sec": sec})
    return out


def enrich(notes, units):
    """build() 결과에 키워드 카드·키워드 문제·절 정보를 더하고, 본문 검색 색인을 따로 돌려줌"""
    index = {}
    for n in notes:
        u = units[n["slug"]]
        secs = sections(n["raw"])
        kws, one = keywords(n["raw"])
        for q in u["questions"]:
            q["sec"] = best_section(q["q"] + " " + str(q.get("a", "")) + " " + " ".join(q.get("o", [])), secs)
        u["questions"] += keyword_questions(n["slug"], kws, secs)
        u["keywords"] = kws
        u["one"] = one
        u["secs"] = [[s["id"], s["title"]] for s in secs]
        index[n["slug"]] = [[s["id"], s["title"], s["text"]] for s in secs]
    return index
