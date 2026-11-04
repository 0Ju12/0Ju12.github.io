"""강의 노트 원본(content/study/notes/*.html, 커밋 금지)을 묶어 공개키로 잠금 → content/study_sealed/notes.sealed.json

    python3 scripts/study_seal.py

잠긴 파일은 GitHub Actions 비밀값 PRIVATE_KEY 로만 풀 수 있고(study.py 가 배포 빌드 때 풂),
사이트에는 강의 노트 페이지가 암호(STUDY_PASSWORD, 없으면 PRIVATE_PASSWORD)로 암호화되어 올라갑니다.
"""
import base64, io, json, os, zipfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "content" / "study" / "notes", ROOT / "content" / "study_sealed" / "notes.sealed.json"
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
b64 = lambda b: base64.b64encode(b).decode()

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(SRC.glob("*.html")):
        z.write(f, f.name)
pub = serialization.load_pem_public_key((ROOT / "keys" / "private_seal_pub.pem").read_bytes())
key, nonce = AESGCM.generate_key(256), os.urandom(12)
rec = {"v": 1, "name": "notes.zip", "key": b64(pub.encrypt(key, OAEP)), "nonce": b64(nonce),
       "ct": b64(AESGCM(key).encrypt(nonce, buf.getvalue(), None))}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rec), encoding="utf-8")
print(f"sealed {len(list(SRC.glob('*.html')))} notes → {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
