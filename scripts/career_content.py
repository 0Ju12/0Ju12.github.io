"""Build editable practice content only from the repository's public source data."""
import hashlib

def prepare_essays(prep, data=None):
    from career_copy import ESSAYS
    rows=[]
    for e in prep.get('essays', []):
        row=dict(e)
        row['id']='essay:'+hashlib.sha256(e['q'].encode()).hexdigest()[:16]
        row['draft']=next((text for fragment,text in ESSAYS if fragment in e['q']), '[실제 경험을 확인해 작성하세요]\n'+e.get('tip',''))
        row['verify']='공개 자료에 근거해 문항별로 다시 쓴 수정용 초안입니다. 가치관·지원 의사·향후 계획은 제안입니다. 대괄호와 회사 정보는 본인이 확인한 뒤 제출하세요.'
        row['sources']=[{'title':'포트폴리오 원문','url':'https://github.com/0Ju12/0Ju12.github.io/blob/main/data/portfolio.yaml'}, {'title':'설계 판단·한계','url':'https://github.com/0Ju12/0Ju12.github.io/blob/main/data/case_notes.yaml'}]
        row['outline']=['이 문항의 결론','실제 경험과 직접 한 행동','결과·한계','직무 연결']
        rows.append(row)
    return rows


def rebuild_decks(data,variants,projects):
    from career_copy import PROJECTS
    cases=data.get('case_notes') or {};out=[];name=data['profile']['name']
    def short(s,n=82):
        return s if len(s)<=n else s[:n-1]+'…'
    def source(pid):return [{'title':'프로젝트 근거','url':'https://0ju12.github.io/projects/'+pid+'.html'}]
    for role,v in variants.items():
        order=[p for gid in v.get('order',[]) for g,p in projects if g.get('id')==gid]
        if not order:order=[p for g,p in projects]
        if not order:continue
        focus='data-projects' if role=='data' else 'ssafy-16'
        preferred=next((p for g,p in projects if p['id']==focus),None)
        if preferred:order=[preferred]+[p for p in order if p['id']!=focus]
        p=order[0];d=p['digest'];cn=(cases.get(p['id']) or {}).get('ko') or {}
        label=v.get('label',role)
        note=f"안녕하세요. {label} 직무를 준비하는 {name}입니다. 제가 강조하고 싶은 강점은 데이터의 제약을 확인하고 결과를 검증하는 태도입니다. {p.get('short') or p['title']}에서는 {d['problem']} 제가 맡은 역할은 {d['role']} 구체적으로 {' '.join(d.get('did',[])[:1])} 결과는 {' '.join(d.get('result',[])[:1])} 이 성과는 해당 프로젝트의 조건에서 얻은 결과이며, 다른 환경에 적용할 때는 검증이 더 필요합니다. 입사 후에도 업무의 기준을 이해하고, 작은 개선부터 근거를 남기며 기여하고 싶습니다. 감사합니다."
        if p['id']=='ssafy-16':
            note=f'안녕하세요. {label} 직무를 준비하는 {name}입니다. 제 강점은 AI의 응답을 그대로 믿기보다 서비스에서 확인할 수 있는 규칙으로 검증하는 태도입니다. SSAFY의 ThRead 프로젝트에서 2인 팀의 Django 백엔드와 LLM 연동, 크롤링 파이프라인을 담당했습니다. LLM에는 댓글의 적절성을 판단하게 하고, 삭제와 채택은 원본 데이터를 기준으로 코드가 처리하도록 구성했습니다. 이 과정에서 자동 테스트를 통해 예외 처리와 출력 규칙을 확인했습니다. 다만 가짜 LLM을 사용한 테스트가 실제 답변 품질까지 보장하는 것은 아니므로, 두 평가를 구분해야 한다고 배웠습니다. 입사 후에도 모델의 성능과 서비스의 신뢰성을 함께 살피며 기여하고 싶습니다. 감사합니다.'
        elif p['id']=='data-projects':
            note=f'안녕하세요. {label} 직무를 준비하는 {name}입니다. 제 강점은 데이터를 모으는 데서 끝내지 않고 정제와 검증, 활용까지 이어지는 흐름을 구현하는 것입니다. 공개 데이터 프로젝트에서 수집부터 모델링과 자동화까지 직접 수행했습니다. 지진 데이터의 수정본을 반영하고, 원본과 정제·집계 계층을 구분하며, SQL로 데이터를 활용하는 흐름을 만들었습니다. 모델 평가에서는 무작위 분할과 시간 분할의 결과가 달라지는 점도 확인했습니다. 이를 통해 수치 하나보다 데이터가 바뀌는 조건과 평가 방식까지 설명하는 일이 중요하다고 배웠습니다. 입사 후에는 업무의 데이터 흐름을 먼저 이해하고, 재실행해도 일관된 결과를 얻을 수 있는 작은 개선부터 검증하며 기여하고 싶습니다. 감사합니다.'
        out.append({'id':'intro-'+role,'title':'1분 자기소개 · '+label,'kind':'intro','role':role,'min':1,'sources':source(p['id']),'verify':'직무 선택 이유·포부는 제안입니다. 본인의 생각으로 수정하고 말하기 시간을 확인하세요.','slides':[{'t':'bullets','layout':'intro','kicker':'60초 · 핵심 경험 하나','h':name+' · 검증 가능한 결과를 만드는 사람','items':[short(p.get('short') or p['title']),short(d['role']),short((d.get('result')or['검증 과정과 한계 설명'])[0])],'note':note}]})
        slides=[{'t':'title','kicker':label+' · 5분 직무 발표','h':'데이터가 바뀌어도 검증할 수 있는 흐름' if role=='data' else 'AI의 응답을 서비스의 규칙으로 검증하기','sub':name,'note':f'안녕하세요. {name}입니다. 두 가지 경험을 통해 문제를 정의하고 결과를 검증하는 과정을 설명하겠습니다.'}]
        for p in order[:2]:
            d=p['digest'];cn=(cases.get(p['id']) or {}).get('ko') or {}
            story=PROJECTS.get(p['id'])
            if story:
                slides.extend([{'t':'bullets','kicker':p.get('short')or p['title'],'h':story[j][0],'items':story[j][1],'note':' '.join(story[k][2] for k in ((0,1) if j==1 else (2,3,4)))}for j in (1,3)])
            else:
                slides.append({'t':'bullets','h':p['title'],'items':d.get('did',[])[:2],'note':' '.join(d.get('result',[]))})

        slides.append({'t':'end','h':'업무의 기준을 이해하고 작은 개선부터 검증하겠습니다','sub':label+' · 실제 지원 회사의 업무에 맞춰 마지막 문장 수정','note':'두 경험에서 공통으로 배운 것은 결과를 보여 주는 것과 그 결과를 믿을 수 있는 조건을 설명하는 일이 함께 필요하다는 점입니다. 지원 직무의 실제 업무와 연결하는 문장을 확인해 보완하겠습니다. 감사합니다.'})
        out.append({'id':'role-'+role,'title':'5분 직무 발표 · '+label,'kind':'role','role':role,'min':5,'slides':slides,'sources':[s for p in order[:2] for s in source(p['id'])],'verify':'회사의 실제 업무·수치는 공고와 원문을 확인하세요. 팀 성과와 개인 기여를 구분하세요.'})
    for g,p in projects:
        d=p['digest'];cn=(cases.get(p['id']) or {}).get('ko') or {}
        sections=[('문제 정의',[d['problem']],d['problem']),('내 역할과 실행',d.get('did',[])[:3],d['role']+' '+' '.join(d.get('did',[]))),('선택과 검증 기준',cn.get('tradeoffs',[])[:2] or ['구현과 검증 과정을 설명'], ' '.join(cn.get('tradeoffs',[]))),('결과와 적용 범위',d.get('result',[]),' '.join(d.get('result',[]))),('한계와 다음 검증',cn.get('next',[])[:2] or ['다른 환경에서의 재현성과 적용 조건 확인'],' '.join(cn.get('next',[])))]
        slides=[{'t':'title','h':p.get('short')or p['title'],'kicker':'3분 프로젝트 발표','sub':p.get('tagline',''),'note':f"{p.get('short')or p['title']}의 문제, 제 역할, 판단과 검증 과정을 설명하겠습니다."}]
        story=PROJECTS.get(p['id'])
        if story:
            slides += [{'t':'bullets','h':h,'kicker':p.get('short')or p['title'],'items':items,'note':note} for h,items,note in story]
        else:
            slides += [{'t':'bullets','h':h,'kicker':p.get('short')or p['title'],'items':[short(x)for x in items],'note':note} for h,items,note in sections]

        out.append({'id':p['id'],'title':p.get('short')or p['title'],'kind':'project','min':3,'slides':slides,'sources':source(p['id']),'verify':'수치는 이 프로젝트의 데이터와 평가 조건에 한정됩니다. 발표 대본은 원문 근거를 포함하므로 실제 속도로 연습해 줄이세요.'})
    for deck in out:
        chars=sum(len(s.get('note','')) for s in deck['slides']);deck['estimated_seconds']=round(chars/6.5)
    return out
