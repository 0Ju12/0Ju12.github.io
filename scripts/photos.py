#!/usr/bin/env python3
"""photos/ 폴더의 원본 사진을 웹용으로 변환해 docs/assets/photos/ 에 저장합니다.

  photos/profile.jpg                 → 프로필 사진 (정사각형 600px)
  photos/<활동 id>/*.jpg|png|heic... → 해당 활동의 갤러리 (긴 변 1600px)

- 위치(GPS) 등 EXIF 정보는 모두 제거합니다 (개인정보 보호).
- 파일 이름이 사진 설명이 됩니다. 예) 2024-11_KSEG_포스터발표.jpg → "2024-11 KSEG 포스터발표"
- 원본 photos/ 는 git에 올라가지 않습니다 (.gitignore).
사용: python3 scripts/photos.py
"""
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "photos"
DST = ROOT / "docs" / "assets" / "photos"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def load(path: Path) -> Image.Image:
    if path.suffix.lower() in {".heic", ".heif"}:
        from pillow_heif import register_heif_opener  # pip install pillow-heif
        register_heif_opener()
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)  # 휴대폰 사진 회전 보정
    return im.convert("RGB")


def save(im: Image.Image, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=85, optimize=True, progressive=True)  # EXIF 없이 저장


def main():
    n = 0
    for f in sorted(SRC.rglob("*")):
        if f.suffix.lower() not in EXTS or f.name.startswith("."):
            continue
        rel = f.relative_to(SRC)
        if rel.parts[0].startswith("profile") and len(rel.parts) == 1:
            im = ImageOps.fit(load(f), (600, 600), centering=(0.5, 0.35))
            save(im, DST / "profile.jpg")
        else:
            im = load(f)
            im.thumbnail((1600, 1600))
            save(im, DST / rel.with_suffix(".jpg"))
        n += 1
        print("✔", rel)
    print(f"{n}장 변환 완료 → docs/assets/photos/")


if __name__ == "__main__":
    main()
