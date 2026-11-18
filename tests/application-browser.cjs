const assert=require('node:assert/strict');
module.exports=async function(page){
 await page.evaluate(()=>location.hash='#/career');
 await page.locator('#career-company').fill('테스트 데이터 기업');await page.locator('#career-role').fill('데이터 엔지니어');await page.locator('#career-new button').click();
 await page.locator('#career-due').fill('2026-12-10');await page.locator('#career-url').fill('https://example.com/job');await page.locator('#career-text').fill('필수: SQL 최적화\n우대: 데이터 품질');await page.locator('#career-post button').click();
 await page.locator('#experience-title').fill('중복 데이터 검증');await page.locator('#experience-role').fill('검증 파이프라인 구현');await page.locator('#experience-result').fill('<script>alert(1)</script> 테스트 결과');await page.locator('#experience-url').fill('https://example.com/proof');await page.locator('#career-experience button:not([type=button])').click();
 await page.locator('#career-requirement').fill('SQL 최적화');await page.locator('#career-req button').click();
 await page.locator('[name=status]').selectOption('proof');await page.locator('[data-req] button:not([type=button])').click();assert((await page.locator('#toast').innerText()).includes('증빙 URL'));
 const ex=await page.evaluate(()=>JSON.parse(localStorage.getItem('interview-app-v1')).experiences[0].id);await page.locator('[name=experience]').selectOption(ex);await page.locator('[name=task]').fill('실행 계획과 성능 측정 결과 정리');await page.locator('[data-req] button:not([type=button])').click();
 await page.reload();await page.waitForSelector('[data-req]');assert.equal(await page.locator('[name=status]').inputValue(),'proof');assert.equal(await page.locator('#career-text').inputValue(),'필수: SQL 최적화\n우대: 데이터 품질');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 let download=page.waitForEvent('download');await page.locator('#career-export').click();assert((await download).suggestedFilename().endsWith('.md'));
 download=page.waitForEvent('download');await page.locator('#career-calendar').click();assert((await download).suggestedFilename().endsWith('.ics'));
 await page.evaluate(()=>location.hash='#/');await page.waitForSelector('text=다가오는 지원 · 다음 행동');assert((await page.locator('#app').innerText()).includes('실행 계획과 성능 측정 결과 정리'));
 await page.evaluate(()=>location.hash='#/career');await page.waitForSelector('[data-delete]');page.once('dialog',d=>d.accept());await page.locator('[data-delete]').click();assert.equal(await page.locator('[name=status]').inputValue(),'draft');
 const state=await page.evaluate(()=>JSON.parse(localStorage.getItem('interview-app-v1')));assert.equal(state.experiences.length,0);assert(state.deleted.experiences[ex]);
 await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(150);
 await page.screenshot({path:require('path').resolve(__dirname,'../work/interview-fixture/career-'+page.viewportSize().width+'.png'),fullPage:true});return 12;
};
