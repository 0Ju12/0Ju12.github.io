"""Refresh official public SWEA D1-D4 metadata; no statements or solutions."""
import concurrent.futures
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

BASE = 'https://swexpertacademy.com/main/code/problem/'
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'content/study_lab/swea-catalog.json'

def fetch(page):
    query = [('problemLevel',str(x)) for x in range(1,5)] + [('pageIndex',str(page))]
    url = BASE + 'problemList.do?' + urllib.parse.urlencode(query)
    for attempt in range(3):
        try:
            request = urllib.request.Request(url,headers={'User-Agent':'StudyCatalog/1.0 (public problem metadata)'})
            with urllib.request.urlopen(request,timeout=40) as response:
                return response.read().decode('utf-8')
        except Exception:
            if attempt == 2: raise
            time.sleep(1+attempt)

def parse(page):
    if '<!-- widget-list -->' not in page: raise ValueError('Official list markup missing')
    region = page.split('<!-- widget-list -->',1)[1].split('<!--// widget-list-->',1)[0]
    out=[]
    for block in region.split('class="week_num">')[1:]:
        number = re.match(r'(\d+)\.',block)
        anchor = re.search(r'fn_move_page\(\s*\x27([^\x27]+)\x27\s*\);?"[^>]*>(.*?)</a>',block,re.S)
        level = re.search(r'badgeC-d([1-4])">D[1-4]</span>',block)
        if not (number and anchor and level): raise ValueError('Incomplete official problem row')
        label = re.sub(r'<span\b[^>]*>.*?</span>','',anchor.group(2),flags=re.S)
        label = re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',label))).strip()
        cid=anchor.group(1)
        out.append({'number':int(number.group(1)),'title':label,'level':'D'+level.group(1),'contestProbId':cid,'url':BASE+'problemDetail.do?contestProbId='+urllib.parse.quote(cid,safe='')+'&categoryId='+urllib.parse.quote(cid,safe='')+'&categoryType=CODE'})
    if not out: raise ValueError('Empty official page')
    pages=[int(n) for n in re.findall(r'pageIndex.value=(\d+)',page)]
    return out,max(pages,default=1)

def main():
    first,last=parse(fetch(1))
    if last>500: raise ValueError('Unexpected pagination; inspect the official site')
    batches={1:first}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        tasks={pool.submit(fetch,n):n for n in range(2,last+1)}
        for future in concurrent.futures.as_completed(tasks):
            n=tasks[future];rows,_=parse(future.result());batches[n]=rows
            if len(batches)%10==0: print(f'Fetched {len(batches)}/{last} pages',flush=True)
    items=[item for n in range(1,last+1) for item in batches[n]]
    if len({item['number'] for item in items})!=len(items): raise ValueError('Duplicate numbers: incomplete pagination')
    if len({item['contestProbId'] for item in items})!=len(items): raise ValueError('Duplicate problem IDs')
    counts={level:sum(item['level']==level for item in items) for level in ['D1','D2','D3','D4']}
    if any(not n for n in counts.values()): raise ValueError('Missing difficulty')
    result={'source':BASE+'problemList.do','fetchedAt':datetime.now(timezone.utc).isoformat(),'levels':['D1','D2','D3','D4'],'pageCount':last,'count':len(items),'counts':counts,'items':sorted(items,key=lambda x:x['number'])}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    temp=DEST.with_suffix('.tmp');temp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(DEST)
    print(json.dumps({'count':len(items),'counts':counts,'pages':last},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
