/* 강의 노트 코드 실행기 — 잠금을 푼 노트 안에서만 동작. 강의 내용은 담지 않은 빈 실행 틀이라 공개돼도 됨.
   - HTML·CSS·JavaScript·Vue: 출처가 없는(sandbox, allow-same-origin 없음) iframe 에서 실행 → 노트 암호 키에 접근 못 함
   - SQL: sql.js(SQLite)로 같은 노트의 앞 SQL 블록을 이어서 실행
   - Python: Pyodide 워커(노트마다 하나, 변수 이어 씀). numpy·pandas·matplotlib·scikit-learn 은 처음 실행 때 내려받음
   - Django·PyTorch·LangChain 등 서버·대형 모델이 필요한 코드는 '로컬 실습'으로 표시만 함 */
(function () {
  if (window.__noteRunner) return; window.__noteRunner = 1;
  var me = document.currentScript, base = me ? me.src.replace(/note-runner\.js.*$/, '') : '../lab/';
  var TRACK = (me && me.dataset.track) || '';
  var CDN = { vue: 'https://unpkg.com/vue@3.5.13/dist/vue.global.js', axios: 'https://cdn.jsdelivr.net/npm/axios@1.7.9/dist/axios.min.js' };
  var LOCAL_PY = /^\s*(?:from|import)\s+(django|rest_framework|drf_spectacular|torch|torchvision|transformers|lmdeploy|gradio|langchain\w*|moondream|peft|huggingface_hub|fastmcp|openai|httpx|requests|IPython|cv2|tensorflow|keras)\b|^\s*from\s+\.|models\.Model\b|\burlpatterns\b|\bdef \w+\(request\b|\brender\(request\b|\bclass Meta:|serializers\.\w+Serializer|\bpath\(['"]/m;
  var HEAVY_PY = /^\s*(?:from|import)\s+(torch|torchvision|transformers|lmdeploy|gradio|langchain\w*|moondream|peft|huggingface_hub|fastmcp|openai|tensorflow|keras)\b/m;
  var DJ_TPL = /\{%\s*\w+|\{\{\s*[\w.]+\s*(\|[^}]*)?\}\}(?![^<]*<\/script>)/;

  var css = '.nr{margin:-6px 0 22px;font:13px/1.5 system-ui,-apple-system,"Segoe UI","Noto Sans KR",sans-serif;color:var(--fg,#1d1f23)}' +
    '.nr-bar{display:flex;flex-wrap:wrap;align-items:center;gap:6px}' +
    '.nr-bar button,.nr-bar a{font:600 12.5px/1 system-ui,-apple-system,"Noto Sans KR",sans-serif;padding:7px 11px;border-radius:8px;border:1px solid var(--line,#d8dbe1);background:var(--card,#fff);color:var(--fg,#1d1f23);cursor:pointer;text-decoration:none}' +
    '.nr-bar button.nr-run{background:var(--accent,#3557d4);border-color:var(--accent,#3557d4);color:#fff}' +
    '.nr-bar button:disabled{opacity:.6;cursor:progress}.nr-bar button:focus-visible,.nr-bar a:focus-visible{outline:2px solid var(--accent,#3557d4);outline-offset:2px}' +
    '.nr-tag{font-size:12px;color:var(--muted,#5d6470)}.nr-local{display:inline-block;font-size:12px;color:var(--muted,#5d6470);border:1px dashed var(--line,#d8dbe1);border-radius:8px;padding:5px 9px}' +
    '.nr-edit{display:block;width:100%;box-sizing:border-box;min-height:120px;margin:0 0 8px;padding:12px 14px;border:2px solid var(--accent,#3557d4);border-radius:10px;font:13.5px/1.6 "JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;background:var(--code-bg,#f6f5f1);color:#1d1f23;tab-size:4;resize:vertical}' +
    '.nr-in{display:block;width:100%;box-sizing:border-box;min-height:56px;margin:8px 0 0;padding:8px 10px;border:1px solid var(--line,#d8dbe1);border-radius:8px;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;background:var(--card,#fff);color:var(--fg,#1d1f23)}' +
    '.nr-in-l{display:block;margin-top:8px;font-size:12px;color:var(--muted,#5d6470)}' +
    '.nr-out{margin-top:8px;border:1px solid var(--line,#d8dbe1);border-radius:10px;overflow:hidden;background:var(--card,#fff)}' +
    '.nr-out pre{margin:0;padding:10px 12px;white-space:pre-wrap;word-break:break-word;font:12.5px/1.55 ui-monospace,Menlo,Consolas,monospace;max-height:360px;overflow:auto;background:none;border:0}' +
    '.nr-out .nr-err{color:#b42318;background:rgba(180,35,24,.06)}.nr-out .nr-val{color:var(--muted,#5d6470)}' +
    '.nr-out .nr-meta{padding:6px 12px;font-size:11.5px;color:var(--muted,#5d6470);border-top:1px solid var(--line,#d8dbe1);display:flex;gap:8px;flex-wrap:wrap;align-items:center}' +
    '.nr-out iframe{display:block;width:100%;height:260px;border:0;background:#fff}.nr-out img{display:block;max-width:100%;background:#fff;margin:6px auto}' +
    '.nr-out table{border-collapse:collapse;font:12.5px ui-monospace,Menlo,Consolas,monospace;margin:8px 12px}.nr-out th,.nr-out td{border:1px solid var(--line,#d8dbe1);padding:3px 8px;text-align:left}.nr-out th{background:var(--th,#f1f2f5)}' +
    '.nr-hint{padding:8px 12px;font-size:12.5px;border-top:1px solid var(--line,#d8dbe1)}' +
    '@media (prefers-color-scheme:dark){.nr-out .nr-err{color:#ff8a80;background:rgba(255,138,128,.08)}.nr-edit{background:#1e2126;color:#e6e8ec}}' +
    '@media print{.nr{display:none}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] }) };
  var blocks = [];
  document.querySelectorAll('div.sourceCode > pre.sourceCode').forEach(function (pre) {
    var m = pre.className.match(/sourceCode\s+(\w+)/); if (!m) return;
    var code = (pre.querySelector('code') || pre).textContent;
    blocks.push({ pre: pre, wrap: pre.parentNode, lang: m[1], orig: code });
  });
  if (!blocks.length) return;

  function kind(b) {
    var c = b.orig;
    if (b.lang === 'python') {
      if (HEAVY_PY.test(c)) return { local: '딥러닝·LLM 코드 — 본인 PC 가상환경에서 실행 (로컬 실습)' };
      if (LOCAL_PY.test(c)) return { local: 'Django·서버 코드 — 본인 PC 가상환경에서 실행 (로컬 실습)' };
      if (/^\s*>>>/m.test(c) && /\.objects\.|\bModel\b|Article|User\b/.test(c) || /\.objects\.(all|filter|get|create|exclude|order_by)\(/.test(c)) return { local: 'Django 셸(ORM) 예시 — python manage.py shell 에서 실행 (로컬 실습)' };
      return { run: 'py', tag: 'Python · 브라우저에서 실행' };
    }
    if (b.lang === 'html') return DJ_TPL.test(c) ? { local: 'Django 템플릿 — 서버에서 그려지는 화면 (로컬 실습)' } : { run: 'web', tag: /createApp|Vue\./.test(c) ? 'Vue · 미리보기' : 'HTML · 미리보기' };
    if (b.lang === 'css') return { run: 'web', tag: 'CSS · 가까운 HTML 예시에 입혀 미리보기' };
    if (b.lang === 'javascript') return /\brequire\(|module\.exports/.test(c) ? { local: 'Node.js 코드 (로컬 실습)' } : { run: 'web', tag: 'JavaScript · 콘솔 + 미리보기' };
    if (b.lang === 'sql') return { run: 'sql', tag: 'SQL · SQLite로 실행 (이 노트의 앞 SQL을 이어서)' };
    return null;
  }

  function near(i, lang, dir) {   // 같은 노트에서 가장 가까운 다른 블록 (CSS → HTML 짝 찾기)
    for (var j = i + dir; j >= 0 && j < blocks.length; j += dir) if (blocks[j].lang === lang && blocks[j].k && blocks[j].k.run) return blocks[j];
    return null;
  }
  var code = function (b) { return b.ta && b.ta.style.display !== 'none' ? b.ta.value : b.orig };

  /* ---------- 웹 (HTML·CSS·JS·Vue) ---------- */
  var token = Math.random().toString(36).slice(2), frames = {};
  window.addEventListener('message', function (e) {
    var d = e.data; if (!d || d.t !== token || !frames[d.id]) return;
    var f = frames[d.id];
    if (d.kind === 'body') { f.iframe.style.display = d.has ? '' : 'none'; if (d.h) f.iframe.style.height = Math.min(Math.max(d.h + 16, 80), 520) + 'px'; return; }
    f.log.style.display = ''; f.log.insertAdjacentHTML('beforeend', '<div' + (d.kind === 'error' ? ' class="nr-err"' : '') + '>' + esc(d.text) + '</div>');
    if (d.kind === 'error' && /Failed to fetch|NetworkError|127\.0\.0\.1|localhost|ERR_CONNECTION/i.test(d.text) && !f.hinted) {
      f.hinted = 1; f.box.insertAdjacentHTML('beforeend', '<div class="nr-hint">💡 서버(예: Django 127.0.0.1:8000)에 요청하는 코드는 브라우저 미리보기에서 응답을 받을 수 없습니다. 2단계 로컬 실습에서 서버를 켜고 실행하세요.</div>');
    }
  });
  function shim(id) {
    return '<script>(function(){var T=' + JSON.stringify(token) + ',I=' + id + ';function s(k,a){var t=Array.prototype.map.call(a,function(x){if(typeof x==="string")return x;try{return JSON.stringify(x,null,1)}catch(_){return String(x)}}).join(" ");parent.postMessage({t:T,id:I,kind:k,text:t},"*")}' +
      '["log","info","warn","table","dir"].forEach(function(k){var o=console[k];console[k]=function(){s(k==="warn"?"warn":"log",arguments);o&&o.apply(console,arguments)}});var oe=console.error;console.error=function(){s("error",arguments);oe.apply(console,arguments)};' +
      'addEventListener("error",function(e){s("error",[e.message+(e.lineno?" ("+e.lineno+"번째 줄)":"")])});addEventListener("unhandledrejection",function(e){s("error",["Promise 오류: "+(e.reason&&e.reason.message||e.reason)])});' +
      'function b(){var d=document.body;parent.postMessage({t:T,id:I,kind:"body",has:!!(d&&(d.children.length>1||d.textContent.trim())),h:document.documentElement.scrollHeight},"*")}addEventListener("load",function(){b();setTimeout(b,400);setTimeout(b,1500)});new MutationObserver(b).observe(document.documentElement,{childList:true,subtree:true})})()<\/script>';
  }
  function webDoc(b, i, id) {
    var c = code(b), libs = '';
    if (b.lang === 'html') {
      var doc = /<html[\s>]/i.test(c) ? c : '<!doctype html><html><head><meta charset="utf-8"></head><body>' + c + '</body></html>';
      return doc.replace(/<head([^>]*)>/i, '<head$1>' + shim(id) + '<base target="_blank">');
    }
    if (b.lang === 'css') {
      var h = near(i, 'html', -1) || near(i, 'html', 1);
      var markup = h ? code(h) : '<h1>제목</h1><p>문단 <a href="#">링크</a></p><div class="box">상자</div><button>버튼</button>';
      if (!/<html[\s>]/i.test(markup)) markup = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + markup + '</body></html>';
      return markup.replace(/<head([^>]*)>/i, '<head$1>' + shim(id)).replace(/<\/head>/i, '<style>' + c.replace(/<\/style/gi, '<\\/style') + '</style></head>');
    }
    // JavaScript: 화면 요소를 찾는 코드면 가장 가까운 HTML 예시를 화면으로 씀
    var dom = /document\.|querySelector|getElementById|addEventListener/.test(c), page = '';
    if (dom) { var hh = near(i, 'html', -1) || near(i, 'html', 1); if (hh) page = code(hh).replace(/<script[\s\S]*?<\/script>/gi, ''); }
    if (/\baxios\b/.test(c)) libs += '<script src="' + CDN.axios + '"><\/script>';
    if (/\bVue\b|createApp/.test(c)) libs += '<script src="' + CDN.vue + '"><\/script>';
    var body = /<body[\s>]/i.test(page) ? page.replace(/^[\s\S]*<body[^>]*>|<\/body>[\s\S]*$/gi, '') : page;
    return '<!doctype html><html><head><meta charset="utf-8">' + shim(id) + libs + '</head><body>' + body + '<script>' + c.replace(/<\/script/gi, '<\\/script') + '\n<\/script></body></html>';
  }

  /* ---------- 파이썬 (Pyodide 워커) ---------- */
  var worker = null, wseq = 0, waits = {};
  function getWorker() {
    if (worker) return worker;
    worker = new Worker(base + 'note-py-worker.js');
    worker.onmessage = function (e) { var w = waits[e.data.id]; if (w) w(e.data) };
    return worker;
  }
  function runPy(src, input, onStatus) {
    return new Promise(function (res) {
      var id = ++wseq, w = getWorker(), timer = null;
      waits[id] = function (d) {
        if (d.status !== 'done') { onStatus(d.status); if (d.status === 'running') timer = setTimeout(function () { onStatus('long') }, 8000); return }
        clearTimeout(timer); delete waits[id]; res(d);
      };
      w.postMessage({ id: id, code: src, input: input });
    });
  }
  function stopPy() { if (worker) { worker.terminate(); worker = null; Object.keys(waits).forEach(function (k) { waits[k]({ status: 'done', out: '', value: '', error: '중지했습니다. 파이썬 환경을 새로 시작합니다(앞에서 만든 변수도 지워짐).', figs: [], ms: 0 }) }) } }

  /* ---------- SQL (sql.js) ---------- */
  var sqlReady = null;
  function getSql() {
    if (sqlReady) return sqlReady;
    sqlReady = new Promise(function (res, rej) {
      var s = document.createElement('script'); s.src = base + 'sql-wasm.js';
      s.onload = function () { initSqlJs({ locateFile: function (f) { return base + f } }).then(res, rej) }; s.onerror = rej; document.head.appendChild(s);
    });
    return sqlReady;
  }
  function table(r) {
    return '<table><thead><tr>' + r.columns.map(function (c) { return '<th>' + esc(c) + '</th>' }).join('') + '</tr></thead><tbody>' +
      r.values.slice(0, 200).map(function (row) { return '<tr>' + row.map(function (v) { return '<td>' + (v === null ? '<i>NULL</i>' : esc(v)) + '</td>' }).join('') + '</tr>' }).join('') + '</tbody></table>' +
      (r.values.length > 200 ? '<div class="nr-hint">앞 200행만 표시 (전체 ' + r.values.length + '행)</div>' : '');
  }

  /* ---------- 화면 ---------- */
  blocks.forEach(function (b, i) {
    b.k = kind(b); if (!b.k) return;
    var box = document.createElement('div'); box.className = 'nr'; b.box = box;
    if (b.k.local) { box.innerHTML = '<span class="nr-local">💻 ' + esc(b.k.local) + '</span>'; b.wrap.after(box); return; }
    var needIn = b.k.run === 'py' && /\binput\(|sys\.stdin|open\(['"][^'"]*\.txt/.test(b.orig);
    box.innerHTML = '<div class="nr-bar"><button type="button" class="nr-run">▶ 실행</button><button type="button" class="nr-ed">✎ 고치기</button>' +
      '<span class="nr-tag">' + esc(b.k.tag) + '</span></div>' +
      (b.k.run === 'py' ? '<label class="nr-in-l"' + (needIn ? '' : ' hidden') + '>입력값 (한 줄에 하나, input()·sys.stdin·input.txt 대신 읽음)<textarea class="nr-in" spellcheck="false"></textarea></label>' : '') +
      '<div class="nr-res"></div>';
    b.wrap.after(box);
    var run = box.querySelector('.nr-run'), ed = box.querySelector('.nr-ed'), res = box.querySelector('.nr-res');
    var bridge = b.wrap.querySelector('.st-lab-code');   // 알고리즘 노트의 '알고리즘 기록에서 실행하기' 버튼을 같은 줄로
    if (bridge) { bridge.removeAttribute('style'); bridge.textContent = '알고리즘 기록에 저장 ↗'; box.querySelector('.nr-bar').insertBefore(bridge, box.querySelector('.nr-tag')) }
    ed.onclick = function () {
      if (!b.ta) {
        b.ta = document.createElement('textarea'); b.ta.className = 'nr-edit'; b.ta.spellcheck = false; b.ta.value = b.orig;
        b.ta.style.height = Math.min(Math.max(b.orig.split('\n').length * 21.6 + 30, 120), 560) + 'px';
        b.ta.addEventListener('keydown', function (e) {
          if (e.key === 'Tab') { e.preventDefault(); var s = b.ta.selectionStart; b.ta.setRangeText('    ', s, b.ta.selectionEnd, 'end') }
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); run.click() }
        });
        b.wrap.after(b.ta);
      }
      var editing = b.ta.style.display !== 'none' && b.pre.style.display === 'none';
      if (editing) { b.ta.style.display = 'none'; b.pre.style.display = ''; ed.textContent = '✎ 고치기' }
      else { b.ta.style.display = ''; b.pre.style.display = 'none'; ed.textContent = '↺ 원래 코드 보기'; b.ta.focus() }
    };
    run.onclick = function () { go(b, i, false) };
    b.run = run; b.res = res;
  });

  function go(b, i, chain) {
    var run = b.run, res = b.res; run.disabled = true;
    if (b.k.run === 'web') {
      var id = ++wseq;
      res.innerHTML = '<div class="nr-out"><iframe sandbox="allow-scripts allow-modals allow-forms allow-popups" title="실행 결과 미리보기"></iframe><pre class="nr-log" style="display:none"></pre>' +
        '<div class="nr-meta">미리보기는 노트와 분리된 칸에서 실행됩니다 · <a href="#" class="nr-close">닫기</a></div></div>';
      var f = { iframe: res.querySelector('iframe'), log: res.querySelector('.nr-log'), box: res.querySelector('.nr-out') };
      frames[id] = f; f.iframe.srcdoc = webDoc(b, i, id);
      res.querySelector('.nr-close').onclick = function (e) { e.preventDefault(); res.innerHTML = '' };
      run.disabled = false; run.textContent = '▶ 다시 실행'; return;
    }
    if (b.k.run === 'sql') {
      res.innerHTML = '<div class="nr-out"><pre>SQLite 준비 중…</pre></div>';
      getSql().then(function (SQL) {
        var db = new SQL.Database(), skipped = 0, html = '';
        for (var j = 0; j < i; j++) if (blocks[j].lang === 'sql') { try { db.exec(code(blocks[j])) } catch (_) { skipped++ } }
        try {
          var out = db.exec(code(b));
          html = out.length ? out.map(table).join('') : '<pre class="nr-val">실행 완료 (돌려준 행 없음' + (db.getRowsModified() ? ' · 바뀐 행 ' + db.getRowsModified() + '개' : '') + ')</pre>';
        } catch (e) {
          html = '<pre class="nr-err">' + esc(e.message) + '</pre>' + (/no such table/i.test(e.message) ? '<div class="nr-hint">💡 이 노트 앞부분에 표를 만드는 SQL(CREATE TABLE·INSERT)이 없거나, 강의에서 따로 준 DB 파일을 쓰는 예시입니다. ✎ 고치기로 CREATE TABLE·INSERT를 위에 적어 실행해 보세요.</div>' : '');
        }
        res.innerHTML = '<div class="nr-out">' + html + '<div class="nr-meta">새 SQLite 메모리 DB에 이 노트의 앞 SQL 블록을 차례로 실행한 뒤 이 블록을 실행' + (skipped ? ' · 앞 블록 중 ' + skipped + '개는 오류로 건너뜀' : '') + '</div></div>';
        db.close(); run.disabled = false; run.textContent = '▶ 다시 실행';
      }, function () { res.innerHTML = '<div class="nr-out"><pre class="nr-err">SQLite를 불러오지 못했습니다.</pre></div>'; run.disabled = false });
      return;
    }
    // python
    var inp = b.box.querySelector('.nr-in');
    res.innerHTML = '<div class="nr-out"><pre class="nr-val">' + (getWorker() && wseq === 0 ? '' : '') + '파이썬 준비 중… (처음 한 번은 10~20초, 이후 바로 실행)</pre></div>';
    return runPy(code(b), inp ? inp.value : '', function (s) {
      var p = res.querySelector('pre');
      if (s === 'running' && p) p.textContent = '실행 중…';
      if (s === 'long') res.querySelector('.nr-out').insertAdjacentHTML('beforeend', '<div class="nr-hint">오래 걸립니다. 무한 반복이면 <button type="button" class="nr-stop">■ 중지</button></div>'), res.querySelector('.nr-stop').onclick = stopPy;
    }).then(function (d) {
      var h = '';
      if (d.out) h += '<pre>' + esc(d.out) + '</pre>';
      if (d.value) h += '<pre class="nr-val">' + esc(d.value) + '</pre>';
      (d.figs || []).forEach(function (png) { h += '<img alt="그래프" src="data:image/png;base64,' + png + '">' });
      if (d.error) {
        h += '<pre class="nr-err">' + esc(d.error) + '</pre>';
        if (/NameError|is not defined/.test(d.error) && !chain && blocks.slice(0, i).some(function (x) { return x.k && x.k.run === 'py' })) h += '<div class="nr-hint">💡 앞 블록에서 만든 변수·함수를 쓰는 코드일 수 있습니다. <button type="button" class="nr-chain">앞 파이썬 블록부터 차례로 실행</button></div>';
        if (/ModuleNotFoundError/.test(d.error)) h += '<div class="nr-hint">💡 브라우저 파이썬에 없는 라이브러리입니다. 2단계 로컬 실습(본인 PC 가상환경)에서 실행하세요.</div>';
        if (/EOFError/.test(d.error)) { var l = b.box.querySelector('.nr-in-l'); if (l) l.hidden = false }
      }
      if (!h) h = '<pre class="nr-val">실행 완료 (출력 없음)</pre>';
      res.innerHTML = '<div class="nr-out">' + h + '<div class="nr-meta">' + (d.ms ? d.ms.toLocaleString() + 'ms · ' : '') + '이 노트의 파이썬 블록끼리 변수를 이어 씀</div></div>';
      var c = res.querySelector('.nr-chain');
      if (c) c.onclick = function () {
        c.disabled = true; c.textContent = '앞 블록 실행 중…';
        var list = blocks.slice(0, i).filter(function (x) { return x.k && x.k.run === 'py' && !/\binput\(|sys\.stdin/.test(x.orig) });
        list.reduce(function (p, x) { return p.then(function () { return runPy(code(x), '', function () {}) }) }, Promise.resolve()).then(function () { go(b, i, true) });
      };
      run.disabled = false; run.textContent = '▶ 다시 실행';
    });
  }
})();
