// 링크 미리보기 이미지·아이콘 생성: docs/og.png, docs/og-en.png (1200×630), docs/apple-touch-icon.png (180×180)
// 사용: node scripts/og.js   — 내용 바꾸면 다시 실행
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const photo = 'data:image/jpeg;base64,' + fs.readFileSync(path.join(root, 'docs/assets/photos/profile.jpg')).toString('base64');
const page = (t) => `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>*{box-sizing:border-box}body{margin:0;width:1200px;height:630px;font-family:"Pretendard Variable",Pretendard,sans-serif;background:#f7f7f8;color:#18181b;overflow:hidden;position:relative}
.b{position:absolute;border-radius:50%;filter:blur(70px)}.b1{width:520px;height:520px;background:#e3e7ff;left:-140px;top:-120px}.b2{width:520px;height:520px;background:#ffe9d6;right:-120px;top:60px}.b3{width:460px;height:460px;background:#dcf5e8;left:360px;bottom:-280px}
.c{position:absolute;inset:56px 64px;display:grid;grid-template-columns:1fr 250px;gap:48px;align-items:center}
.k{display:inline-flex;align-items:center;gap:10px;font-size:22px;font-weight:700;color:#5f5f68;background:#fff;border:1px solid #e4e4e8;border-radius:999px;padding:6px 18px 6px 14px}
.k i{width:11px;height:11px;border-radius:50%;background:#22c55e}
h1{font-size:68px;line-height:1.08;letter-spacing:-.05em;margin:22px 0 18px;font-weight:800}
h1 em{font-style:normal;background:linear-gradient(90deg,#5b6cff,#db2777 55%,#ea7a0c);-webkit-background-clip:text;background-clip:text;color:transparent}
.a{display:flex;flex-wrap:wrap;gap:10px}.a span{font-size:20px;font-weight:600;background:#fff;border:1px solid #e4e4e8;border-radius:999px;padding:6px 16px}
img{width:250px;height:250px;border-radius:56px;object-fit:cover;border:8px solid #fff;box-shadow:0 20px 50px -16px rgba(0,0,0,.25)}
.n{text-align:center;margin-top:18px;font-size:28px;font-weight:800;letter-spacing:-.03em}.u{text-align:center;color:#5f5f68;font-size:19px;margin-top:2px}</style></head>
<body><i class="b b1"></i><i class="b b2"></i><i class="b b3"></i><div class="c"><div><span class="k"><i></i>${t.role}</span><h1>${t.h1}</h1><div class="a">${t.areas.map(a => `<span>${a}</span>`).join('')}</div></div>
<div><img src="${photo}"><div class="n">${t.name}</div><div class="u">0ju12.github.io</div></div></div></body></html>`;
const KO = { role: '데이터·AI 엔지니어', name: '이영주', h1: '데이터를 모으고,<br>모델로 검증하고,<br><em>결과로 증명합니다.</em>', areas: ['지구물리 데이터 연구', '국제 공동연구', 'LLM · RAG', '딥러닝'] };
const EN = { role: 'Data & AI Engineer', name: 'Young-Ju Lee', h1: 'Collect the data,<br>verify with models,<br><em>prove it with results.</em>', areas: ['Geophysical data research', 'International collaboration', 'LLM · RAG', 'Deep learning'] };
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [name, t] of [['og.png', KO], ['og-en.png', EN]]) {
    await p.setContent(page(t), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(root, 'docs', name) });
    console.log('✔ docs/' + name);
  }
  const i = await b.newPage({ viewport: { width: 180, height: 180 } });
  await i.setContent(`<body style="margin:0;background:#18181b">${fs.readFileSync(path.join(root, 'docs/favicon.svg'), 'utf8').replace('<svg ', '<svg width="180" height="180" ')}</body>`, { waitUntil: 'networkidle' });
  await i.screenshot({ path: path.join(root, 'docs', 'apple-touch-icon.png') });
  console.log('✔ docs/apple-touch-icon.png');
  await b.close();
})();
