import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import yaml
from jinja2 import Environment, FileSystemLoader
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build, study
class LearningTest(unittest.TestCase):
 def test_pure_helpers(self):
  subprocess.run(['node','--test','tests/learning.test.cjs'],cwd=ROOT,check=True)
 def test_separate_cases_and_qualified_metrics_render(self):
  data=build.normalize(yaml.safe_load((ROOT/'data/portfolio.yaml').read_text()))
  self.assertEqual(len(data['selected_cases']['data']),3)
  for ids in data['selected_cases'].values():
   for i in ids:self.assertIn(i,data['project_lookup'])
  self.assertIn('heritage',data['project_lookup']);self.assertIn('vqa',data['project_lookup'])
  self.assertNotIn('ssafy-16',data['project_lookup'])   # 관통 프로젝트는 비공개
  env=Environment(loader=FileSystemLoader(ROOT/'templates'))
  for i in ['heritage','vqa','hankki']:
   html=env.get_template('project.html.j2').render(sp=data['project_lookup'][i],group={},prev=None,next=None,related=[],en=False,**data)
   self.assertIn('성과 수치의 의미',html)
  for t in ['learning-demo.html.j2','evaluation.html.j2']:
   self.assertIn('<!doctype html>',env.get_template(t).render(**data))
 def test_note_anchors_survive_existing_ids_and_skip_sections(self):
  note={'title':'test','raw':'<body><h2 id="old">1. 스택</h2><h2>2. 후위 표기</h2></body>','track':'algo','slug':'stack2','nq':0}
  html=study.inject(note,None,None)
  self.assertIn('learn-section-0',html);self.assertIn('learn-section-1',html);self.assertIn('id="old"',html)
 def test_examples_are_equivalent_and_prune_visits(self):
  import re
  s=(ROOT/'templates/interview/learning.js.j2').read_text()
  a=json.loads(re.search(r'var PAIR_A=(".*?");',s).group(1))
  b=a.replace('    if i == n:', '    if total > target:\n        return\n    if i == n:')
  for n,target,arr in [(0,0,''),(3,0,'1 2 3'),(8,10,'1 2 3 4 5 6 7 8')]:
   inp=f'{n} {target}\n{arr}\n';results=[]
   for code in [a,b]:
    p=subprocess.run([sys.executable,'-c',code+'\nprint(visits)'],input=inp,text=True,capture_output=True,check=True)
    results.append(p.stdout.splitlines())
   self.assertEqual(results[0][0],results[1][0]);self.assertLessEqual(int(results[1][1]),int(results[0][1]))
