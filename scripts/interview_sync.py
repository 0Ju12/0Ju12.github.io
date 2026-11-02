"""면접 답변 노트(claude.ai 페이지)의 DB 스냅샷 → content/private/interview.json (비공개 원문, 커밋 금지)

    # 1) ArtifactData list (out_dir) 로 questions 컬렉션을 JSON 파일로 저장
    # 2) python3 scripts/interview_sync.py <스냅샷 폴더>/questions
    # 3) python3 scripts/private_seal.py interview.json  → 잠근 파일만 커밋
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1])
qs = []
for f in sorted(src.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    d["id"] = f.stem
    qs.append(d)
qs.sort(key=lambda d: (d.get("order", 999), d["id"]))
out = {"synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
       "practice_url": "https://claude.ai/artifact/MrbLjcYsJ9DcdHz1zGhZ9S", "questions": qs}
dst = ROOT / "content" / "private" / "interview.json"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(qs)} questions → {dst}")
