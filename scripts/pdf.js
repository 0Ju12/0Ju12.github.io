// docs/resume.html → docs/resume.pdf, docs/resume-1page.html → docs/resume-1page.pdf  (사용: node scripts/pdf.js)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const root = path.resolve(__dirname, '..');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const name of ['resume', 'resume-1page', 'resume-en', 'resume-1page-en']) {
    await page.goto('file://' + path.join(root, 'docs', name + '.html'), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({ path: path.join(root, 'docs', name + '.pdf'), format: 'A4', printBackground: true, preferCSSPageSize: true });
    console.log(`✔ docs/${name}.pdf 생성 완료`);
  }
  await browser.close();
})();
