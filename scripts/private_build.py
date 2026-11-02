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
        docs.append(AESGCM(key).decrypt(base64.b64decode(r["nonce"]), base64.b64decode(r["ct"]), None).decode("utf-8"))
    return docs


def render(md_texts):
    import markdown, yaml
    pages = []
    for t in md_texts:
        meta, body = {}, t
        if t.startswith("---"):
            _, fm, body = t.split("---", 2)
            meta = yaml.safe_load(fm) or {}
        html = markdown.markdown(body, extensions=["tables", "fenced_code"])
        html = re.sub(r'(?<![="])(https?://[^\s<|]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', html)
        pages.append({"title": meta.get("title", "문서"), "order": meta.get("order", 99), "html": html})
    return sorted(pages, key=lambda p: p["order"])


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
