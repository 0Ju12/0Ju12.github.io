import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import interview
import study
from jinja2 import Environment, FileSystemLoader

class Locker:
    password = 'fixture-only'
    def page(self, title, body, home, **kwargs):
        self.body = body
        return '<html><body>encrypted-fixture</body></html>'

class InterviewBuildTest(unittest.TestCase):
    def test_metadata_is_built_and_public_version_has_no_private_payload(self):
        env = Environment(loader=FileSystemLoader(ROOT / 'templates'))
        data = {'profile': {'name': '검증 사용자', 'headline': '검증용', 'name_en': 'Fixture'}, 'activities': []}
        locker = Locker()
        with tempfile.TemporaryDirectory() as tmp, patch.object(interview, 'OUT', Path(tmp)), patch.object(study, 'LOCKER', locker, create=True), patch.object(interview, '_private', return_value=[]), patch.object(interview, '_private_questions', return_value=[]), patch.object(interview, '_bank_questions', return_value=[]):
            result = interview.build(env, data)
            release = json.loads((Path(tmp) / 'version.json').read_text())
            self.assertEqual(set(release), {'version', 'built_at'})
            self.assertEqual(len(release['version']), 32)
            self.assertNotIn('questions', json.dumps(release))
            self.assertIn(release['version'], locker.body)
            self.assertIn('자료 갱신 상태', locker.body)
            self.assertGreater(result['questions'], 0)
            self.assertIn('encrypted-fixture', (Path(tmp) / 'index.html').read_text())

class PersonalDraftTest(unittest.TestCase):
    def test_personal_drafts_keep_stable_id_and_source_metadata(self):
        row = {"id": "draft:fixture", "q": "검증 질문", "a": "검증용 답변", "c": "인성", "sources": [{"title": "검증", "url": "https://example.com"}]}
        with patch.object(interview, '_private', side_effect=lambda name, path: [row] if name == 'interview_drafts.json' else []), patch.object(interview, '_prep', return_value={}):
            result = interview.questions({"activities": []}, [])
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['id'], 'draft:fixture')
            self.assertEqual(result[0]['kind'], 'draft')
            self.assertEqual(result[0]['target_seconds'], 60)
            self.assertEqual(result[0]['sources'], row['sources'])

if __name__ == '__main__':
    unittest.main()

class CareerContentTest(unittest.TestCase):
    def test_essays_have_stable_ids_and_missing_facts_are_marked(self):
        from career_content import prepare_essays
        prep={'experiences':[], 'essays':[{'q':'우리 회사에 지원한 동기','g':'지원 동기'}, {'q':'갈등이 있었던 경험','g':'협업'}]}
        rows=prepare_essays(prep)
        self.assertIn('[회사명]', rows[0]['draft'])
        self.assertIn('[실제로',rows[1]['draft'])
        prep['essays'].reverse()
        self.assertEqual(rows[0]['id'],prepare_essays(prep)[1]['id'])
    def test_every_deck_has_five_to_ten_minutes_and_sourced_figures(self):
        import yaml
        from career_content import rebuild_decks
        data=yaml.safe_load((ROOT/'data/portfolio.yaml').read_text())
        data['case_notes']=yaml.safe_load((ROOT/'data/case_notes.yaml').read_text())
        variants=yaml.safe_load((ROOT/'data/resume_variants.yaml').read_text())
        rows=rebuild_decks(data,variants,interview._projects(data))
        self.assertEqual(len(rows),14)   # 직무별 4개 + 프로젝트 10개(한끼 포함)
        for deck in rows:
            self.assertTrue(300<=deck['estimated_seconds']<=600,deck['id'])
            figures=[s for s in deck['slides'] if s.get('img')]
            self.assertGreaterEqual(len(figures),3)
            self.assertGreaterEqual(len(deck['slides']),12)
            for figure in figures:
                self.assertTrue((ROOT/'docs/interview'/figure['img']).resolve().exists(),figure['img'])
                self.assertTrue(figure['credit'])
                self.assertTrue(figure['image_source'].startswith('https://'))
        self.assertIn('BERTScore',str(next(d for d in rows if d['id']=='posco-pospeak')))

class AuthoredCopyTest(unittest.TestCase):
    def test_all_current_essay_prompts_have_distinct_authored_copy(self):
        import yaml
        from career_content import prepare_essays
        prep=yaml.safe_load((ROOT/'data/prep.yaml').read_text())
        rows=prepare_essays(prep)
        self.assertEqual(len(rows),30)
        self.assertEqual(len({r['draft'] for r in rows}),30)
        self.assertTrue(all(len(r['draft'])>300 for r in rows))
        self.assertIn('BERTScore',next(r for r in rows if '실패를 경험' in r['q'])['draft'])
    def test_each_public_project_has_an_authored_storyboard(self):
        import yaml
        from career_copy import PROJECTS
        data=yaml.safe_load((ROOT/'data/portfolio.yaml').read_text())
        for group in data['activities']:
            for project in group.get('projects',[]):
                story=PROJECTS[project['id']]
                self.assertEqual(len(story),5)
                self.assertTrue(all(len(row[2])>80 for row in story))
