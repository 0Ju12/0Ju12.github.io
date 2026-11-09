"""강의 노트 원본을 공개키로 잠금 (평문 content/study/notes/·quiz/ 는 커밋 금지)

    python3 scripts/study_seal.py                      # 전체 → content/study_sealed/notes.sealed.json (추가 묶음 정리)
    python3 scripts/study_seal.py --add a.html b.html  # 새로 받은 노트만 → content/study_sealed/notes-<시각>.sealed.json

--add 는 개인키·전체 원본이 없는 환경(정기 작업 등)에서 새 노트·수정된 노트만 올릴 때 씁니다.
배포 빌드(study.py)가 PRIVATE_KEY 로 전체 묶음과 추가 묶음을 이름 순서대로 풀어 합칩니다(같은 파일 이름은 나중 것이 이김).
사이트에는 노트·문제가 암호(STUDY_PASSWORD, 없으면 PRIVATE_PASSWORD)로 암호화되어 올라갑니다.
"""
import base64, io, json, os, sys, time, zipfile
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
SRC, DIR = ROOT / "content" / "study" / "notes", ROOT / "content" / "study_sealed"
OAEP = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
b64 = lambda b: base64.b64encode(b).decode()


def seal(files, out):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f, arc in files:
            z.write(f, arc)
    pub = serialization.load_pem_public_key((ROOT / "keys" / "private_seal_pub.pem").read_bytes())
    key, nonce = AESGCM.generate_key(256), os.urandom(12)
    rec = {"v": 1, "name": "notes.zip", "key": b64(pub.encrypt(key, OAEP)), "nonce": b64(nonce),
           "ct": b64(AESGCM(key).encrypt(nonce, buf.getvalue(), None))}
    DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec), encoding="utf-8")
    print(f"sealed {len(files)} files → {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if len(sys.argv) > 2 and sys.argv[1] == "--add":
    files = []
    for a in sys.argv[2:]:
        p = Path(a)
        if p.suffix == ".html":
            files.append((p, p.name))
        elif p.suffix == ".json":
            files.append((p, f"quiz/{p.name}"))
        else:
            sys.exit(f"✗ {p.name}: .html 노트 또는 quiz .json 만 넣을 수 있습니다")
    seal(files, DIR / time.strftime("notes-%Y%m%d-%H%M%S.sealed.json", time.gmtime()))
else:
    files = [(f, f.name) for f in sorted(SRC.glob("*.html"))]
    files += [(f, f"quiz/{f.name}") for f in sorted((SRC.parent / "quiz").glob("*.json"))]   # 문제·개념 데이터도 함께
    if len(files) < 10:
        sys.exit("✗ 전체 원본이 없습니다. 새 노트만 올릴 때는 --add 를 쓰세요")
    seal(files, DIR / "notes.sealed.json")
    for old in DIR.glob("notes-*.sealed.json"):                    # 전체에 이미 포함된 추가 묶음 정리
        old.unlink()
        print(f"removed {old.name} (전체 묶음에 포함)")
