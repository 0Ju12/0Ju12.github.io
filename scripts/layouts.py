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
from build import DATA, DOCS, TEMPLATES, normalize  # noqa: E402


def render(names=None):
    data = normalize(yaml.safe_load(DATA.read_text(encoding="utf-8")))
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    out = []
    for f in sorted((TEMPLATES / "layouts").glob("*.html.j2")):
        name = f.name.split(".")[0]
        if names and name not in names:
            continue
        html = env.get_template(f"layouts/{f.name}").render(**data)
        (DOCS / f"design-{name}.html").write_text(html, encoding="utf-8")
        out.append(name)
    return out


if __name__ == "__main__":
    print("✔", ", ".join(render(sys.argv[1:] or None)))
