/* 강의 노트 파이썬 실행기 (브라우저 안 Pyodide). 노트 한 편 = 워커 하나라서 앞 블록에서 만든 변수를 다음 블록이 이어 씀.
   네트워크는 Pyodide·패키지 내려받기에만 씀. 노트 암호 키(sessionStorage)는 워커에서 읽을 수 없음. */
importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');
let ready = (async () => {
  const py = await loadPyodide();
  py.runPython(`
import os, sys, io, builtins, base64
os.environ['MPLBACKEND'] = 'AGG'
_ns = {'__name__': '__main__'}
_real_open = builtins.open
class _Out(io.StringIO):
    def write(self, s):
        if self.tell() + len(s) > 200000: raise RuntimeError('출력이 200,000자를 넘어 멈췄습니다.')
        return super().write(s)
class _Err(io.StringIO): pass
def _stderr(): return sys.stderr.getvalue() if isinstance(sys.stderr, _Err) else ''
def _prepare(stdin_text):
    out = _Out()
    sys.stdout = out
    sys.stderr = _Err()
    sys.stdin = io.StringIO(stdin_text)
    lines = iter(stdin_text.splitlines())
    def _input(prompt=''):
        if prompt: out.write(str(prompt))
        try: return next(lines)
        except StopIteration: raise EOFError('입력값이 더 없습니다. 아래 입력 칸에 값을 넣어 주세요.')
    builtins.input = _input
    def _open(f, mode='r', *a, **k):   # SWEA 식 sys.stdin = open('input.txt') 를 입력 칸으로 대신함
        if isinstance(f, str) and os.path.basename(f).endswith('.txt') and 'r' in mode and not os.path.exists(f):
            return io.StringIO(stdin_text)
        return _real_open(f, mode, *a, **k)
    builtins.open = _open
    return out
def _figures():
    if 'matplotlib.pyplot' not in sys.modules: return []
    import matplotlib.pyplot as plt
    pngs = []
    for n in plt.get_fignums():
        buf = io.BytesIO(); plt.figure(n).savefig(buf, format='png', dpi=110, bbox_inches='tight')
        pngs.append(base64.b64encode(buf.getvalue()).decode())
    plt.close('all')
    return pngs
def _show_value(v):
    if v is None: return ''
    try:
        import pandas as pd
        if isinstance(v, (pd.DataFrame, pd.Series)): return v.to_string(max_rows=40, max_cols=20)
    except Exception: pass
    r = repr(v)
    return r if len(r) < 20000 else r[:20000] + ' …'
`);
  return py;
})();

const missing = (py, code) => {
  // Pyodide 기본 묶음에 없는 순수 파이썬 패키지(예: seaborn)는 micropip 으로 한 번 더 시도
  const mods = [...code.matchAll(/^\s*(?:from|import)\s+([A-Za-z_]\w*)/gm)].map(m => m[1]);
  return [...new Set(mods)].filter(m => { try { py.pyimport(m); return false } catch (_) { return true } });
};

onmessage = async ({ data }) => {
  const { id, code, input } = data;
  const t0 = performance.now();
  let py;
  try {
    postMessage({ id, status: 'loading' });
    py = await ready;
    await py.loadPackagesFromImports(code);
    const need = missing(py, code);
    if (need.length) {
      await py.loadPackage('micropip');
      const micropip = py.pyimport('micropip');
      for (const m of need) { try { await micropip.install(m) } catch (_) { /* 아래 실행에서 ModuleNotFoundError 로 알려 줌 */ } }
    }
    postMessage({ id, status: 'running' });
    const prep = py.globals.get('_prepare');
    const out = prep(input || ''); prep.destroy();
    let value = '', error = '';
    try {
      const v = await py.runPythonAsync(code, { globals: py.globals.get('_ns') });
      const show = py.globals.get('_show_value'); value = show(v); show.destroy();
      if (v && v.destroy) v.destroy();
    } catch (e) {
      // Pyodide 내부 줄은 빼고, 사용자 코드(<exec>)부터의 traceback 만 남김
      const se = py.globals.get('_stderr')();
      const lines = ((se && se.includes('Traceback') ? se : '') || String(e.message || e)).trim().split('\n');
      const k = lines.findIndex(l => l.includes('File "<exec>"'));
      error = (k >= 0 ? lines.slice(k) : lines.slice(-1)).join('\n').replace(/File "<exec>", line (\d+)(, in <module>)?/g, '$1번째 줄');
    }
    let text = out.getvalue(); out.destroy();
    if (!error) { const w = py.globals.get('_stderr')(); if (w) text += (text ? '\n' : '') + w; }   // 경고 문구는 출력 뒤에
    const figs = py.globals.get('_figures')().toJs();
    postMessage({ id, status: 'done', out: text, value, error, figs: [...figs], ms: Math.round(performance.now() - t0) });
  } catch (e) {
    postMessage({ id, status: 'done', out: '', value: '', error: '실행 환경을 준비하지 못했습니다: ' + (e.message || e), figs: [], ms: 0 });
  }
};
