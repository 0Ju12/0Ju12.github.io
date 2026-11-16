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
