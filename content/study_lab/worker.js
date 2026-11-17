importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');
let ready=loadPyodide();
onmessage=async({data})=>{try{const py=await ready;py.globals.set('_user_code',data.code);py.globals.set('_user_input',data.input);const result=py.runPython(`
import sys, json, io, builtins
_rows = iter(_user_input.splitlines())
_events = []
_out = io.StringIO()
_old_input = builtins.input
_old_stdout = sys.stdout
builtins.input = lambda prompt='': next(_rows)
sys.stdout = _out
_count = 0
def _trace(frame, event, arg):
    global _count
    if frame.f_code.co_filename != '<student>': return _trace
    if event == 'line':
        _count += 1
        if _count > 6000: raise RuntimeError('실행 단계가 6,000개를 넘었어요. 입력을 줄여 주세요.')
        state = {}
        for k,v in frame.f_locals.items():
            if k.startswith('_'): continue
            if isinstance(v,(int,float,str,bool,list,tuple,type(None))):
                try:
                    s=json.dumps(v,ensure_ascii=False)
                    if len(s)<20000: state[k]=json.loads(s)
                except: pass
        _events.append({'line':frame.f_lineno,'vars':state,'output':_out.getvalue()})
    return _trace
_scope = {}
_error = None
try:
    sys.settrace(_trace)
    exec(compile(_user_code,'<student>','exec'),_scope)
except Exception as e:
    _error = type(e).__name__ + ': ' + str(e)
finally:
    sys.settrace(None)
    builtins.input = _old_input
    sys.stdout = _old_stdout
_final = {}
for _k,_v in _scope.items():
    if _k.startswith('_'): continue
    try:
        _s = json.dumps(_v,ensure_ascii=False)
        if len(_s)<20000: _final[_k]=json.loads(_s)
    except: pass
_events.append({'kind':'end','line':None,'vars':_final,'output':_out.getvalue()})
json.dumps({'events':_events,'output':_out.getvalue(),'error':_error},ensure_ascii=False)
`);postMessage(JSON.parse(result));}catch(e){postMessage({error:String(e),events:[]})}};
