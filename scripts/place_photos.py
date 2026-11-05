#!/usr/bin/env python3
"""커리어 지도 '연구 데이터' 장소에 사진·짧은 설명 후보를 채운다 (위키백과·위키미디어 공용).

  python3 scripts/place_photos.py          # data/career_map.yaml 의 wiki: 항목마다 조회
결과
  docs/assets/places/<id>.jpg              # 640px 썸네일 (공용 라이선스 사진)
  data/places_fetched.yaml                 # 사진 출처·저자·라이선스 + 위키 요약(설명 초안)
사람이 요약을 확인해 career_map.yaml 의 ko.about / en.about 과 photo: 로 옮긴다.
네트워크: en/ko.wikipedia.org, commons.wikimedia.org, upload.wikimedia.org 접근 필요.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "places"
UA = {"User-Agent": "0ju12-portfolio-place-photos/1.0 (https://0ju12.github.io)"}


def get(url, raw=False):
    for i in range(5):
        time.sleep(1.0)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                b = r.read()
            return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 4:
                raise
            time.sleep(5 * (i + 1))


def summary(lang, title):
    try:
        return get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(' ', '_'))}")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        q = get(f"https://{lang}.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=1&srsearch={urllib.parse.quote(title)}")
        hits = q.get("query", {}).get("search", [])
        return summary(lang, hits[0]["title"]) if hits and hits[0]["title"] != title else None


def credit(file_title):
    q = get("https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata|url&format=json&titles="
            + urllib.parse.quote(file_title))
    page = next(iter(q["query"]["pages"].values()))
    meta = (page.get("imageinfo") or [{}])[0].get("extmetadata", {})
    clean = lambda v: re.sub(r"<[^>]+>", "", (meta.get(v) or {}).get("value", "")).strip()
    return {"author": clean("Artist"), "license": clean("LicenseShortName"),
            "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(file_title.replace(" ", "_"))}


def main():
    places = yaml.safe_load((ROOT / "data" / "career_map.yaml").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    found = {}
    for pl in places:
        w = pl.get("wiki")
        if not w:
            continue
        lang, title = (w.split(":", 1) if re.match(r"^(en|ko):", w) else ("en", w))
        try:
            s = summary(lang, title)
        except Exception as e:
            print("✗", pl["id"], e); continue
        if not s:
            print("✗", pl["id"], "문서 없음"); continue
        rec = {"wiki_title": s.get("title"), "wiki_url": s.get("content_urls", {}).get("desktop", {}).get("page"),
               "extract": s.get("extract")}
        img = (s.get("originalimage") or {}).get("source")
        if img and img.lower().endswith((".jpg", ".jpeg", ".png")):
            fname = urllib.parse.unquote(img.rsplit("/", 1)[-1])
            try:
                import io
                from PIL import Image
                im = Image.open(io.BytesIO(get(img, raw=True))).convert("RGB")   # 원본(upload.wikimedia.org) → 로컬에서 축소
                im.thumbnail((960, 960))
                im.save(OUT / f"{pl['id']}.jpg", quality=84)
                rec["photo"] = {"src": f"assets/places/{pl['id']}.jpg", "file": fname, **credit("File:" + fname)}
            except Exception as e:
                print("  사진 실패:", pl["id"], e)
        elif img:
            rec["image_skipped"] = img
        found[pl["id"]] = rec
        print("✔", pl["id"], rec.get("wiki_title"), "· 사진" if img else "· 사진 없음")
    (ROOT / "data" / "places_fetched.yaml").write_text(yaml.safe_dump(found, allow_unicode=True, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
