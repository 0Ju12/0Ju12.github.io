// 개인 비서 업무실 바로가기(docs/desk) 브라우저 점검: 비공개 포트 응답을 가짜로 대신해
// 준비됨 → 자동 이동, 응답 없음 → 안내 버튼, 주소 설정 검증을 휴대폰·데스크톱에서 확인
const {chromium}=require('playwright');const assert=require('assert');const http=require('http');const fs=require('fs');const path=require('path');
const root=path.resolve(__dirname,'..','docs');const shots=process.env.DESK_SHOTS;
const APP='https://humble-tribble-x544gwrrjgrg2vq75-8501.app.github.dev/';
const PIXEL='<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>';
async function shot(page,vp,file){const h=await page.evaluate(()=>document.documentElement.scrollHeight);await page.setViewportSize({width:vp.width,height:h});await page.screenshot({path:file});await page.setViewportSize(vp)}
(async()=>{const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://x').pathname));if(!file.startsWith(root)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.statusCode=404;return res.end()}res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(file))}).listen(0,'127.0.0.1');
await new Promise(r=>server.on('listening',r));const base='http://127.0.0.1:'+server.address().port;const browser=await chromium.launch();
try{for(const [tag,vp] of [['mobile',{width:390,height:844}],['desktop',{width:1280,height:900}]]){
 // 1) Private port not reachable: guidance and buttons stay on the page.
 let ctx=await browser.newContext({viewport:vp,deviceScaleFactor:shots?2:1});let page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://**/*',r=>r.abort());
 await page.goto(base+'/desk/index.html');
 assert.equal(await page.getAttribute('meta[name=robots]','content'),'noindex,nofollow');
 assert.equal(await page.getAttribute('#open','href'),APP);
 await page.waitForFunction(()=>document.querySelector('#state').textContent.includes('대기'));
 assert(await page.evaluate(()=>document.documentElement.scrollWidth)<=vp.width+2);
 if(shots)await shot(page,vp,`${shots}/launcher-${tag}.png`);
 // 2) Address settings: reject a foreign host, accept and store a new Codespace.
 await page.locator('#settings summary').click();
 await page.fill('#address','https://evil.example.com/');await page.click('#address-form .btn');
 assert((await page.textContent('#note')).includes('github.dev'));
 await page.fill('#address','https://other-space-abc.github.dev/');await page.click('#address-form .btn');
 assert.equal(await page.getAttribute('#open','href'),'https://other-space-abc-8501.app.github.dev/');
 assert.equal(await page.evaluate(()=>localStorage.getItem('personal-assistant.port8501')),'https://other-space-abc-8501.app.github.dev/');
 // 3) A #connect link only pre-fills the form; nothing is saved without a click.
 await page.goto(base+'/desk/index.html#connect=https://new-space-xyz-8501.app.github.dev');
 assert(await page.evaluate(()=>document.querySelector('#settings').open));
 assert.equal(await page.evaluate(()=>localStorage.getItem('personal-assistant.port8501')),'https://other-space-abc-8501.app.github.dev/');
 assert.deepEqual(errors,[]);await ctx.close();
 // 4) Private port ready: the launcher moves straight to the desk.
 ctx=await browser.newContext({viewport:vp});page=await ctx.newPage();
 await page.route('https://**/*',r=>{const u=r.request().url();if(u.startsWith(APP+'ready.svg'))return r.fulfill({contentType:'image/svg+xml',body:PIXEL});if(u===APP)return r.fulfill({contentType:'text/html; charset=utf-8',body:'<title>desk</title>업무실'});return r.abort()});
 await page.goto(base+'/desk/index.html');
 await page.waitForURL(APP);
 await ctx.close()}
 console.log('Desk launcher: probe, redirect, address settings passed on mobile and desktop')}finally{await browser.close();server.close()}})().catch(e=>{console.error(e);process.exitCode=1});
