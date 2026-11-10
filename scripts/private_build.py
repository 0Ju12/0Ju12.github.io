"""content/private_sealed/*.json → docs/private/index.html (암호를 입력해야 열리는 페이지)

필요한 환경 변수 (GitHub Actions 비밀값):
  PRIVATE_KEY       잠긴 파일을 푸는 개인키 (PEM)
  PRIVATE_PASSWORD  방문자가 입력할 암호
둘 중 하나라도 없으면 "아직 설정되지 않음" 페이지만 만듭니다.
페이지 내용은 PBKDF2-SHA256(60만 회) + AES-GCM 으로 암호화되어, 암호 없이는 읽을 수 없습니다.
"""
import base64, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEALED = ROOT / "content" / "private_sealed"
OUT = ROOT / "docs" / "private"
ITER = 600_000


def unseal_all(pem):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    priv = serialization.load_pem_private_key(pem.encode(), password=None)
    oaep = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    docs = []
    for f in sorted(SEALED.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        key = priv.decrypt(base64.b64decode(r["key"]), oaep)
        docs.append((r.get("name", f.stem), AESGCM(key).decrypt(base64.b64decode(r["nonce"]), base64.b64decode(r["ct"]), None).decode("utf-8")))
    return docs


def render(docs):
    import markdown, yaml
    pages = []
    for name, t in docs:
        if name.endswith(".json"):
            if name == "interview.json":
                pages.append(interview_page(json.loads(t)))
            continue
        meta, body = {}, t
        if t.startswith("---"):
            _, fm, body = t.split("---", 2)
            meta = yaml.safe_load(fm) or {}
        html = markdown.markdown(body, extensions=["tables", "fenced_code"])
        html = re.sub(r'(?<![="])(https?://[^\s<|]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', html)
        pages.append({"title": meta.get("title", "문서"), "order": meta.get("order", 99), "html": html})
    return sorted(pages, key=lambda p: p["order"])


def _tokens(s):
    return re.findall(r"\s+|[^\s]+", s or "")


def diff_html(a, b):
    import difflib, html
    A, B = _tokens(a), _tokens(b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B, autojunk=False).get_opcodes():
        x, y = html.escape("".join(A[i1:i2])), html.escape("".join(B[j1:j2]))
        if op == "equal":
            out.append(x)
        else:
            if x.strip():
                out.append(f"<del>{x}</del>")
            if y.strip():
                out.append(f"<ins>{y}</ins>")
            elif op == "replace":
                out.append(y)
    return "".join(out)


def interview_page(data):
    from html import escape as e
    qs = data.get("questions", [])
    groups = {}
    for q in qs:
        groups.setdefault(q.get("group") or "개인 추가 질문", []).append(q)
    total_v = sum(len(q.get("versions") or []) for q in qs)
    reviewed = sum(1 for q in qs if q.get("reviews"))
    h = [f'<div class="iv-top"><div class="iv-stats"><span><b>{len(qs)}</b>문항</span><span><b>{total_v}</b>버전</span>'
         f'<span><b>{reviewed}</b>문항 AI 검토</span><span class="muted">동기화 {e(data.get("synced_at", ""))}</span></div>'
         f'<a class="iv-go" href="{e(data.get("practice_url", ""))}" target="_blank" rel="noopener">연습하러 가기 · 답변 수정 + AI 피드백 →</a></div>']
    for g, items in groups.items():
        h.append(f"<h2>{e(g)}</h2>")
        for q in items:
            vs = q.get("versions") or []
            revs = q.get("reviews") or {}
            last = vs[-1] if vs else None
            num = e(q.get("num") or "")
            h.append(f'<details class="iv-q"><summary><span class="n">{num}</span><span class="t">{e(q.get("title", ""))}</span>'
                     f'<span class="v">v{len(vs)}{" · 검토 " + str(len(revs)) if revs else ""}</span></summary><div class="iv-body">')
            if q.get("guide"):
                h.append(f'<div class="iv-guide"><b>피드백</b><br>{e(q["guide"]).replace(chr(10), "<br>")}</div>')
            if last:
                h.append(f'<p class="lbl">최신 답변 (v{len(vs)}{" · " + e(last.get("note")) if last.get("note") else ""})</p>'
                         f'<div class="iv-ans">{e(last["text"]).replace(chr(10), "<br>")}</div>')
            else:
                h.append('<p class="muted">아직 답변이 없습니다.</p>')
            if len(vs) > 1:
                h.append('<p class="lbl">버전별 변화</p>')
                for i in range(len(vs) - 1, 0, -1):
                    h.append(f'<details class="iv-diff"><summary>v{i} → v{i + 1} {e(vs[i].get("note") or "")}</summary>'
                             f'<div class="iv-ans">{diff_html(vs[i - 1]["text"], vs[i]["text"]).replace(chr(10), "<br>")}</div></details>')
            if revs:
                key = sorted(revs, key=lambda k: revs[k].get("at", ""))[-1]
                r = revs[key]
                a, b = (int(x) + 1 for x in key.split("-"))
                h.append(f'<p class="lbl">최근 AI 검토 ({"v" + str(b) if a == b else f"v{a} → v{b}"})</p><div class="iv-rev">')
                if r.get("summary"):
                    h.append(f'<p><b>{e(r["summary"])}</b></p>')
                if r.get("suggestions"):
                    h.append("<ul>" + "".join(f'<li><b>{e(s.get("point", ""))}</b> — {e(s.get("why", ""))}'
                                              + (f'<br><span class="muted">예시: {e(s["example"])}</span>' if s.get("example") else "") + "</li>"
                                              for s in r["suggestions"]) + "</ul>")
                if r.get("fact_flags"):
                    h.append("<p class='muted'>사실 확인: " + e(" / ".join(r["fact_flags"])) + "</p>")
                h.append("</div>")
            h.append("</div></details>")
    return {"title": "면접 준비", "order": 0, "html": "".join(h)}


def encrypt(payload, password):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(payload, ensure_ascii=False).encode(), None)
    e = lambda b: base64.b64encode(b).decode()
    return {"salt": e(salt), "iv": e(iv), "ct": e(ct), "iter": ITER}


def build(env, data):
    OUT.mkdir(parents=True, exist_ok=True)
    pem, pw = os.environ.get("PRIVATE_KEY"), os.environ.get("PRIVATE_PASSWORD")
    box = None
    if pem and pw and SEALED.exists() and any(SEALED.glob("*.json")):
        box = encrypt({"pages": render(unseal_all(pem))}, pw)
    (OUT / "index.html").write_text(env.get_template("private.html.j2").render(box=box, **data), encoding="utf-8")
    return bool(box)
