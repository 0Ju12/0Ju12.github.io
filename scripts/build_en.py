#!/usr/bin/env python3
"""English edition: data/portfolio.en.yaml → docs/en.html, docs/resume-en.html, docs/resume-1page-en.html

Same templates as the Korean site; Korean UI labels are swapped for English after rendering.
Writing / study pages are Korean-only, so they are linked rather than rendered here.
Usage: python3 scripts/build_en.py   (scripts/build.py calls this at the end)
"""
import re
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

import build

ROOT = build.ROOT
DATA = ROOT / "data" / "portfolio.en.yaml"

# Korean UI label → English (longest first so partial phrases don't clash)
LABELS = [
    ("<h1>지구과학 데이터를<br><span>딥러닝</span>으로 풀어냅니다.</h1>", "<h1>Geoscience data,<br>solved with <span>deep learning</span>.</h1>"),
    ("SSAFY 강의 노트", "SSAFY lecture notes"),
    ("WEB · Django · DB · 알고리즘 · AI를 주제별로 다시 정리한 학습 공간", "Study space — lecture notes on Web · Django · DB · algorithms · AI (in Korean)"),
    ("data/portfolio.yaml 에서 자동 생성", "generated from data/portfolio.en.yaml"),
    ("프로젝트에서 배운 것", "What I learned from projects"),
    ("문제 → 역할 → 결과", "problem → role → result"),
    ("함께 일할 기회를 기다립니다.", "Looking forward to working together."),
    ("역량 · 학력 · 수상", "Skills · Education · Awards"),
    ("학습 공간 열기", "Open study space"),
    ("지구과학 데이터를", "Geoscience data,"),
    ("으로 풀어냅니다.", " to the answer."),
    ("대표 프로젝트", "Selected work"),
    ("이력서 (1장)", "Resume (1 page)"),
    ("상세 이력서", "Full resume"),
    ("메일 보내기", "Send email"),
    ("자세히 보기", "Details"),
    ("실습 프로그램", "programs"),
    ("프로필 사진", "Profile photo"),
    ("📜 자격", "📜 Certifications"),
    ("EXPERIENCE · 핵심 활동", "EXPERIENCE"),
    ("OTHER ACTIVITIES · 기타 활동", "OTHER ACTIVITIES"),
    ("PUBLICATIONS · 논문 및 발표", "PUBLICATIONS"),
    ("PUBLICATIONS · 연구 성과", "PUBLICATIONS"),
    ("EDUCATION · 교육", "EDUCATION"),
    ("PROJECTS · 핵심 경험", "PROJECTS"),
    ("SKILLS · 기술", "SKILLS"),
    ("이력서 (요약)", "Resume (summary)"),
    ("(전체 목록은 포트폴리오 참고)", "(full list on the portfolio site)"),
    ("[논문]", "[Paper]"),
    ("[발표]", "[Talk]"),
    ("딥러닝", "deep learning"),
    ("이메일", "Email"),
    ("포트폴리오", "Portfolio"),
    ("이력서", "Resume"),
    ("테마", "Theme"),
    ("읽기", "Read"),
    ("접기", "Close"),
    ("문제", "Problem"),
    ("역할", "Role"),
    ("한 일", "Actions"),
    ("결과", "Results"),
]
REGEX = [
    (r"(\d+)개 프로젝트", r"\1 projects"),
    (r"학회 발표 (\d+)건 보기", r"Show \1 conference talks"),
    (r"외 학회 발표 (\d+)건", r"+ \1 conference talks"),
    (r"논문 (\d+)\s*·\s*학회 발표 (\d+)", r"\1 papers · \2 talks"),
    (r"(\d+)편", r"\1"),
    (r"✍️ 글: [^<]*", ""),
]


