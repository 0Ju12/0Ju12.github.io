importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');
let ready=loadPyodide();
onmessage=async({data})=>{const started=performance.now();try{const py=await ready;py.globals.set('_user_code',data.code);py.globals.set('_user_input',data.input);py.globals.set('_capture',data.trace!==false);const result=py.runPython(`
import sys, json, io, builtins, math
from collections import deque
_rows = iter(_user_input.splitlines())
_events = []
_old_input, _old_stdout = builtins.input, sys.stdout
class _LimitedOutput(io.StringIO):
    def write(self, text):
        if self.tell()+len(text)>100000: raise RuntimeError('출력이 100,000자를 넘었어요.')
        return super().write(text)
_out = _LimitedOutput()
builtins.input = lambda prompt='': next(_rows)
sys.stdout = _out
_count, _bytes = 0, 0
_scope = {}
def _value(v, depth=0):
    if depth>4: return '…'
    if isinstance(v,int) and not isinstance(v,bool) and abs(v)>9007199254740991: return str(v)
    if isinstance(v,float) and not math.isfinite(v): return str(v)
    if isinstance(v,(int,float,str,bool,type(None))): return v[:2000] if isinstance(v,str) else v
    if isinstance(v,(list,tuple,set,deque)): return [_value(x,depth+1) for x in list(v)[:150]]
    if isinstance(v,dict): return {str(k):_value(x,depth+1) for k,x in list(v.items())[:150]}
    raise TypeError()
def _snapshot(locals):
    state={}
    for k,v in list(locals.items()):
        if k.startswith('_'): continue
        try:
            value=_value(v)
            if len(json.dumps(value,ensure_ascii=False))<20000: state[k]=value
        except: pass
    return state
def _trace(frame, event, arg):
    global _count, _bytes
    if frame.f_code.co_filename!='<student>': return _trace
    if event in ('line','return'):
        _count+=1
        if _count>(6000 if _capture else 1000000): raise RuntimeError('실행 단계 한도를 넘었어요. 입력을 줄이거나 반복문을 확인하세요.')
        if _capture:
            chain=[]; f=frame
            while f and len(chain)<40:
                if f.f_code.co_filename=='<student>': chain.append({'name':f.f_code.co_name,'line':f.f_lineno,'vars':_snapshot(f.f_locals)})
                f=f.f_back
            state=_snapshot(_scope); state.update(_snapshot(frame.f_locals))
            entry={'line':frame.f_lineno,'kind':event,'vars':state,'stack':list(reversed(chain)),'types':{k:type(v).__name__ for k,v in list(_scope.items())+list(frame.f_locals.items()) if not k.startswith('_')},'output':_out.getvalue()}
            if event=='return':
                try: entry['returnValue']=_value(arg)
                except: pass
            size=len(json.dumps(entry,ensure_ascii=False));_bytes+=size
            if _bytes>12000000: raise RuntimeError('실행 기록이 12MB를 넘었어요. 입력을 줄여 주세요.')
            _events.append(entry)
    return _trace
_error=None
try:
    sys.settrace(_trace)
    exec(compile(_user_code,'<student>','exec'),_scope)
except BaseException as e:
    _error=type(e).__name__+': '+str(e)
finally:
    sys.settrace(None)
    builtins.input,sys.stdout=_old_input,_old_stdout
if _capture: _events.append({'kind':'end','line':None,'vars':_snapshot(_scope),'stack':[],'output':_out.getvalue()})
json.dumps({'events':_events,'output':_out.getvalue(),'error':_error,'steps':_count},ensure_ascii=False)
`);const parsed=JSON.parse(result);parsed.elapsedMs=Math.round(performance.now()-started);postMessage(parsed)}catch(e){postMessage({error:String(e),events:[],output:'',elapsedMs:Math.round(performance.now()-started)})}};
