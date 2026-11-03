#!/usr/bin/env python3
"""디자인 시안 렌더링: templates/layouts/<이름>.html.j2 → docs/design-<이름>.html

    python3 scripts/layouts.py            # 시안 전부
    python3 scripts/layouts.py bento      # 특정 시안만
data/portfolio.yaml 의 site.layout 을 지정하면 build.py 가 그 시안을 index.html 로 사용합니다.
"""
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import DATA, DOCS, TEMPLATES, load_posts, normalize  # noqa: E402


def render(names=None):
    data = normalize(yaml.safe_load(DATA.read_text(encoding="utf-8")))
    data["posts"] = load_posts(data.get("activities", []))
    data["study_notes"] = sorted((DOCS / "study" / "notes").glob("*.html"))
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    out = []
    for f in sorted((TEMPLATES / "layouts").glob("*.html.j2")):
        name = f.name.split(".")[0]
        if names and name not in names:
            continue
        html = env.get_template(f"layouts/{f.name}").render(**data)
        html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)  # 시안은 검색 노출 제외
        (DOCS / f"design-{name}.html").write_text(html, encoding="utf-8")
        out.append(name)
    if not names:  # 시안 비교 페이지
        cur = (data.get("site") or {}).get("layout")
        html = env.get_template("design-picker.html.j2").render(designs=DESIGNS, current=cur, **data)
        (DOCS / "design-picker.html").write_text(html, encoding="utf-8")
    return out


DESIGNS = [
    {"id": "showcase", "name": "Showcase (현재)", "ref": "현재 사이트",
     "desc": "어두운 히어로 + 학업 단계별(석사·학부·부트캠프) 큰 사례 카드. 지금 0ju12.github.io 에 적용된 시안."},
    {"id": "showcase-pro", "name": "★ Showcase Pro", "ref": "현재 시안의 구성·색을 유지하고 다듬은 버전",
     "desc": "현재 느낌(어두운 히어로 + 좌우 교차 사례)을 그대로 두고 다듬었습니다. Pretendard·숫자 정렬, 스크롤해도 따라오는 상단 메뉴, 버튼 7개를 주요 2개 + 아이콘 3개로 정리, 기울어진 사진 대신 프로필 카드, 이모지 대신 아이콘. 프로젝트는 7개로 나눠 화면 캡처는 브라우저 프레임, 그림은 캡션, 이미지가 없으면 핵심 수치 패널로 보여 줍니다."},
    {"id": "report", "name": "A · Report", "ref": "Eugene Yan(eugeneyan.com)처럼 글과 사례 연구가 중심인 ML 엔지니어 사이트",
     "desc": "종이 질감 배경, 세리프 제목, 고정폭 메타데이터. 프로젝트 7개를 '기간 · 제목 · 핵심 수치' 표로 보여 주고, 행을 누르면 사례가 펼쳐집니다. 읽는 사람이 30초 안에 전체를 훑을 수 있는 구조."},
    {"id": "gallery", "name": "B · Gallery", "ref": "국내 IT 기업 채용 페이지·서비스형 포트폴리오의 카드 UI",
     "desc": "Pretendard, 밝은 카드 그리드. 화면 캡처가 있는 프로젝트는 썸네일로, 없는 것은 핵심 수치로 보여 줍니다. LLM·RAG / 딥러닝 / 데이터 / 연구 필터, 카드를 누르면 상세 창이 열립니다."},
    {"id": "pipeline", "name": "C · Pipeline", "ref": "개발자 도구·데이터 플랫폼 랜딩 페이지의 다크 테마",
     "desc": "다크 + 격자 배경 + 고정폭 글꼴. 첫 화면에 '수집 → 정제 → 학습·색인 → 검증 → 결과' 흐름도를 두고, 각 단계에 실제로 쓴 도구를 적었습니다. 데이터 엔지니어 지원에 가장 직접적인 메시지."},
    {"id": "sidebar", "name": "이전 시안 · Sidebar", "ref": "왼쪽 고정 사이드바형",
     "desc": "이전에 만들어 둔 시안. 왼쪽 고정 프로필 + 오른쪽 스크롤."},
    {"id": "bento", "name": "이전 시안 · Bento", "ref": "벤토 그리드형",
     "desc": "이전에 만들어 둔 시안. 크기가 다른 타일을 격자로 배치."},
]


if __name__ == "__main__":
    print("✔", ", ".join(render(sys.argv[1:] or None)))
