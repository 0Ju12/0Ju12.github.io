"""Render only synthetic data for browser tests; never unseal personal content."""
import json
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
ROOT = Path(__file__).resolve().parents[1]
def render(target):
    target.mkdir(parents=True, exist_ok=True)
    app = {
        'name': '검증 사용자', 'roles': {'data': '데이터'}, 'cats': ['인성', '프로젝트', 'OPIc'],
        'questions': [{'id': 'q1', 'c': '인성', 'g': '기본', 'q': '프로젝트에서 배운 점은 무엇인가요?', 'a': '문제를 정의하고 결과를 검증했습니다.', 'kind': 'mine'}],
        'decks': [{'id': 'demo', 'title': '프로젝트 발표', 'kind': 'project', 'min': 3, 'slides': [{'t': 'title', 'h': '프로젝트', 'note': '발표 노트'}]}],
        'prep': {'goals': [], 'weekly': [], 'essays': []},
        'metadata': {'version': 'fixture-v1', 'built_at': '2026-11-16T00:00:00+00:00', 'sources': [{'name': '공채 정보', 'path': 'data/recruit.yaml', 'updated': '2026-11-01', 'description': '검증용 자료'}]},
    }
    env = Environment(loader=FileSystemLoader(ROOT / 'templates'))
    (target / 'index.html').write_text(env.get_template('interview.html.j2').render(app=app, profile={'name': '검증 사용자'}), encoding='utf-8')
    (target / 'version.json').write_text(json.dumps({'version': 'fixture-v1'}), encoding='utf-8')
if __name__ == '__main__':
    render(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'work' / 'interview-fixture')
