/* Bridge between the prep space and 네오's desk: only the opener on an allowed origin may read a summary,
   open a menu or drop inbox items, and inbox items are applied only by a click. Uses the synthetic fixture. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const fixture=process.env.INTERVIEW_FIXTURE||path.resolve(__dirname,'../work/interview-fixture');
const DESK='<!doctype html><meta charset="utf-8"><button id="go">open</button><script>let w,last=null;addEventListener("message",e=>{if(e.source===w&&e.origin==="https://0ju12.github.io"){if(e.data.type==="prep:ready")w.postMessage({type:"prep:hello"},e.origin);if(e.data.type==="prep:summary")last=e.data.summary}});document.getElementById("go").onclick=()=>{w=window.open("https://0ju12.github.io/study/index.html","prep")}</script>';
(async()=>{const browser=await chromium.launch({...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});let checks=0;
try{const ctx=await browser.newContext();
await ctx.route('**/*',r=>{const u=new URL(r.request().url());
  if(u.origin==='http://localhost:8501')return r.fulfill({contentType:'text/html',body:DESK});
  if(u.origin==='https://0ju12.github.io'&&u.pathname==='/study/index.html')return r.fulfill({contentType:'text/html',body:fs.readFileSync(path.join(fixture,'index.html'))});
  if(u.origin==='https://0ju12.github.io'&&u.pathname==='/study/version.json')return r.fulfill({contentType:'application/json',body:'{"version":"fixture-v1"}'});
  return r.abort()});
const desk=await ctx.newPage();await desk.goto('http://localhost:8501/');const [prep]=await Promise.all([desk.waitForEvent('popup'),desk.click('#go')]);const errors=[];prep.on('pageerror',e=>errors.push(e.message));
await desk.waitForFunction(()=>last&&last.interview);const s=await desk.evaluate(()=>last);assert.equal(s.interview.total,1);assert.equal(s.week.length,7);assert(s.menus.interview);checks++;
await desk.evaluate(()=>w.postMessage({type:'prep:open',route:'questions'},'https://0ju12.github.io'));await prep.waitForFunction(()=>location.hash==='#/questions');checks++;
await desk.evaluate(()=>w.postMessage({type:'prep:open',route:'javascript:alert(1)'},'https://0ju12.github.io'));await prep.waitForTimeout(200);assert.equal(await prep.evaluate(()=>location.hash),'#/questions');checks++;
await desk.evaluate(()=>w.postMessage({type:'prep:inbox',item:{kind:'answer',qid:'q1',title:'답변 다듬기',text:'네오가 다듬은 답변'}},'https://0ju12.github.io'));
await prep.waitForFunction(()=>/받은 자료 1/.test(document.querySelector('#haewon-inbox').textContent));
assert.notEqual(await prep.evaluate(()=>(JSON.parse(localStorage.getItem('interview-app-v1')||'{}').answers||{}).q1?.text),'네오가 다듬은 답변');checks++;
await prep.click('#haewon-inbox');await prep.click('[data-hw-apply]');await prep.waitForFunction(()=>JSON.parse(localStorage.getItem('interview-app-v1')).answers.q1.text==='네오가 다듬은 답변');checks++;
await prep.evaluate(()=>window.postMessage({type:'prep:inbox',item:{kind:'note',text:'spoof'}},'*'));await prep.waitForTimeout(200);
assert.equal(await prep.evaluate(()=>JSON.parse(localStorage.getItem('prep-haewon-inbox')).length),0);checks++;
assert.deepEqual(errors,[]);console.log('desk bridge checks',checks)}finally{await browser.close()}})().catch(e=>{console.error(e);process.exit(1)});