def to_english(html: str) -> str:
    html = html.replace('<html lang="ko">', '<html lang="en">')
    # 파일 경로(src/href)는 번역하지 않도록 잠시 빼 둔다 — 예: "..._결과화면.jpg" 가 "Results화면" 으로 깨지는 문제
    kept = []
    def _keep(m):
        kept.append(m.group(0))
        return f"\x00{len(kept) - 1}\x00"
    html = re.sub(r'(?:src|href)="[^"]*"', _keep, html)
    for pat, rep in REGEX:
        html = re.sub(pat, rep, html)
    for ko, en in LABELS:
        html = html.replace(ko, en)
    html = re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], html)
    # Korean-only pages: point resume buttons at the English PDFs
    html = html.replace('href="resume-1page.pdf"', 'href="resume-1page-en.pdf"').replace('href="resume.pdf"', 'href="resume-en.pdf"')
    return html


CAPTIONS = {
    "캘거리_중력탐사_현장측정": "Calgary — gravity survey in the field",
    "석사_학위수여식": "M.S. commencement",
    "석사학위논문_(표지)": "M.S. thesis — cover",
    "Fig03_": "M.S. thesis Fig. 3 — WCF → LFI five-step workflow",
    "Fig10_": "M.S. thesis Fig. 10 — basement/salt classes by CC(k) band",
    "Fig11_": "M.S. thesis Fig. 11 — SLFI (basement) · DLFI (salt) maps",
    "프로젝트_장려상·수료증": "POSCO academy — Excellence Award & certificate",
    "관통5_LLM_댓글분석_결과화면": "ThRead — LLM comment-analysis result screen",
    "국보입문가이드_RAG": "Heritage RAG guide — Q&A showing only verified citations",
    "학회_참가": "2022 — conference badges (KSEG · K-CCUS)",
    "유타_FORGE_지열부지_포스터발표": "2024.04 — Utah FORGE poster presentation",
}


def translate_captions(acts):
    for g in acts:
        for a in [g] + (g.get("projects") or []):
            for item in a.get("gallery") or []:
                for key, en in CAPTIONS.items():
                    if key in item["src"]:
                        item["caption"] = en
                        break


def main():
    data = build.normalize(yaml.safe_load(DATA.read_text(encoding="utf-8")))
    translate_captions(data["activities"])
    data["posts"] = []          # Writing is Korean-only
    data["study_notes"] = []
    data["private_ready"] = False
    data["evidence"] = build.evidence_index(data, en=True)
    env = Environment(loader=FileSystemLoader(build.TEMPLATES),
                      autoescape=select_autoescape(["html", "j2"], default_for_string=False),
                      trim_blocks=True, lstrip_blocks=True)
    layout = (data.get("site") or {}).get("layout", "showcase")
    out = {
        "en.html": env.get_template(f"layouts/{layout}.html.j2").render(alt_lang={"url": "index.html", "label": "KO", "code": "ko"}, **data),
        "resume-en.html": env.get_template("resume.html.j2").render(**data),
        "resume-1page-en.html": env.get_template("resume-1page.html.j2").render(**data),
    }
    md = Environment(loader=FileSystemLoader(build.TEMPLATES), trim_blocks=True, lstrip_blocks=True)
    (build.OUT / "profiles-en.md").write_text(
        md.get_template("profiles.md.j2").render(**data).replace(
            "| 석사(SCIE 제1저자) · 시공간 딥러닝 · LLM 파인튜닝·RAG · 데이터 파이프라인",
            "| M.S. (SCIE first author) · Spatiotemporal deep learning · LLM fine-tuning & RAG · Data pipelines"),
        encoding="utf-8")
    print("✔ out/profiles-en.md")
    for name, html in build.project_pages(env, data, en=True).items():
        (build.DOCS / "projects" / name).write_text(to_english(html), encoding="utf-8")
    print("✔ docs/projects/*-en.html")
    for name, html in out.items():
        html = to_english(html)
        left = sorted(set(re.findall(r"[가-힣][가-힣 ·]*", re.sub(r"<!--.*?-->|<script.*?</script>|src=\"[^\"]*\"", "", html, flags=re.S))))
        (build.DOCS / name).write_text(html, encoding="utf-8")
        print(f"✔ docs/{name}" + (f"  (Korean left: {left[:8]})" if left else ""))


if __name__ == "__main__":
    main()
