# 사진 원본 폴더 (git에 올라가지 않음)

- `profile.jpg` — 프로필 사진
- `<활동 id>/` — 활동별 사진. 폴더 이름은 data/portfolio.yaml 의 활동 id 와 같아야 합니다.
  - wildfire-capstone / posco-pospeak / masters / calgary-2024 / undergrad-research
- 파일 이름이 사진 설명이 됩니다: `2024-11_KSEG_포스터발표.jpg` → "2024-11 KSEG 포스터발표"

넣은 뒤: `python3 scripts/photos.py && python3 scripts/build.py`
