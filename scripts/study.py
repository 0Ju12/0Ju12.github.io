"""content/study/notes/*.html (노션 강의 요약) + quiz/lessons.json → docs/study/ 학습 앱 (암호로 잠김)

- 원본: 로컬의 content/study/notes/ (커밋 금지) 또는 잠긴 content/study_sealed/notes.sealed.json (배포 빌드에서 PRIVATE_KEY 로 풂)
- 출력: 모든 노트·목록 페이지를 암호(STUDY_PASSWORD, 없으면 PRIVATE_PASSWORD)로 AES-GCM 암호화한 잠금 페이지.
  암호가 없는 빌드(로컬 등)에서는 내용 없는 '잠김' 페이지만 만들어 평문이 docs/ 에 남지 않음.

- 각 노트에 학습 공간 내비게이션(목록·이전·다음)을 끼워 docs/study/notes/ 로 복사
- 제목·날짜·목차·요약을 뽑아 docs/study/index.html 학습 앱 생성 (문제·키워드 카드·약점 리포트·모의고사)
- 본문 검색 색인은 같은 키로 암호화해 docs/study/search.enc.json 에 (암호 없는 빌드엔 만들지 않음)
- manifest.webmanifest · sw.js 로 홈 화면 설치·오프라인 사용
"""
import base64, html, io, json, os, re, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content" / "study" / "notes"
SEALED = ROOT / "content" / "study_sealed" / "notes.sealed.json"
ITER = 600_000
OUT = ROOT / "docs" / "study"

TRACKS = [   # 파일 이름으로 분류 — 새 강의 노트가 들어와도 규칙에 맞으면 자동으로 해당 트랙에
    ("web", "WEB", "HTML·CSS·Bootstrap·반응형", lambda n: n[:3] in ("01_", "02_", "03_")),
    ("js", "JavaScript", "기본 문법·DOM·이벤트", lambda n: "_JS_" in n or "_JavaScript_" in n),
    ("algo", "SW 알고리즘", "자료구조·탐색·DP·그래프", lambda n: n.startswith("SW")),
    ("django", "Django", "MTV·ORM·Form·인증·DRF", lambda n: "_Django_" in n),
    ("db", "DB · SQL", "SQL·관계(1:N, M:N)·N+1", lambda n: "_DB_" in n),
    ("ai", "AI", "데이터 분석·ML·NLP·LLM·비전·에이전트", lambda n: n.startswith("AI")),
    ("etc", "기타", "분류 규칙에 없는 노트", lambda n: True),
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


# 잠금 페이지가 document.write 로 그린 뒤에는 브라우저가 #절 로 스크롤하지 않음 → 직접 이동하고 잠깐 강조
HASH_JS = """<style>h2[id]{scroll-margin-top:64px}.st-hit{outline:3px solid #f59e0b;outline-offset:6px;border-radius:4px;transition:outline-color 1.6s}</style>
<script>(function(){function go(){var h=decodeURIComponent(location.hash.slice(1));if(!h)return;var el=document.getElementById(h);if(!el)return;
el.scrollIntoView({block:'start'});el.classList.add('st-hit');setTimeout(function(){el.style.outlineColor='transparent'},1800)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(go,30)});else setTimeout(go,30);
window.addEventListener('hashchange',go)})();</script>"""


# 노트마다 똑같이 박혀 있던 KaTeX 수식 폰트(노트 1편당 약 340KB, 52편 합계 약 18MB)를 공용 파일 하나로 빼서
# 브라우저가 한 번만 받고 캐시하게 함. 폰트는 공개 오픈소스(KaTeX, MIT)라 암호 없이 docs/study/fonts/ 에 둠
FONT_RE = re.compile(r"url\((['\"]?)data:font/(woff2|woff|ttf);base64,([A-Za-z0-9+/=]+)\1\)")


def slim(raw, fontdir):
    import hashlib

    def rep(m):
        b = base64.b64decode(m.group(3))
        name = f"{hashlib.sha1(b).hexdigest()[:12]}.{m.group(2)}"
        f = fontdir / name
        if not f.exists():
            fontdir.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b)
        return f"url('../fonts/{name}')"
    return FONT_RE.sub(rep, raw)


NUM_PREFIX = re.compile(r"(<(?:title|h1)[^>]*>)\s*(?:(?:AI|SW)\s*)?\d+\.\s*")


def inject(note, prev, nxt):
    links = ['<a href="../index.html">← 학습 공간</a>', f'<span class="st-t">{html.escape(note["title"])}</span>']
    if prev:
        links.append(f'<a href="{prev["slug"]}.html">‹ 이전</a>')
    if nxt:
        links.append(f'<a href="{nxt["slug"]}.html">다음 ›</a>')
    if note.get("nq"):
        links.append(f'<a href="../index.html#/quiz/{note["slug"]}">문제 {note["nq"]}개 풀기</a>')
    links.append('<a href="../../index.html">포트폴리오</a>')
    bar = NAV_CSS + HASH_JS + '<nav class="st-nav">' + "".join(links) + "</nav>"
    raw = NUM_PREFIX.sub(r"\1", note["raw"])                         # <title>·<h1> 앞 번호 제거
    return re.sub(r"(<body[^>]*>)", r"\1" + bar.replace("\\", "\\\\"), raw, count=1)


