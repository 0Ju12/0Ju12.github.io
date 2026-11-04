"""content/study/notes/*.html (노션 강의 요약) → docs/study/ 학습 공간 (암호로 잠김)

- 원본: 로컬의 content/study/notes/ (커밋 금지) 또는 잠긴 content/study_sealed/notes.sealed.json (배포 빌드에서 PRIVATE_KEY 로 풂)
- 출력: 모든 노트·목록 페이지를 암호(STUDY_PASSWORD, 없으면 PRIVATE_PASSWORD)로 AES-GCM 암호화한 잠금 페이지.
  암호가 없는 빌드(로컬 등)에서는 내용 없는 '잠김' 페이지만 만들어 평문이 docs/ 에 남지 않음.

- 각 노트에 학습 공간 내비게이션(목록·이전·다음)을 끼워 docs/study/notes/ 로 복사
- 제목·날짜·목차·요약을 뽑아 docs/study/index.html 허브 페이지 생성 (검색·트랙 필터)
"""
import base64, html, io, json, os, re, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "study" / "notes"
SEALED = ROOT / "content" / "study_sealed" / "notes.sealed.json"
ITER = 600_000
OUT = ROOT / "docs" / "study"

TRACKS = [
    ("web", "WEB", "HTML·CSS·Bootstrap·반응형", lambda n: n[:2] in ("01", "02", "03")),
    ("algo", "SW 알고리즘", "자료구조·탐색·DP·그래프", lambda n: n.startswith("SW")),
    ("django", "Django", "MTV·ORM·Form·인증", lambda n: n[:2].isdigit() and 4 <= int(n[:2]) <= 13),
    ("db", "DB · SQL", "SQL·관계(1:N, M:N)·N+1", lambda n: n[:2].isdigit() and 14 <= int(n[:2]) <= 19),
    ("ai", "AI", "데이터 분석·ML·NLP·LLM·비전", lambda n: n.startswith("AI")),
]
SKIP_SECTIONS = ("핵심 키워드", "확인 문제", "참고 내용", "실습 문제")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse(path):
    s = path.read_text(encoding="utf-8")
    title = clean(re.search(r"<title>(.*?)</title>", s, re.S).group(1))
    m = re.search(r"\((\d{2})(\d{2})\)\s*$", title)
    date = f"2026.{m.group(1)}.{m.group(2)}" if m else ""
    title_clean = re.sub(r"\s*\(\d{4}\)\s*$", "", title)
    num, _, name = title_clean.partition(".") if re.match(r"^(AI |SW )?\d+\.", title_clean) else ("", "", title_clean)
    sections = [re.sub(r"^\d+\.\s*", "", clean(x)) for x in re.findall(r"<h2[^>]*>(.*?)</h2>", s, re.S)]
    sections = [x for x in sections if x and not x.startswith(SKIP_SECTIONS)]
    body = re.sub(r"<style.*?</style>", "", s, flags=re.S)
    i = body.find("한눈에")
    summary = ""
    if i >= 0:
        summary = clean(body[i:i + 3000])
        summary = re.sub(r"^한눈에 보기\s*", "", summary)
        summary = summary[:150].rsplit(" ", 1)[0] + "…" if len(summary) > 150 else summary
    track = next(t for t in TRACKS if t[3](path.stem))
    name = name.strip() or title_clean
    slug = re.sub(r"^(ai|sw)?\d+_", "", path.stem.lower())          # 앞 번호 없는 파일 이름
    return {"file": path.name, "slug": slug, "title": name, "num": num.strip(),
            "name": name, "date": date, "sections": sections[:8],
            "summary": summary, "track": track[0], "raw": s}


NAV_CSS = """<style>.st-nav{position:sticky;top:0;z-index:999;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;
padding:10px 18px;background:rgba(13,13,15,.92);backdrop-filter:blur(8px);font:600 13px/1.4 "Noto Sans KR",system-ui,sans-serif}
.st-nav a{color:#5eead4;text-decoration:none}.st-nav a:hover{text-decoration:underline}.st-nav .st-t{color:#a1a1aa;margin-right:auto;font-weight:500}
@media print{.st-nav{display:none}}@media (max-width:600px){.st-nav .st-t{display:none}.st-nav a:first-child{margin-right:auto}}</style>"""


