"""Exercise the exact Python tracer embedded in the browser worker."""
import json
import subprocess
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'content/study_lab/worker.js').read_text().split('py.runPython(`',1)[1].split('`);const parsed',1)[0]
def run(code,inp='',trace=True):
    scope={'_user_code':code,'_user_input':inp,'_capture':trace}
    exec(SOURCE.rsplit("json.dumps({'events':",1)[0],scope)
    return scope
class AlgorithmTraceTest(unittest.TestCase):
    def test_deque_set_dict_and_immutable_stack_snapshots(self):
        r=run('from collections import deque\nqueue=deque([0])\nvisited={0}\ngraph={0:[1]}\nqueue.append(1)\nqueue.popleft()\nprint(queue)')
        self.assertIsNone(r['_error'])
        self.assertEqual(r['_events'][-1]['vars']['queue'],[1])
        self.assertTrue(any(e['vars'].get('queue')==[0] for e in r['_events']))
        self.assertTrue(any(e.get('types',{}).get('visited')=='set' for e in r['_events']))
    def test_recursive_calls_and_return_values_are_real_frames(self):
        r=run('def fact(n):\n    if n<=1: return 1\n    return n*fact(n-1)\nprint(fact(4))')
        self.assertEqual(r['_out'].getvalue().strip(),'24')
        self.assertTrue(any(len(e.get('stack',[]))>=4 for e in r['_events']))
        self.assertTrue(any(e.get('kind')=='return' and e.get('returnValue')==24 for e in r['_events']))
    def test_non_trace_runs_are_isolated_and_report_steps_and_errors(self):
        r=run('print(int(input())*2)','3',False)
        self.assertEqual(r['_events'],[]);self.assertEqual(r['_out'].getvalue(),'6\n');self.assertGreater(r['_count'],0)
        bad=run('raise ValueError("test")','',False)
        self.assertIn('ValueError',bad['_error'])
        self.assertNotIn('queue',run('print(1)')['_scope'])
    def test_output_guard_stops_unbounded_printing(self):
        self.assertIn('100,000',run('print("a"*100001)')['_error'])

    def test_learning_examples_execute_as_documented(self):
        js="const fs=require('fs'),vm=require('vm');const c=vm.createContext({});vm.runInContext(fs.readFileSync('templates/interview/practice.js.j2','utf8'),c);process.stdout.write(JSON.stringify(c.DEMOS));"
        demos=json.loads(subprocess.check_output(['node','-e',js],cwd=ROOT,text=True))
        for name,expected in [('calculator','23'),('bfs','[0, 1, 2, 3]'),('recursion','120')]:
            r=run(demos[name]['code'],demos[name]['input'])
            self.assertIsNone(r['_error'],name)
            self.assertEqual(r['_out'].getvalue().strip(),expected)

    def test_infinite_dp_sentinel_is_json_safe(self):
        r=run('dist=[0,float("inf")]\nprint(1)')
        self.assertEqual(r['_events'][-1]['vars']['dist'],[0,'inf'])
        json.loads(json.dumps(r['_events'],allow_nan=False))

    def test_large_integer_values_are_exact_in_json(self):
        r=run('n=10**30')
        self.assertEqual(r['_events'][-1]['vars']['n'],str(10**30))
