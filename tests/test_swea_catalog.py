import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SweaCatalogTest(unittest.TestCase):
    def test_official_catalogue_is_complete_and_unique(self):
        d=json.loads((ROOT/'content/study_lab/swea-catalog.json').read_text())
        self.assertEqual(d['count'],len(d['items']))
        self.assertEqual(len({p['number'] for p in d['items']}),d['count'])
        self.assertEqual(set(d['counts']),{'D1','D2','D3','D4'})
        for level,n in d['counts'].items():
            self.assertEqual(n,sum(p['level']==level for p in d['items']))
            self.assertGreater(n,0)
        self.assertEqual(d['pageCount'],(d['count']+9)//10)
        for p in d['items']:
            self.assertTrue(p['title'])
            self.assertIn(p['contestProbId'],p['url'])
            self.assertTrue(p['url'].startswith('https://swexpertacademy.com/'))
    def test_workspace_and_backup_behaviour(self):
        subprocess.run(['node','--test','tests/swea.test.cjs'],cwd=ROOT,check=True)
