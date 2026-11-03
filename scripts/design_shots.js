// 디자인 시안 미리보기 캡처: docs/design-<이름>.html → docs/assets/design/<이름>-{desk,mob}.jpg  (사용: node scripts/design_shots.js)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const root = path.resolve(__dirname, '..'), out = path.join(root, 'docs', 'assets', 'design');
  fs.mkdirSync(out, { recursive: true });
  const names = fs.readdirSync(path.join(root, 'docs')).filter(f => /^design-(?!picker).+\.html$/.test(f)).map(f => f.slice(7, -5));
  const b = await chromium.launch();
  for (const n of names) {
    for (const [tag, vp] of [['desk', { width: 1280, height: 860 }], ['mob', { width: 390, height: 780 }]]) {
      const p = await b.newPage({ viewport: vp, deviceScaleFactor: 1, colorScheme: n === 'pipeline' ? 'dark' : 'light' });
      await p.goto('file://' + path.join(root, 'docs', `design-${n}.html`), { waitUntil: 'networkidle' });
      await p.evaluate(() => document.fonts.ready);
      await p.screenshot({ path: path.join(out, `${n}-${tag}.jpg`), type: 'jpeg', quality: 78 });
      await p.close();
    }
    console.log('✔', n);
  }
  await b.close();
})();
