// 링크 미리보기 이미지·아이콘 생성 (1200×630)
//   docs/og.png, docs/og-en.png                — 메인 페이지
//   docs/og/<id>.png, docs/og/<id>-en.png      — 프로젝트 상세 페이지 (재료: out/og_projects*.json, build.py 가 생성)
//   docs/apple-touch-icon.png (180×180)
// 사용: python3 scripts/build.py && node scripts/og.js   — 내용 바꾸면 다시 실행
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const b64 = (rel) => {
  const f = path.join(root, 'docs', rel);
  if (!rel || !fs.existsSync(f)) return '';
  return `data:image/${rel.endsWith('.png') ? 'png' : 'jpeg'};base64,` + fs.readFileSync(f).toString('base64');
};
const esc = (s) => String(s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const photo = b64('assets/photos/profile.jpg');
const FONT = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">';
const BASE = `*{box-sizing:border-box}body{margin:0;width:1200px;height:630px;font-family:"Pretendard Variable",Pretendard,sans-serif;background:#f6f7f9;color:#18181b;overflow:hidden;position:relative;word-break:keep-all}
.foot{position:absolute;left:72px;right:72px;bottom:48px;display:flex;align-items:center;gap:14px;font-size:22px;color:#5f5f68}
.foot img{width:48px;height:48px;border-radius:14px;object-fit:cover}.foot b{color:#18181b;font-weight:800}.foot span:last-child{margin-left:auto}`;

const home = (t) => `<!doctype html><html><head><meta charset="utf-8">${FONT}<style>${BASE}
.c{position:absolute;left:72px;right:72px;top:70px}
.r{font-size:24px;font-weight:700;color:#5f5f68}
h1{font-size:76px;line-height:1.08;letter-spacing:-.05em;margin:22px 0 0;font-weight:800}
.bar{position:absolute;right:72px;top:70px;width:6px;height:250px;background:#1f3a5f;border-radius:3px}</style></head>
<body><div class="c"><div class="r">${t.role}</div><h1>${t.h1}</h1></div>
<div class="foot"><img src="${photo}"><b>${t.name}</b><span>${t.tag}</span><span>0ju12.github.io</span></div></body></html>`;

const proj = (m, en) => {
  const img = b64(m.image);
  return `<!doctype html><html><head><meta charset="utf-8">${FONT}<style>${BASE}
.c{position:absolute;left:72px;top:64px;width:${img ? 560 : 1056}px}
.g{font-size:21px;font-weight:700;color:#1f3a5f}
h1{font-size:${img ? 44 : 56}px;line-height:1.22;letter-spacing:-.035em;margin:16px 0 18px;font-weight:800}
.t{font-size:24px;line-height:1.5;color:#3f444c;margin:0 0 22px}
.k{display:inline-block;font-size:22px;font-weight:700;padding:10px 18px;border-radius:14px;background:#e8edf5;color:#1f3a5f;line-height:1.4}
.im{position:absolute;right:56px;top:64px;width:500px;height:400px;border-radius:24px;background:#fff;border:1px solid #e4e6ea;display:grid;place-items:center;overflow:hidden}
.im img{max-width:100%;max-height:100%;object-fit:contain}</style></head>
<body><div class="c"><div class="g">${esc(m.group)} · ${esc(m.period)}</div><h1>${esc(m.tagline || m.title)}</h1>${m.key ? `<div class="k">${esc(m.key)}</div>` : ''}</div>
${img ? `<div class="im"><img src="${img}"></div>` : ''}
<div class="foot"><img src="${photo}"><b>${en ? 'Young-Ju Lee' : '이영주'}</b><span>${en ? 'Data & AI Engineer' : '데이터·AI 엔지니어'}</span><span>0ju12.github.io</span></div></body></html>`;
};

const KO = { role: '데이터·AI 엔지니어', name: '이영주', tag: '지구물리 연구 · LLM 데이터 파이프라인', h1: '데이터를 모으고,<br>모델로 검증하고,<br>결과로 증명합니다.' };
const EN = { role: 'Data & AI Engineer', name: 'Young-Ju Lee', tag: 'Geophysics research · LLM data pipelines', h1: 'Collect the data,<br>verify with models,<br>prove it with results.' };

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  const shot = async (html, out) => {
    await p.setContent(html, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(root, 'docs', out) });
    console.log('✔ docs/' + out);
  };
  await shot(home(KO), 'og.png');
  await shot(home(EN), 'og-en.png');
  fs.mkdirSync(path.join(root, 'docs', 'og'), { recursive: true });
  for (const [file, en] of [['og_projects.json', false], ['og_projects-en.json', true]]) {
    const f = path.join(root, 'out', file);
    if (!fs.existsSync(f)) { console.log('… ' + file + ' 없음 — build.py 먼저 실행'); continue; }
    for (const m of JSON.parse(fs.readFileSync(f, 'utf8'))) await shot(proj(m, en), `og/${m.id}.png`);
  }
  const i = await b.newPage({ viewport: { width: 180, height: 180 } });
  await i.setContent(`<body style="margin:0;background:#18181b">${fs.readFileSync(path.join(root, 'docs/favicon.svg'), 'utf8').replace('<svg ', '<svg width="180" height="180" ')}</body>`, { waitUntil: 'networkidle' });
  await i.screenshot({ path: path.join(root, 'docs', 'apple-touch-icon.png') });
  console.log('✔ docs/apple-touch-icon.png');
  await b.close();
})();
