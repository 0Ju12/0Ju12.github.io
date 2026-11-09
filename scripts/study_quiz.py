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
        m = re.match(r"^([a-f])\)", a)
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
            out.append({"type": "M", "prompt": stem, "options": opts, "answer": str(k), "explanation": _text(expl)})
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
        for q in qs:
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
