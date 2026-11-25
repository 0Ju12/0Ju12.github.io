// 개인 비서 업무실(docs/desk) 브라우저 점검: 비공개 실행 환경을 가짜 응답으로 대신해 연결·접수·결과·수정 요청 흐름을 휴대폰·데스크톱에서 확인
const {chromium}=require('playwright');const assert=require('assert');const http=require('http');const fs=require('fs');const path=require('path');
const root=path.resolve(__dirname,'..','docs');const shots=process.env.DESK_SHOTS;
const PRIVATE='https://humble-tribble-x544gwrrjgrg2vq75-8501.app.github.dev';
// Fake private workspace: answers the postMessage bridge with an in-memory job list.
const fake=`<script>
const jobs=[{id:2,root:1,number:2,status:'완료',task:'첫 문단을 더 간결하게',mode:'pair',codex_model:'',claude_model:'',created:'2026-11-25 01:10:00'},
{id:1,root:1,number:1,status:'완료',task:'자기소개서 데이터 엔지니어 지원 동기 문단을 다듬어 주세요',mode:'pair',codex_model:'',claude_model:'',created:'2026-11-25 01:00:00'},
{id:3,root:3,number:1,status:'Claude 검토 중',task:'SQL 면접 예상 질문 정리',mode:'claude',codex_model:'',claude_model:'opus',created:'2026-11-25T02:00:00Z'}];
const work={history:[['Codex 초안','초안 본문'],['Claude 검토','- 근거 수치 보강'],['최종 결과','## 수정안\\n지원 동기를 **데이터 품질** 경험 중심으로 정리했습니다.\\n1. 첫 문장\\n2. 근거\\n\`\`\`sql\\nselect 1;\\n\`\`\`']],events:[{status:'Codex 초안 작성',stamp:'2026-11-25 01:00:30'},{status:'Claude 검토',stamp:'2026-11-25 01:02:00'},{status:'완료',stamp:'2026-11-25 01:03:00'}],diff:'+ 추가된 줄\\n- 삭제된 줄',file_diff:null,attachments:[{name:'cover.docx',number:1}],parent:1};
let next=10;window.posted=[];
addEventListener('message',e=>{if(e.data?.desk!=='request')return;let value,ok=true;
 if(e.data.path==='/api/jobs'&&e.data.method==='POST'){const b=JSON.parse(e.data.body);posted.push(b);const j={id:next++,root:b.parent?1:next,number:b.parent?3:1,status:'접수',task:b.task,mode:b.mode,created:'2026-11-25 03:00:00'};jobs.unshift(j);value=j}
 else if(e.data.path==='/api/jobs')value=jobs;else value=work;
 e.source.postMessage({desk:'result',id:e.data.id,ok,value},'*')});
parent.postMessage({desk:'hello'},'*');
</script>`;
// Grow the viewport to the page height so the sticky rail is captured at full length.
async function shot(page,vp,file){const h=await page.evaluate(()=>document.documentElement.scrollHeight);await page.setViewportSize({width:vp.width,height:h});await page.screenshot({path:file});await page.setViewportSize(vp)}
(async()=>{const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://x').pathname));if(!file.startsWith(root)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.statusCode=404;return res.end()}res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync(file))}).listen(0,'127.0.0.1');
await new Promise(r=>server.on('listening',r));const base='http://127.0.0.1:'+server.address().port;const browser=await chromium.launch();
try{for(const [tag,vp] of [['mobile',{width:390,height:844}],['desktop',{width:1280,height:900}]]){
 const ctx=await browser.newContext({viewport:vp,deviceScaleFactor:shots?2:1});const page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://**/*',r=>r.request().url().startsWith(PRIVATE+'/portfolio-link')?r.fulfill({contentType:'text/html; charset=utf-8',body:fake}):r.abort());
 await page.goto(base+'/desk/index.html');
 assert.equal(await page.getAttribute('meta[name=robots]','content'),'noindex,nofollow');
 await page.waitForFunction(()=>document.body.dataset.link==='ok');
 await page.waitForFunction(()=>document.querySelectorAll('.items .item').length===2);
 assert.equal(await page.textContent('.count'),'2');
 if(shots)await shot(page,vp,`${shots}/after-${tag}-new.png`);
 // search filter
 await page.fill('#find-work','SQL');assert.equal(await page.locator('.items .item:visible').count(),1);await page.fill('#find-work','');
 // invalid model id keeps the request local
 await page.locator('.team summary').click();await page.locator('input[name=cpick][value=custom]').evaluate(e=>e.click());await page.fill('#cm','bad id!');await page.fill('#task','테스트');await page.locator('.send').click();
 assert((await page.textContent('#notice')).includes('모델 ID'));await page.locator('input[name=cpick][value=""]').evaluate(e=>e.click());
 // submit with Ctrl+Enter
 await page.fill('#task','주간 채용 공고 요약');await page.press('#task','Control+Enter');
 await page.waitForFunction(()=>!document.querySelector('#record').hidden);

 // open finished record
 await page.locator('.items .item').filter({hasText:'자기소개서'}).click();
 await page.waitForFunction(()=>document.querySelector('#status').textContent==='완료'&&document.querySelector('.secretary-reply'));
 assert.equal(await page.getAttribute('#status','data-state'),'done');
 assert.equal(await page.locator('.answer ol li').count(),2);
 assert(await page.locator('#flow .step time').first().textContent());
 assert(!(await page.isHidden('#feedback')));
 if(shots){await shot(page,vp,`${shots}/after-${tag}-record.png`);if(tag==='desktop'){await page.emulateMedia({colorScheme:'dark'});await shot(page,vp,`${shots}/after-${tag}-record-dark.png`);await page.emulateMedia({colorScheme:'light'})}}
 await page.fill('#comment','근거 수치 하나 추가');await page.press('#comment','Control+Enter');
 await page.waitForFunction(()=>document.querySelector('#status').textContent==='접수');
 const posted=await page.frames().find(f=>f.url().startsWith(PRIVATE)).evaluate(()=>posted);
 assert.equal(posted.length,2);assert.equal(posted[1].parent,2);assert.equal(posted[0].mode,'pair');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth)<=vp.width+2);
 assert.deepEqual(errors,[]);await ctx.close()}
 console.log('Desk: connect, search, submit, record, revise passed on mobile and desktop')}finally{await browser.close();server.close()}})().catch(e=>{console.error(e);process.exitCode=1});
