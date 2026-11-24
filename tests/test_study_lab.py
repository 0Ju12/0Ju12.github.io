"""Synthetic notes verify integration without accessing sealed lecture material."""
import base64
import gzip
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import study

class StudyLabTest(unittest.TestCase):
    def test_build_keeps_lab_encrypted_and_links_unlocked_notes(self):
        env = Environment(loader=FileSystemLoader(ROOT / 'templates'))
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'notes'
            out = Path(td) / 'out'
            src.mkdir(); out.mkdir()
            (src / 'SW02_List2.html').write_text('<html><head><title>SW 02. List 2 (0902)</title></head><body><h2>2차원 배열</h2><pre class="sourceCode python"><code>arr = [[1, 2]]</code></pre></body></html>')
            with patch.object(study, 'SRC', src), patch.object(study, 'OUT', out), patch.dict(os.environ, {'STUDY_PASSWORD':'synthetic-fixture-password'}):
                notes = study.build(env, {'profile':{'name':'Fixture'}})
            self.assertEqual(notes[0]['slug'], 'list2')
            lab = (out / 'lab/index.html').read_text()
            self.assertNotIn('id="code"', lab)
            self.assertIn('id="box"', lab)
            payload = json.loads(lab.split('<script id="box" type="application/json">')[1].split('</script>')[0])
            pt = AESGCM(study.LOCKER.key).decrypt(base64.b64decode(payload['iv']),base64.b64decode(payload['ct']),None)
            self.assertEqual(payload.get('gz'), 1)   # 암호화 전에 gzip 으로 줄임
            raw = gzip.decompress(pt).decode()
            self.assertIn('id="code"', raw)
            self.assertIn('../notes/list2.html', raw)
            self.assertTrue((out / 'lab/note-bridge.js').exists())
            for name in ['app.js','worker.js','style.css']:
                self.assertTrue((out / 'lab' / name).exists())
            injected=study.inject(notes[0],None,None)
            self.assertIn('../index.html#/algo',injected)
            self.assertIn('../lab/note-bridge.js',injected)

    def test_non_algorithm_note_has_no_python_handoff(self):
        note={'slug':'django_form','title':'Form','track':'django','raw':'<body><p>form</p></body>'}
        self.assertNotIn('note-bridge.js',study.inject(note,None,None))

if __name__ == '__main__': unittest.main()
