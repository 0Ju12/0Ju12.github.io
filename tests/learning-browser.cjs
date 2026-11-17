const assert=require('node:assert/strict');
module.exports=async function(page){
 await page.locator('#algo-bulk-panel details').evaluate(e=>e.open=true);
 await page.locator('#learn-files').setInputFiles([{name:'2001_input.txt',mimeType:'text/plain',buffer:Buffer.from('bulk input')},{name:'sample_output.txt',mimeType:'text/plain',buffer:Buffer.from('42')}]);
 await page.waitForSelector('#learn-apply');assert.equal(await page.locator('#learn-number-0').inputValue(),'2001');assert.equal(await page.locator('#learn-number-1').inputValue(),'');await page.locator('#learn-number-1').fill('2001');await page.locator('#learn-overwrite').check();await page.locator('#learn-apply').click();await page.waitForFunction(()=>JSON.parse(localStorage.getItem('interview-app-v1')).algoDrafts['swea-2001'].input==='bulk input');
 await page.locator('#sw-query').fill('2001');await page.locator('[data-sw-open="2001"]').click();const f=page.frameLocator('#sw-frame');await f.locator('#input').waitFor();assert.equal(await f.locator('#input').inputValue(),'bulk input');assert.equal(await page.locator('#sw-expected').inputValue(),'42');
 await page.locator('#learn-compare-run').evaluate(e=>e.closest('details').open=true);await page.locator('#learn-pair').click();await page.locator('#learn-compare-run').click();await page.waitForFunction(()=>document.querySelector('#learn-compare-status').textContent.includes('출력이 같습니다'));assert((await page.locator('#learn-trace-a').innerText()).includes('4단계'));
 const before=await f.locator('#code').inputValue();assert(!before.includes('solutions = 0'));
 await page.locator('#learn-export').evaluate(e=>e.closest('details').open=true);const download=page.waitForEvent('download');await page.locator('#learn-export').click();assert((await download).suggestedFilename().endsWith('.md'));
 assert((await page.locator('#learn-save-state').textContent()).includes('GitHub:'));
 assert(await page.evaluate(()=>document.documentElement.scrollWidth)<=page.viewportSize().width+2);
 return 6;
};