NUM_PREFIX = re.compile(r"(<(?:title|h1)[^>]*>)\s*(?:(?:AI|SW)\s*)?\d+\.\s*")


def inject(note, prev, nxt):
    links = ['<a href="../index.html">← 학습 공간</a>', f'<span class="st-t">{html.escape(note["title"])}</span>']
    if prev:
        links.append(f'<a href="{prev["slug"]}.html">‹ 이전</a>')
    if nxt:
        links.append(f'<a href="{nxt["slug"]}.html">다음 ›</a>')
    links.append('<a href="../../index.html">포트폴리오</a>')
    bar = NAV_CSS + '<nav class="st-nav">' + "".join(links) + "</nav>"
    raw = NUM_PREFIX.sub(r"\1", note["raw"])                         # <title>·<h1> 앞 번호 제거
    return re.sub(r"(<body[^>]*>)", r"\1" + bar.replace("\\", "\\\\"), raw, count=1)


def _source():
    """평문 원본 폴더 — 로컬 원본이 있으면 그대로, 없으면 잠긴 묶음을 PRIVATE_KEY 로 풀어 임시 폴더에"""
    if SRC.exists() and any(SRC.glob("*.html")):
        return SRC
    pem = os.environ.get("PRIVATE_KEY")
    if not (pem and SEALED.exists()):
        return None
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    r = json.loads(SEALED.read_text(encoding="utf-8"))
    priv = serialization.load_pem_private_key(pem.encode(), password=None)
    key = priv.decrypt(base64.b64decode(r["key"]), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    raw = AESGCM(key).decrypt(base64.b64decode(r["nonce"]), base64.b64decode(r["ct"]), None)
    tmp = Path(tempfile.mkdtemp(prefix="study-"))
    zipfile.ZipFile(io.BytesIO(raw)).extractall(tmp)
    return tmp


class Locker:
    """같은 빌드의 모든 페이지를 한 키로 암호화(페이지마다 IV만 다름) → 한 번 연 탭에서는 다시 묻지 않음"""
    def __init__(self, env, password):
        self.env, self.password = env, password
        self.salt = os.urandom(16)
        if password:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            self.key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.salt, iterations=ITER).derive(password.encode())

    def page(self, title, inner_html, home):
        box = None
        if self.password:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            iv = os.urandom(12)
            e = lambda b: base64.b64encode(b).decode()
            box = {"salt": e(self.salt), "iv": e(iv), "iter": ITER, "ct": e(AESGCM(self.key).encrypt(iv, inner_html.encode(), None))}
        return self.env.get_template("study_lock.html.j2").render(title=title, box=box, home=home)


def build(env, data):
    src = _source()
    if not src:
        return []
    locker = Locker(env, os.environ.get("STUDY_PASSWORD") or os.environ.get("PRIVATE_PASSWORD"))
    notes = [parse(p) for p in sorted(src.glob("*.html"))]
    order = {t[0]: i for i, t in enumerate(TRACKS)}
    notes.sort(key=lambda n: (order[n["track"]], n["date"] or "9", n["file"]))   # 수강 날짜 순
    (OUT / "notes").mkdir(parents=True, exist_ok=True)
    for i, n in enumerate(notes):
        same = [x for x in notes if x["track"] == n["track"]]
        j = same.index(n)
        prev = same[j - 1] if j > 0 else None
        nxt = same[j + 1] if j + 1 < len(same) else None
        (OUT / "notes" / f"{n['slug']}.html").write_text(locker.page(n["title"], inject(n, prev, nxt), "../../index.html"), encoding="utf-8")
    tracks = [{"id": t[0], "name": t[1], "desc": t[2], "notes": [n for n in notes if n["track"] == t[0]]} for t in TRACKS]
    dated = sorted([n for n in notes if n["date"]], key=lambda n: (n["date"], order[n["track"]], n["file"]))
    hub = env.get_template("study.html.j2").render(tracks=tracks, notes=notes, timeline=dated, **data)
    (OUT / "index.html").write_text(locker.page("강의 노트", hub, "../index.html"), encoding="utf-8")
    return notes
