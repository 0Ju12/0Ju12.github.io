"""비공개 원문(content/private/*.md, 커밋 금지)을 공개키로 잠가 content/private_sealed/*.json 으로 저장

    python3 scripts/private_seal.py            # 전체 다시 잠그기
    python3 scripts/private_seal.py 02-evidence.md

잠긴 파일은 저장소의 공개키(keys/private_seal_pub.pem)로만 만들 수 있고,
GitHub Actions 비밀값 PRIVATE_KEY 가 있어야 풀 수 있습니다. 평문은 저장소에 남지 않습니다.
"""
import base64, json, os, sys
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "content" / "private", ROOT / "content" / "private_sealed"
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
b64 = lambda b: base64.b64encode(b).decode()


def seal(path):
    pub = serialization.load_pem_public_key((ROOT / "keys" / "private_seal_pub.pem").read_bytes())
    key, nonce = AESGCM.generate_key(256), os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, path.read_bytes(), None)
    rec = {"v": 1, "name": path.name, "key": b64(pub.encrypt(key, OAEP)), "nonce": b64(nonce), "ct": b64(ct)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (path.name.replace(".", "_") + ".sealed.json")).write_text(json.dumps(rec), encoding="utf-8")
    print("sealed", path.name)


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(p.name for p in SRC.iterdir() if p.suffix in (".md", ".json"))
    for n in names:
        seal(SRC / n)
