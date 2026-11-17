const $=s=>document.getElementById(s);
const fly=`T = int(input())

for test_case in range(1, T + 1):
    N, M = map(int, input().split())
    arr = [list(map(int, input().split())) for _ in range(N)]

    answer = 0

    for i in range(N - M + 1):
        for j in range(N - M + 1):
            total = 0

            for r in range(M):
                for c in range(M):
                    total += arr[i + r][j + c]

            answer = max(answer, total)

    print(f"#{test_case} {answer}")`;
const examples=[{title:'파리퇴치',num:'2001',file:'파리퇴치.py',desc:'격자 위의 모든 영역을 탐색하며, 가장 큰 합을 찾아보세요.',tags:['2차원 배열','완전 탐색'],code:fly,input:'1\n5 2\n1 3 3 6 7\n8 13 9 12 8\n4 16 11 12 6\n2 4 1 23 2\n9 13 4 7 3',note:'List 2 노트의 2차원 배열 순회와 연결돼요. 시작점 (i, j)를 바꾸고, 내부 반복문의 (r, c)를 더해 M × M 영역을 방문합니다. 파리퇴치의 기본 완전 탐색 풀이를 실행합니다.',source:'SWEA 학습 예제'}, {title:'Flatten',num:'1208',file:'flatten_learning.py',desc:'높은 곳에서 낮은 곳으로, 상자가 이동하는 과정을 관찰하세요.',tags:['배열','최댓값·최솟값'],code:`dumps = int(input())
arr = list(map(int, input().split()))
for step in range(dumps):
    hi = arr.index(max(arr))
    lo = arr.index(min(arr))
    if arr[hi] - arr[lo] <= 1:
        break
    arr[hi] -= 1
    arr[lo] += 1
answer = max(arr) - min(arr)
print(answer)`,input:'8\n7 4 2 9 5 3 8 1 6 4',note:'List 2 노트의 배열과 탐색 개념을 연습하는 예제예요. 최댓값과 최솟값 위치를 찾고 양쪽 값을 갱신합니다. 이 코드는 시각화용 학습 예제이며 강의 개념을 연습하기 위한 예제입니다.',source:'학습 예제'}, {title:'선택 정렬',num:'LIST 2',file:'selection_sort.py',desc:'가장 작은 값을 찾아, 앞에서부터 차례대로 정렬하세요.',tags:['선택 정렬','배열'],code:`arr = list(map(int, input().split()))
N = len(arr)
for i in range(N - 1):
    min_idx = i
    for j in range(i + 1, N):
        if arr[j] < arr[min_idx]:
            min_idx = j
    arr[i], arr[min_idx] = arr[min_idx], arr[i]
print(arr)`,input:'29 10 14 37 13',note:'List 2 노트의 선택 정렬 예시 [29, 10, 14, 37, 13]을 실행해 봅니다. 아직 정렬하지 않은 구간에서 최솟값을 찾아 i번째 값과 교환해요. 시간 복잡도는 O(N²)입니다.',source:'강의 노트 · 학습 예제'}];
let selected=0,events=[],pos=0,timer=null,worker=null,timeout=null,finalOutput='',runError=null,runCode='',runInput='',busy=false,watchName='arr',requestId=0,runMetrics={};
const breakpoints=new Set();
function saved(key,fallback){if(new URLSearchParams(location.search).get('ephemeral')==='1')return fallback;try{return localStorage.getItem(key)??fallback}catch{return fallback}}
function persist(key,value){if(new URLSearchParams(location.search).get('ephemeral')==='1')return;try{localStorage.setItem(key,value)}catch{}}
function notify(text){$('notice').textContent=text}
function stop(){clearTimeout(timer);timer=null;$('play').textContent='▶';$('play').setAttribute('aria-label','재생')}
function setBusy(value){busy=value;$('run').disabled=value;$('cancel').hidden=!value}
function cancelRun(message='실행을 취소했어요.'){requestId++;clearTimeout(timeout);if(worker){worker.terminate();worker=null}setBusy(false);$('status').textContent=message}
function initialArray(){try{const lines=$('input').value.trim().split('\n');if(selected===0){let [n,m]=lines[1].split(/\s+/).map(Number);if(!Number.isInteger(n)||n<1||n>20)return {arr:[]};return {arr:lines.slice(2,2+n).map(x=>x.trim().split(/\s+/).map(Number)),M:m}}return {arr:lines[selected===1?1:0].trim().split(/\s+/).map(Number)}}catch{return {arr:[]}}}
function selectExample(index){stop();if(busy)cancelRun();selected=index;const e=examples[index];$('code').value=saved('algo-code-'+index,e.code);$('input').value=saved('algo-input-'+index,e.input);$('title').textContent=e.title;$('desc').textContent=e.desc;$('filename').textContent=e.file+' · '+e.source;$('concepts').innerHTML=e.tags.map(t=>'<span>'+t+'</span>').join('');$('noteText').textContent=e.note;$('visName').textContent=index===0?'2차원 배열 탐색':index===1?'배열 높이의 변화':'최솟값 탐색 & 교환';events=[];pos=0;runError=null;finalOutput='';watchName='arr';breakpoints.clear();$('status').textContent='실행을 누르면 기록을 만들어요';notify('');$('problems').innerHTML=examples.map((e,i)=>`<button class="problem ${i===index?'selected':''}" data-index="${i}"><small>${e.num} · ${e.source}</small><strong>${e.title}</strong></button>`).join('');document.querySelectorAll('.problem').forEach(b=>b.onclick=()=>selectExample(+b.dataset.index));updateWatchOptions();render()}
function nums(line){$('numbers').replaceChildren();$('code').value.split('\n').forEach((_,i)=>{const b=document.createElement('button');b.className=(i+1===line?'current ':'')+(breakpoints.has(i+1)?'breakpoint':'');b.textContent=i+1;b.title=`${i+1}번 줄 중단점 ${breakpoints.has(i+1)?'해제':'설정'}`;b.setAttribute('aria-pressed',String(breakpoints.has(i+1)));b.onclick=()=>{breakpoints.has(i+1)?breakpoints.delete(i+1):breakpoints.add(i+1);nums(events[pos]?.line)};$('numbers').append(b)});$('numbers').scrollTop=$('code').scrollTop;$('breakpointCount').textContent=`중단점 ${breakpoints.size}개`}
function updateWatchOptions(){const names=new Set(['arr']);for(const e of events)for(const [k,v] of Object.entries(e.vars||{}))if(v&&typeof v==='object')names.add(k);const actual=[...names].filter(n=>events.some(e=>Object.hasOwn(e.vars||{},n)));if(actual.length&&!actual.includes(watchName))watchName=actual.find(n=>ALGO_VISUALS.infer(n)!=='array')||actual[0];$('watchArray').replaceChildren();for(const name of names){const option=document.createElement('option');option.value=name;option.textContent=name;$('watchArray').append(option)}$('watchArray').value=watchName}
function visualize(v){if(ALGO_VISUALS.draw($('canvas'),events[pos],$('visMode').value,watchName)){$('sizeBadge').textContent=$('visMode').selectedOptions[0].textContent;return}const data=Array.isArray(v[watchName])?v[watchName]:events.length?[]:initialArray().arr;const prev=events[pos-1]?.vars?.[watchName];const canvas=$('canvas');canvas.replaceChildren();$('sizeBadge').textContent='—';if(!Array.isArray(data)||!data.length){canvas.textContent=events.length?`${watchName} 배열이 아직 없거나 비어 있어요.`:'실행하면 선택한 배열을 시각화해요.';return}const matrix=Array.isArray(data[0]);if(matrix){if(!data.every(Array.isArray)){canvas.textContent='숫자로 된 1차원·2차원 배열을 선택해 주세요.';return}const width=Math.max(...data.map(r=>r.length));if(width>20||data.length>20){canvas.textContent='20 × 20 이하의 배열로 줄여 주세요.';return}const grid=document.createElement('div');grid.className='grid';grid.style.gridTemplateColumns=`repeat(${Math.max(width,1)},1fr)`;data.forEach((row,r)=>row.forEach((value,c)=>{const el=document.createElement('div');el.className='cell';const m=v.M;if(watchName==='arr'&&Number.isInteger(v.i)&&Number.isInteger(v.j)&&r>=v.i&&r<v.i+m&&c>=v.j&&c<v.j+m)el.classList.add('region');const currentText=runCode.split('\n')[(events[pos]?.line||0)-1]||'';if(watchName==='arr'&&currentText.includes('arr[i + r][j + c]')&&r===v.i+v.r&&c===v.j+v.c)el.classList.add('hit');if(prev?.[r]?.[c]!==undefined&&JSON.stringify(prev[r][c])!==JSON.stringify(value))el.classList.add('changed');el.textContent=String(value);el.title=`${watchName}[${r}][${c}] = ${value}`;grid.append(el)}));canvas.append(grid);$('sizeBadge').textContent=data.length+' × '+width}else{if(!data.every(x=>typeof x==='number'&&Number.isFinite(x))){canvas.textContent=JSON.stringify(data).slice(0,500);return}const bars=document.createElement('div');bars.className='bars';const max=Math.max(...data.map(Math.abs),1);data.slice(0,100).forEach((val,i)=>{const wrap=document.createElement('div');wrap.className='barWrap';const el=document.createElement('div');el.className='bar'+([v.hi,v.lo,v.j,v.min_idx].includes(i)?' hit':'')+(prev?.[i]!==undefined&&prev[i]!==val?' changed':'');el.style.height=(35+Math.abs(val)/max*150)+'px';el.textContent=String(val);el.title=`${watchName}[${i}] = ${val}`;const label=document.createElement('small');label.textContent=i;wrap.append(el,label);bars.append(wrap)});canvas.append(bars);$('sizeBadge').textContent=data.length+' elements'+(data.length>100?' · 처음 100개':'')}}
function scrollToLine(line){if(!line)return;const top=(line-1)*21,bottom=top+21;if(top<$('code').scrollTop||bottom>$('code').scrollTop+$('code').clientHeight-32)$('code').scrollTop=Math.max(0,top-$('code').clientHeight/2);$('numbers').scrollTop=$('code').scrollTop}
function render(){const e=events[pos],v=e?.vars||{},previous=events[pos-1]?.vars||{};nums(e?.line);visualize(v);$('variables').replaceChildren();Object.entries(v).filter(([k,val])=>!Array.isArray(val)).slice(0,24).forEach(([k,val])=>{const changed=pos>0&&JSON.stringify(previous[k])!==JSON.stringify(val);const el=document.createElement('div');el.className='var'+(changed?' changed':'');el.textContent=k;const strong=document.createElement('strong');strong.textContent=val&&typeof val==='object'?JSON.stringify(val).slice(0,150):String(val);el.append(strong);if(changed){const before=document.createElement('small');before.textContent=Object.hasOwn(previous,k)?`${previous[k]} → ${val}`:'새 변수';el.append(before)}$('variables').append(el)});if(!e)$('variables').innerHTML='<p class="empty">실행하면 변수의 변화를 여기서 볼 수 있어요.</p>';$('stepCount').textContent=events.length?`${pos+1} / ${events.length}`:'0 / 0';$('timeline').max=Math.max(events.length-1,0);$('timeline').value=pos;const ended=e?.kind==='end';$('output').textContent=(ended?finalOutput:e?.output)||'아직 출력이 없어요.';if(ended&&runError)$('output').textContent+='\n'+runError;const text=e?runCode.split('\n')[e.line-1]?.trim():'';$('stepTitle').textContent=ended?(runError?'실행 오류':'실행 완료'):e?.kind==='return'?'함수 반환 · '+JSON.stringify(e.returnValue):e?`${e.line}번 줄 · ${text}`:'코드를 실행해 볼까요?';$('stepDesc').textContent=e?(ended?(runError?'오류 이전까지의 기록을 되짚어 확인할 수 있어요.':'모든 코드가 실행된 최종 상태입니다. 출력과 변수의 마지막 값을 확인해 보세요.'):e.kind==='return'?'함수가 값을 반환하는 순간입니다. 호출 스택에서 반환값을 확인하세요.':text?.includes('total +=')?`arr[${v.i+v.r}][${v.j+v.c}]의 값을 total에 더할 차례예요. 현재 누적 합은 ${v.total}입니다.`:text?.includes('max(answer')?`영역 합 ${v.total}과 지금까지의 최댓값 ${v.answer}를 비교합니다.`:text?.includes('for ')?'반복문의 다음 원소를 확인합니다. 다음 단계를 누르면 변수 변화가 반영돼요.':'현재 표시된 값은 이 줄을 실행하기 직전의 상태입니다.'):'왼쪽의 코드를 확인하고 실행 버튼을 눌러 주세요.';$('visSub').textContent=ended?'실제 Python 실행 기록 · 최종 상태':e?'실제 Python 실행 기록 · 현재 줄 실행 직전':'입력값이 눈에 보이는 구조가 됩니다';for(const id of ['prev','next','play','reset','timeline','last','nextChange','seekLine','export'])$(id).disabled=!events.length;scrollToLine(e?.line)}
function move(delta){if(!events.length)return;pos=Math.max(0,Math.min(events.length-1,pos+delta));render()}
function schedule(){const delay=700/Number($('speed').value);timer=setTimeout(()=>{timer=null;if(pos>=events.length-1){if($('loop').checked)pos=0;else{stop();return}}else pos++;render();if(breakpoints.has(events[pos]?.line)&&events[pos]?.kind==='line'){stop();notify(`${events[pos].line}번 줄 중단점에서 멈췄어요.`);return}if(pos===events.length-1&&!$('loop').checked){stop();return}schedule()},delay)}
function start(){if(!events.length)return;notify('');if(pos===events.length-1){pos=0;render()}$('play').textContent='Ⅱ';$('play').setAttribute('aria-label','일시정지');schedule()}
function invalidate(message){stop();if(busy)cancelRun();events=[];pos=0;finalOutput='';runError=null;runMetrics={};updateWatchOptions();render();persist('algo-code-'+selected,$('code').value);persist('algo-input-'+selected,$('input').value);$('status').textContent=message;notify('')}
function ensureWorker(){if(worker)return worker;worker=new Worker('worker.js?v=trace2');return worker}
$('run').onclick=()=>{stop();clearTimeout(timeout);runCode=$('code').value;runInput=$('input').value;events=[];pos=0;finalOutput='';runError=null;updateWatchOptions();render();setBusy(true);notify('');$('status').textContent=worker?'Python 실행 중…':'Python 로딩 및 실행 중… (첫 실행 약 10~30초)';persist('algo-code-'+selected,runCode);persist('algo-input-'+selected,runInput);const active=++requestId;const w=ensureWorker();timeout=setTimeout(()=>{if(active===requestId)cancelRun('시간 초과: 입력·반복문을 확인하고 다시 실행해 주세요.')},60000);w.onmessage=({data})=>{if(active!==requestId)return;clearTimeout(timeout);setBusy(false);events=data.events||[];finalOutput=data.output||'';runError=data.error;runMetrics={steps:data.steps||events.length,elapsedMs:data.elapsedMs||0};$('status').textContent=data.error?'실행 오류 · 마지막 단계에서 확인해 주세요':`${events.length}단계 기록 완료 · 배속을 골라 재생하세요`;updateWatchOptions();if(data.error)pos=Math.max(0,events.length-1);render();if(data.error&&!events.length)$('output').textContent=data.error};w.onerror=()=>{if(active!==requestId)return;cancelRun('Python 로딩 실패. 네트워크 연결 후 다시 실행해 주세요.')};w.postMessage({code:runCode,input:runInput})};
$('cancel').onclick=()=>cancelRun();$('next').onclick=()=>{stop();move(1)};$('prev').onclick=()=>{stop();move(-1)};$('reset').onclick=()=>{stop();pos=0;render()};$('last').onclick=()=>{stop();pos=Math.max(0,events.length-1);render()};$('play').onclick=()=>timer?stop():start();$('timeline').oninput=()=>{stop();pos=+$('timeline').value;render()};$('speed').value=saved('algo-speed','1');if(!$('speed').value)$('speed').value='1';$('speed').onchange=()=>{persist('algo-speed',$('speed').value);if(timer){clearTimeout(timer);schedule()}notify(`${$('speed').value}배속 · 초당 약 ${(Number($('speed').value)/0.7).toFixed(1)}단계`)};
$('nextChange').onclick=()=>{stop();const state=JSON.stringify(events[pos]?.vars);const next=events.findIndex((e,i)=>i>pos&&JSON.stringify(e.vars)!==state);if(next<0){notify('이후에 변수 변경이 없어요.');return}pos=next;render()};$('seekLine').onclick=()=>{stop();const line=Number($('targetLine').value);if(!Number.isInteger(line)||line<1){notify('올바른 줄 번호를 입력해 주세요.');return}let next=events.findIndex((e,i)=>i>pos&&e.line===line&&e.kind!=='end');let wrapped=false;if(next<0){next=events.findIndex(e=>e.line===line&&e.kind!=='end');wrapped=true}if(next<0){notify(`${line}번 줄은 이 실행에서 방문하지 않았어요.`);return}pos=next;render();notify(`${wrapped?'처음부터 찾아 ':''}${line}번 줄의 실행 위치로 이동했어요.`)};$('clearBreakpoints').onclick=()=>{breakpoints.clear();nums(events[pos]?.line);notify('모든 중단점을 해제했어요.')};$('visMode').onchange=()=>render();$('watchArray').onchange=()=>{watchName=$('watchArray').value;render()};
$('export').onclick=()=>{const payload={problem:examples[selected].title,exportedAt:new Date().toISOString(),code:runCode,input:runInput,output:finalOutput,error:runError,events};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`algo-studio-${examples[selected].num.replace(/\s/g,'-')}-trace.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('코드·입력·단계별 변수를 JSON 파일로 저장했어요.')};
$('code').oninput=()=>{breakpoints.clear();invalidate('코드가 바뀌었어요. 다시 실행해 주세요.')};$('code').onscroll=()=>{$('numbers').scrollTop=$('code').scrollTop};$('code').onkeydown=e=>{if(e.key==='Tab'){e.preventDefault();const a=e.target.selectionStart,b=e.target.selectionEnd;e.target.setRangeText('    ',a,b,'end');$('code').oninput()}};$('input').oninput=()=>invalidate('입력이 바뀌었어요. 다시 실행해 주세요.');$('restore').onclick=()=>{persist('algo-code-'+selected,examples[selected].code);persist('algo-input-'+selected,examples[selected].input);selectExample(selected)};$('notesNav').onclick=()=>$('note').scrollIntoView({behavior:'smooth'});$('lab').onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();if(!busy)$('run').click();return}if(/^(INPUT|TEXTAREA|SELECT|BUTTON)$/.test(e.target.tagName)||e.target.isContentEditable)return;if(e.key===' '){e.preventDefault();$('play').click()}if(e.key==='ArrowRight'){e.preventDefault();$('next').click()}if(e.key==='ArrowLeft'){e.preventDefault();$('prev').click()}});// Same-origin handoff: only code and note identity are passed, never study keys.
const params=new URLSearchParams(location.search);
if(params.get('embedded')!=='1')location.replace('../index.html#/algo');
const noteSlug=params.get('note')||'list2';
const safeNote=/^[a-z0-9_]+$/.test(noteSlug)?noteSlug:'list2';
const noteHref='../notes/'+safeNote+'.html';
$('sourceNote').href=noteHref;
$('notesNav').onclick=()=>{location.href=noteHref};
const preset={fly:0,flatten:1,selection:2}[params.get('example')]??0;
selectExample(preset);
if(params.get('import')==='note'){
    let handoff=null;
    try{handoff=JSON.parse(sessionStorage.getItem('study-lab-handoff')||'null');sessionStorage.removeItem('study-lab-handoff')}catch{}
    if(handoff&&handoff.note===safeNote&&typeof handoff.code==='string'&&handoff.code.length<=50000&&Date.now()-handoff.createdAt<600000){
        $('code').value=handoff.code;
        $('input').value='';
        $('filename').textContent=safeNote+' · 강의 코드';
        $('title').textContent='강의 코드 실험';
        $('desc').textContent='필요한 입력값을 넣고 실행하세요. 원본 강의 노트는 수정되지 않습니다.';
        invalidate('강의 코드를 가져왔어요. 입력값을 확인하고 실행하세요.');
    }else notify('가져올 코드가 없거나 만료되었어요. 노트에서 다시 열어 주세요.');
}

// Embedded workspace: the host owns per-problem drafts and portable backups.
if(params.get('embedded')==='1'){
    document.body.classList.add('embedded-workspace');
    const workToken=params.get('token');
    let loaded=false;
    function emitWork(){if(!loaded)return;window.parent.postMessage({type:'algo-work:state',token:workToken,code:$('code').value,input:$('input').value,output:finalOutput,error:runError,ran:events.length>0,metrics:runMetrics},location.origin)}
    window.addEventListener('message',function(e){
        const m=e.data;
        if(e.source!==window.parent||e.origin!==location.origin||!m||m.token!==workToken)return;if(m.type==='algo-work:replace'&&loaded){if(typeof m.code==='string')$('code').value=m.code;if(typeof m.input==='string')$('input').value=m.input;if(['auto','array','stack','queue','graph','calls'].includes(m.mode))$('visMode').value=m.mode;invalidate('선택한 코드·입력으로 변경했어요.');emitWork();if(m.run)$('run').click();return}if(m.type!=='algo-work:load'||loaded)return;
        if(typeof m.code!=='string'||m.code.length>100000||typeof m.input!=='string'||m.input.length>100000)return;
        loaded=true;stop();if(busy)cancelRun();events=[];pos=0;finalOutput='';runError=null;
        $('code').value=m.code;$('input').value=m.input;
        $('title').textContent=(m.problem.number?m.problem.number+'. ':'')+m.problem.title;
        $('filename').textContent='my_solution.py';const badge=document.querySelector('.difficulty');if(badge)badge.textContent=m.problem.level||'';$('desc').textContent='알고리즘 기록에 연결된 내 풀이';
        $('concepts').replaceChildren();$('visName').textContent='내 코드 실행 상태';updateWatchOptions();render();
        $('status').textContent='코드와 입력을 작성하고 실행하세요.';
        $('restore').hidden=true;
        emitWork();
    });
    $('code').addEventListener('input',emitWork);$('input').addEventListener('input',emitWork);
    const oldTab=$('code').onkeydown;$('code').onkeydown=function(e){oldTab(e);if(e.key==='Tab')emitWork()};
    const originalRun=$('run').onclick;
    $('run').onclick=function(){originalRun();if(worker){const onResult=worker.onmessage;worker.onmessage=function(e){onResult(e);emitWork()}}};
    window.addEventListener('pagehide',emitWork);
    window.parent.postMessage({type:'algo-work:ready',token:workToken},location.origin);
    if(typeof ResizeObserver!=='undefined')new ResizeObserver(function(){window.parent.postMessage({type:'algo-work:height',token:workToken,height:document.body.scrollHeight+24},location.origin)}).observe(document.body);
}

$('inputFile').onchange=async function(){const file=this.files[0];if(!file)return;try{const text=await ALGO_TEXT_FILES.apply(file,$('input').value,window.confirm.bind(window));if(text===null)return;$('input').value=text;$('input').dispatchEvent(new Event('input',{bubbles:true}));$('status').textContent=file.name+' 입력을 가져왔어요. 이 문제에 자동 저장됩니다.'}catch(e){$('status').textContent=e.message}finally{this.value=''}};
// Batch checks use an isolated worker and report raw results to the host.
let batchWorker=null,batchEpoch=0,batchAbort=null;
function cancelBatch(){batchEpoch++;if(batchAbort){batchAbort();batchAbort=null;}if(batchWorker){batchWorker.terminate();batchWorker=null}}
window.addEventListener('message',async function(e){const m=e.data;if(e.source!==window.parent||e.origin!==location.origin||!m||m.token!==params.get('token'))return;if(m.type==='algo-work:batch-cancel'){cancelBatch();return}if(m.type!=='algo-work:batch'||!Array.isArray(m.cases)||!m.cases.length||m.cases.length>20||m.cases.some(c=>!c||typeof c.input!=='string'||c.input.length>100000||typeof c.expected!=='string'||c.expected.length>100000))return;cancelBatch();const epoch=batchEpoch,code=$('code').value;batchWorker=new Worker('worker.js?v=trace2');for(const c of m.cases){const w=batchWorker;if(epoch!==batchEpoch)break;const data=await new Promise(resolve=>{const timeout=setTimeout(()=>resolve({error:'실행 제한 시간 초과',output:'',timeout:true}),60000);batchAbort=()=>{clearTimeout(timeout);resolve({cancelled:true})};w.onmessage=({data})=>{clearTimeout(timeout);resolve(data)};w.onerror=()=>{clearTimeout(timeout);resolve({error:'Python 실행기를 불러오지 못했어요.',output:'',timeout:true})};w.postMessage({code,input:c.input,trace:false})});batchAbort=null;if(epoch!==batchEpoch)break;window.parent.postMessage({type:'algo-work:batch-result',token:m.token,batchId:m.batchId,caseId:c.id,input:c.input,expected:c.expected,output:data.output,error:data.error,steps:data.steps,elapsedMs:data.elapsedMs},location.origin);if(data.timeout){w.terminate();batchWorker=new Worker('worker.js?v=trace2');}}if(epoch===batchEpoch)window.parent.postMessage({type:'algo-work:batch-done',token:m.token,batchId:m.batchId},location.origin);if(epoch===batchEpoch)cancelBatch()});

// Comparisons never replace the editor and use fresh workers for each candidate.
let compareEpoch=0,compareWorker=null,compareAbort=null;
function cancelComparison(){compareEpoch++;if(compareAbort){compareAbort();compareAbort=null}if(compareWorker){compareWorker.terminate();compareWorker=null}}
window.addEventListener('message',async e=>{const m=e.data;if(e.source!==parent||e.origin!==location.origin||!m||m.token!==params.get('token'))return;if(m.type==='algo-work:compare-cancel'){cancelComparison();return}if(m.type!=='algo-work:compare'||!Array.isArray(m.codes)||m.codes.length!==2||m.codes.some(c=>typeof c!=='string'||c.length>100000)||typeof m.input!=='string'||m.input.length>100000)return;if(busy)cancelRun('비교 실행으로 전환했어요.');cancelBatch();cancelComparison();const epoch=compareEpoch,results=[];for(const code of m.codes){if(epoch!==compareEpoch)return;const w=new Worker('worker.js?v=trace2');compareWorker=w;const result=await new Promise(resolve=>{const t=setTimeout(()=>resolve({error:'60초 실행 시간 초과',events:[],output:'',steps:0,elapsedMs:60000}),60000);compareAbort=()=>{clearTimeout(t);resolve(null)};w.onmessage=({data})=>{clearTimeout(t);resolve(data)};w.onerror=()=>{clearTimeout(t);resolve({error:'Python 실행기 로딩 실패',events:[],output:'',steps:0,elapsedMs:0})};w.postMessage({code,input:m.input,trace:true})});w.terminate();compareAbort=null;if(epoch!==compareEpoch||!result)return;results.push(result)}if(epoch===compareEpoch){compareWorker=null;parent.postMessage({type:'algo-work:compare-result',comparisonId:m.comparisonId,token:m.token,results},location.origin)}});
window.addEventListener('pagehide',cancelComparison);
