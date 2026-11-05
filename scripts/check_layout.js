// 배포 전 화면 점검 — 휴대폰(390px)·데스크톱(1280px)에서 가로 스크롤(화면 넘침)이 생기는 페이지를 찾음
// 사용: node scripts/check_layout.js   (문제가 있으면 종료 코드 1)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const docs = path.resolve(__dirname, '..', 'docs');
const list = ['index.html', 'en.html', 'demo.html', 'demo-en.html', 'study/index.html']
  .concat(fs.readdirSync(path.join(docs, 'projects')).filter(f => f.endsWith('.html')).map(f => 'projects/' + f))
  .concat(fs.readdirSync(path.join(docs, 'posts')).filter(f => f.endsWith('.html')).map(f => 'posts/' + f));
(async () => {
  const b = await chromium.launch();
  const bad = [];
  for (const [label, vp] of [['휴대폰', { width: 390, height: 844 }], ['데스크톱', { width: 1280, height: 800 }]]) {
    const ctx = await b.newContext({ viewport: vp });
    const p = await ctx.newPage();
    for (const rel of list) {
      await p.goto('file://' + path.join(docs, rel), { waitUntil: 'load' });
      await p.waitForTimeout(150);
      const w = await p.evaluate(() => document.documentElement.scrollWidth);
      if (w > vp.width + 2) bad.push(`${label} ${rel}: 화면 폭 ${vp.width}px 인데 내용 폭 ${w}px`);
    }
    await ctx.close();
  }
  await b.close();
  bad.forEach(x => console.log('✗', x));
  console.log(`화면 점검 ${list.length}개 페이지 × 2 · 문제 ${bad.length}`);
  process.exit(bad.length ? 1 : 0);
})();