def _source():
    """평문 원본 폴더 — 로컬 원본이 있으면 그대로, 없으면 잠긴 묶음들을 PRIVATE_KEY 로 풀어 임시 폴더에

    notes.sealed.json(전체) 다음 notes-*.sealed.json(추가분)을 이름 순서대로 풀어 덮어씀 → 정기 작업이
    개인키 없이 새 노트만 추가 묶음으로 잠가 올려도 배포 빌드에서 합쳐짐
    """
    if SRC.exists() and any(SRC.glob("*.html")):
        return SRC
    pem = os.environ.get("PRIVATE_KEY")
    if not (pem and SEALED.exists()):
        return None
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    priv = serialization.load_pem_private_key(pem.encode(), password=None)
    tmp = Path(tempfile.mkdtemp(prefix="study-"))
    for f in [SEALED] + sorted(SEALED.parent.glob("notes-*.sealed.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        key = priv.decrypt(base64.b64decode(r["key"]), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        raw = AESGCM(key).decrypt(base64.b64decode(r["nonce"]), base64.b64decode(r["ct"]), None)
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

    def page(self, title, inner_html, home, pwa=True):
        box = None
        if self.password:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            iv = os.urandom(12)
            e = lambda b: base64.b64encode(b).decode()
            box = {"salt": e(self.salt), "iv": e(iv), "iter": ITER, "ct": e(AESGCM(self.key).encrypt(iv, inner_html.encode(), None))}
        root = "../" if home.startswith("../../") else ""
        return self.env.get_template("study_lock.html.j2").render(title=title, box=box, home=home, root=root, pwa=pwa)

    def blob(self, obj):
        """검색 색인 같은 큰 데이터 → gzip 후 같은 키로 암호화 (브라우저가 sessionStorage 의 키로 풂)"""
        import gzip
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        iv = os.urandom(12)
        raw = gzip.compress(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode(), 9)
        e = lambda b: base64.b64encode(b).decode()
        return {"iv": e(iv), "gz": 1, "ct": e(AESGCM(self.key).encrypt(iv, raw, None))}


def pwa(out, slugs):
    """홈 화면 설치·오프라인용 manifest 와 service worker (페이지는 이미 암호화돼 있어 캐시해도 평문이 남지 않음)"""
    import hashlib
    man = {"name": "학습 노트 · SSAFY 16기", "short_name": "학습 노트", "start_url": "./index.html", "scope": "./",
           "display": "standalone", "background_color": "#0e1116", "theme_color": "#1f3a5f", "lang": "ko",
           "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}
    (out / "manifest.webmanifest").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    ver = hashlib.sha1((out / "index.html").read_bytes() if (out / "index.html").exists() else b"").hexdigest()[:10]
    (out / "sw.js").write_text(SW_JS.replace("__VER__", ver), encoding="utf-8")


# 페이지: 네트워크 먼저(새 노트 반영) → 실패하면 캐시. 그 밖의 파일: 캐시 먼저 + 뒤에서 갱신
SW_JS = """const C='study-__VER__';
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['./','./index.html','./manifest.webmanifest','./icon-192.png'])).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('study-')&&k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;
 const put=res=>{if(res&&res.ok){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res};
 if(r.mode==='navigate'||u.pathname.endsWith('.json')){e.respondWith(fetch(r).then(put).catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match('./index.html'))));return}
 e.respondWith(caches.match(r).then(m=>{const f=fetch(r).then(put).catch(()=>m);return m||f}))});
"""


LOCKER = None   # 같은 빌드의 면접 준비 앱(interview.py)도 이 키를 써서, 한 번 연 탭에서는 둘 다 다시 묻지 않음


def build(env, data):
    global LOCKER
    LOCKER = Locker(env, os.environ.get("STUDY_PASSWORD") or os.environ.get("PRIVATE_PASSWORD"))
    src = _source()
    if not src:
        return []
    locker = LOCKER
    notes = [parse(p) for p in sorted(src.glob("*.html"))]
    for n in notes:
        n["raw"] = slim(n["raw"], OUT / "fonts")
    import study_quiz
    quiz_file = src / "quiz" / "lessons.json"
    if not quiz_file.exists():
        quiz_file = ROOT / "content" / "study" / "quiz" / "lessons.json"
    units = study_quiz.build(notes, quiz_file)
    index = study_quiz.enrich(notes, units)
    for n in notes:
        n["nq"] = len(units[n["slug"]]["questions"])
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
    app = {"tracks": [{"id": t[0], "name": t[1], "desc": t[2]} for t in TRACKS],
           "notes": [{k: n[k] for k in ("slug", "title", "num", "date", "sections", "summary", "track", "nq")} for n in notes],
           "units": units, "salt": base64.b64encode(locker.salt).decode() if locker.password else ""}
    search = OUT / "search.enc.json"
    if locker.password:
        search.write_text(json.dumps(locker.blob(index)), encoding="utf-8")
    elif search.exists():
        search.unlink()                                           # 암호 없는 빌드엔 색인을 남기지 않음
    hub = env.get_template("study.html.j2").render(tracks=tracks, notes=notes, timeline=dated, app=app, **data)
    (OUT / "index.html").write_text(locker.page("강의 노트", hub, "../index.html"), encoding="utf-8")
    pwa(OUT, [n["slug"] for n in notes])
    return notes
