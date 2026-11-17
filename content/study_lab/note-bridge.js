/* Runs only inside an unlocked algorithm note. No network or credentials. */
(function(){
  function init(){
    const note=location.pathname.split('/').pop().replace(/\.html$/,'');
    if(!/^[a-z0-9_]+$/.test(note))return;
    document.querySelectorAll('pre.sourceCode.python, pre.python, div.sourceCode.python > pre, pre:has(code.language-python)').forEach(function(pre){
      if(pre.dataset.labBound)return;
      pre.dataset.labBound='1';
      const button=document.createElement('button');
      button.type='button';button.className='st-lab-code';button.textContent='이 Python 코드로 실험하기 ↗';
      button.style.cssText='display:block;margin:8px 0 20px;padding:8px 12px;border:1px solid #719281;border-radius:8px;background:#edf4ef;color:#23533b;cursor:pointer;font:600 12px system-ui';
      button.onclick=function(){
        const code=(pre.querySelector('code')||pre).textContent;
        if(code.length>50000){button.textContent='코드가 너무 길어요. 50,000자 이하를 선택해 주세요.';return}
        try{sessionStorage.setItem('study-lab-handoff',JSON.stringify({note:note,code:code,createdAt:Date.now()}));location.href='../lab/index.html?import=note&note='+encodeURIComponent(note)}
        catch(_){button.textContent='브라우저의 세션 저장을 허용한 뒤 다시 시도해 주세요.'}
      };
      pre.after(button);
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
