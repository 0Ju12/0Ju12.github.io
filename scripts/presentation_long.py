"""5–10 minute illustrated presentations from public portfolio pages and retrospectives."""
import re
from pathlib import Path
from urllib.parse import quote
import yaml
ROOT=Path(__file__).resolve().parents[1]
REVISION='illustrated-20261116-v1'
POSTS={
'masters':['2026-11-wavenumber-correlation'],
'calgary-2024':['2026-11-wavenumber-correlation'],
'undergrad-research':['2026-11-plate-tectonics-co2-storage'],
'wildfire-capstone':['2026-11-small-data-spatiotemporal'],
'ssafy-16':['2026-11-llm-verify-pipeline','2026-11-rag-citation-verify','2026-11-fastapi-ai-proxy','2026-11-django-relational-db'],
'posco-pospeak':['2026-11-catastrophic-forgetting'],
'portfolio-site':['2026-11-portfolio-one-yaml'],
'prep-apps':['2026-11-portfolio-one-yaml'],
'data-projects':['2026-11-warehouse-dbt-airflow'],
}
FIGURE_GUIDES={
'masters':[
 ('Fig01','가샤 위치와 연구 범위','먼저 지도에서 가샤 지역과 관측 범위를 확인하겠습니다. 이 자료는 아부다비 해상 지역의 중력·자력 해석이라는 공간적 맥락을 보여 줍니다. 색이나 위치만 보고 구조를 확정하기보다, 어디의 어떤 관측값을 함께 해석했는지 설명하는 데 사용하겠습니다.'),
 ('Fig03','논문의 실제 5단계 분석 흐름','그림은 논문에 정리한 실제 처리 흐름입니다. 상향 연속으로 얕은 잡음의 영향을 줄이고, 단위가 다른 두 물리량을 정규화한 뒤 파수 영역에서 관계를 계산합니다. 마지막에 지표와 검증을 분리해 두었다는 점을 보시면 됩니다. 새로 그린 개념도와 원문 그림을 함께 제시해 표현과 근거를 연결했습니다.'),
 ('Fig11','SLFI·DLFI의 공간 분포','위아래 분포도는 같은 입력 자료에서도 어떤 성분을 선택하느냐에 따라 드러나는 구조가 달라진다는 점을 보여 줍니다. 공간적으로 일치하는 패턴과 추가 가설을 구분해서 설명하겠습니다. 이 그림만으로 지하 구조가 완전히 입증되는 것은 아니므로 독립 모델과 다른 탐사 자료가 필요합니다.'),
 ('Fig10','상관 구간별 분류 기준','이 그림에서는 중력과 자력의 관계가 같은 방향인지 반대 방향인지에 따라 성분을 구분하는 기준을 확인할 수 있습니다. 임계값은 보기 좋은 그림을 만드는 값으로 선택한 것이 아니라, 상관과 남는 신호 에너지를 함께 비교해 정했다는 점을 설명하겠습니다.'),
],
'calgary-2024':[
 ('캠퍼스','캘거리대학교 연구 환경','사진은 캘거리대학교 캠퍼스를 보여 주는 공개 참고 사진입니다. 제가 직접 촬영했거나 사진 속에 등장한다는 뜻은 아닙니다. 약 6개월 파견이라는 연구 환경을 소개하는 시각 자료이며, 개인적인 적응이나 갈등 장면을 이 사진으로 입증하려고 하지는 않겠습니다.'),
 ('masters:Fig03','공동연구에서 다룬 분석 과정','공동연구의 기술적 맥락은 석사 연구의 중력·자력 복합 해석입니다. 이 그림은 당시 연구에서 다룬 분석 순서를 설명하는 데 사용합니다. 해외 체류 자체보다 서로 다른 물리량을 어떤 기준으로 비교하고 검증했는지에 초점을 두겠습니다.'),
 ('masters:Fig11','해석 결과를 검토한 자료','이 분포도는 파견 기간을 포함한 공동연구 맥락의 결과 자료입니다. 모든 그림을 파견 기간에 혼자 만들었다는 뜻은 아닙니다. 제 분석 기여와 세 기관 공동연구의 결과를 구분하고, 실제로 어떤 부분을 담당했는지 질문에 답하겠습니다.'),
],
'undergrad-research':[
 ('북미','북미 판구조 형성사 복원','이 그림은 북미 지역의 판구조 형성사를 복원한 논문 그림입니다. 현재 지질 구조를 해석할 때 과거의 형성 과정을 함께 봐야 한다는 문제의식을 설명합니다. 여러 시점의 지도는 예측 성능 곡선이 아니라 지질학적 복원 자료입니다.'),
 ('북해','북해 사례와의 비교','다음은 북해 지역의 형성사 그림입니다. 북미와 북해를 같은 틀에서 비교할 때 공통적으로 볼 조건과 지역별 차이를 나누어 설명하겠습니다. 지도 사이의 시각적 유사성만으로 정량적 결론을 내리지는 않겠습니다.'),
 ('Blundell','유타 FORGE 주변의 지열발전소 참고 사진','사진은 유타 FORGE 인근 Blundell 지열발전소의 공개 참고 사진입니다. 제가 직접 촬영하거나 해당 시설을 운영했다는 의미는 아닙니다. 연구가 다룬 지열·저장소의 현실적 맥락을 보여 주는 자료이며, 사진의 원저자와 공개 이용 조건을 함께 표기했습니다.'),
],
'wildfire-capstone':[
 ('GIS_실제','미학습 강릉 산불의 실제·예측 비교','위쪽과 아래쪽의 실제와 예측을 같은 시점 기준으로 비교하겠습니다. 초기 화선이 작을 때와 확산이 커진 뒤의 형태가 어떻게 다른지 확인할 수 있습니다. 한 장면이 비슷하다는 사실과 전체 사건에 대한 일반화 성능은 구분해야 합니다. 강릉 사건을 학습에서 제외했다는 조건을 함께 설명하겠습니다.'),
 ('예측_마스크','픽셀 마스크에서 보는 오류','검은 영역은 실제와 예측의 화선 마스크입니다. 넓은 배경을 맞히는 것과 작은 화선의 형태를 맞히는 것은 다른 문제입니다. 이런 불균형 때문에 Accuracy만 보면 오류를 충분히 이해하기 어렵습니다. 경계의 누락과 과대 예측을 살펴본 뒤 F1과 IoU 같은 지표가 필요한 이유를 설명하겠습니다.'),
 ('학습_곡선','원래 보고서의 학습 곡선','이 곡선은 원래 보고서에 있던 학습·검증 기록입니다. 새로 측정하거나 임의로 그린 곡선이 아닙니다. 다만 회고에서 밀양 검증 구간이 학습 윈도우와 일부 겹쳤다는 점을 확인했으므로, 곡선이 안정적이라는 사실만으로 일반화가 입증됐다고 말하지 않겠습니다.'),
],
'ssafy-16':[
 ('도서목록','ThRead 서비스의 실제 도서 목록 화면','이 화면은 사용자가 보는 ThRead의 도서 목록입니다. 화면에 보이는 추천·목록 결과가 어떤 데이터에서 만들어지는지 뒤쪽 처리 흐름과 연결해 설명하겠습니다. 등록된 데이터의 범위와 외부 모델의 응답 범위를 구분하는 것이 설계의 중요한 조건이었습니다.'),
 ('LLM_댓글','댓글 분석 결과와 진행 상태','이 화면에서는 댓글 분석 결과가 서비스에 전달되는 형태를 볼 수 있습니다. 오래 걸리는 작업을 한 번에 기다리게 하는 대신 진행 상황을 전달하는 방식과 연결됩니다. 화면이 존재한다는 사실이 모델의 품질이나 사용자 만족도를 검증하는 것은 아니므로, 뒤에서 테스트의 범위를 구분하겠습니다.'),
 ('RAG_질의','국보 입문 가이드의 근거 제시','국보 입문 가이드는 ThRead와 구분되는 개인 RAG 프로젝트입니다. 이 화면에서는 답변과 실제 인용된 근거를 함께 확인하는 방식을 볼 수 있습니다. 검색 결과에 존재하는 번호만 허용하고, 답변에 인용되지 않은 출처를 근거처럼 늘어놓지 않는 구조를 설명하겠습니다.'),
],
'posco-pospeak':[
 ('①','KILL KONG 앱의 실제 화면','홈·채팅·단어·연습 화면을 통해 최종 팀 결과물의 사용 흐름을 소개하겠습니다. 저는 이 앱 전체를 혼자 만든 것이 아니라 교정 데이터 구축과 모델 실험을 담당했습니다. 화면은 팀 결과물의 맥락을 보여 주며, 제 기여 범위는 별도로 구분하겠습니다.'),
 ('②','LoRA·RAG·Memory를 포함한 팀 구조도','이 그림은 팀 자료에 있는 시스템 구조입니다. 학습 실험에서 사용한 FLAN-T5 LoRA와 최종 앱 구성의 Qwen-2.5를 같은 모델로 혼동하지 않도록 구분해서 설명하겠습니다. RAG와 오답노트는 최종 서비스의 맥락이고, 뒤의 점수는 특정 학습 전략 비교의 결과입니다.'),
 ('③','교정 예시의 정성 비교','이 화면은 팀 자료에 정리된 교정 예시 비교입니다. 특정 예시에서 어떤 표현을 바꾸었는지 설명하는 용도로 사용합니다. 소수의 예시를 근거로 다른 모델보다 보편적으로 우수하다고 주장하지 않으며, 측정 시점과 평가 조건이 없는 전체 순위 비교로 확대하지 않겠습니다.'),
],
'portfolio-site':[
 ('첫화면','YAML에서 생성한 포트폴리오 화면','이 화면은 구조화된 자료를 템플릿으로 렌더링한 실제 포트폴리오입니다. 같은 사실을 웹 페이지와 이력서, 문서에서 반복해서 수정하는 부담을 줄이려는 목적을 설명합니다. 시각적 표현이 통일되어도 원본 사실이 오래되면 결과물 역시 오래된 정보를 전달할 수 있다는 한계를 함께 보겠습니다.'),
 ('prep-apps:잠금_화면','공개 페이지와 잠긴 자료의 경계','잠금 화면은 공개 사이트 안에서 비공개 자료를 별도 암호화 흐름으로 다루는 방식을 보여 줍니다. 비밀번호를 입력하는 화면이 있다는 것만으로 모든 저장 방식이 안전하다는 뜻은 아닙니다. 원본의 공개 범위와 브라우저 기록, 내려받은 파일의 성격을 나누어 설명하겠습니다.'),
],
'prep-apps':[
 ('발표자료','발표자 메모를 함께 보는 기존 앱 화면','이 사진은 기존 앱의 발표자 메모 화면입니다. 이번에 확장한 5~10분 발표 화면과 동일한 최신 스크린샷이라고 표시하지는 않겠습니다. 자료를 읽는 화면에서 실제 연습으로 연결하려던 출발점을 설명하고, 이번에 보완한 저장·편집·대본 기능으로 이어가겠습니다.'),
 ('잠금_화면','암호화된 자료를 여는 잠금 화면','이 화면은 배포 자료의 잠금 방식에 대한 참고 화면입니다. 암호화된 페이지와 사용자가 작성한 로컬 기록은 서로 다른 저장 대상입니다. GitHub 권한을 주었다고 개인 기록이 서버에 저장되거나 기기 간에 자동 동기화되는 것은 아니라는 경계를 설명하겠습니다.'),
 ('공채정보','모바일에서 확인하는 준비 자료','모바일 화면은 실제 사용 환경에서 글의 길이와 이동 동선이 달라진다는 점을 보여 줍니다. 데스크톱에서 동작한다는 이유만으로 모바일에서도 편하게 사용할 수 있다고 가정할 수 없습니다. 입력 후 이동, 새로고침, 저장 실패와 복구를 별도 흐름으로 검사해야 하는 이유입니다.'),
],
'data-projects':[
 ('지진_파이프라인','USGS 지진 자료의 수집·검증 결과','지도와 집계는 지진 데이터 파이프라인의 실제 출력입니다. 이 자료에서 중요한 점은 새 행을 추가하는 것뿐 아니라 이미 들어온 관측값이 수정될 수 있다는 사실입니다. 지도에 점을 찍는 결과와 수정 이력을 관리하는 처리 과정을 연결해 설명하겠습니다.'),
 ('전력_수요','전력 수요의 실제값과 모델 비교','이 그림은 공개된 프로젝트의 전력 수요 실제값과 모델 결과입니다. 새로 생성한 임의의 곡선이 아닙니다. 기준선과 비교한 평가 구간이 무엇인지, 평균 오차가 작더라도 피크나 특정 시간대에서 어떤 오류가 남을 수 있는지 설명하겠습니다.'),
 ('설비_센서','설비 센서의 부품별 이상 점수','센서 그래프는 부품별 상태와 이상 점수가 시간에 따라 어떻게 달라지는지 보여 줍니다. 시계열 문제에서 무작위 분할과 시간 분할의 결과가 달라질 수 있다는 논점으로 이어집니다. 특정 그래프의 패턴을 현장 고장 진단의 보편적인 성능으로 확대하지 않겠습니다.'),
],
}

def paragraphs(pid):
    result=[];sources=[]
    for slug in POSTS[pid]:
        path=ROOT/'content/posts'/f'{slug}.md'
        if not path.exists():continue
        text=path.read_text();text=re.sub(r'^---\n.*?\n---\n','',text,flags=re.S)
        text=re.split(r'\n## (?:면접 질문|출처|참고)',text)[0]
        text=re.sub(r'```.*?```','',text,flags=re.S)
        sources.append({'title':'회고 원문 · '+slug,'url':'https://0ju12.github.io/posts/'+slug+'.html'})
        for block in re.split(r'\n\s*\n',text):
            if block.lstrip().startswith(('#','|','<')):continue
            block=re.sub(r'!\[[^]]*\]\([^)]*\)','',block)
            block=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',block)
            block=re.sub(r'(?m)^\s*(?:[-*>]|\d+[.)])\s*','',block)
            block=re.sub(r'[*`_]|<[^>]+>','',block).strip();block=re.sub(r'\s+',' ',block)
            if len(block)>=55:result.append(block)
    return result,sources

def figure(pid,key,caption,explanation):
    target=pid
    if ':' in key:target,key=key.split(':',1)
    directory=ROOT/'docs/assets/photos'/target
    matches=sorted(p for p in directory.glob('*') if p.suffix.lower() in ('.jpg','.png') and key in p.name)
    if not matches:return None
    p=matches[0];credits={};f=directory/'credits.yaml'
    if f.exists():credits=yaml.safe_load(f.read_text())or{}
    credit=credits.get(p.name,{})
    return {'img':'../'+p.relative_to(ROOT/'docs').as_posix(),'caption':caption,'credit':credit.get('credit','자료: 기존 공개 포트폴리오의 프로젝트 그림·화면'),'image_source':credit.get('page','https://0ju12.github.io/'+quote(p.relative_to(ROOT/'docs').as_posix(),safe='/')),'note':explanation}

def long_decks(data,variants,projects):
    from career_copy import PROJECTS
    decks=[];project_decks={};name=data['profile']['name']
    for group,p in projects:
        pid=p['id'];story=PROJECTS.get(pid)
        if not story:continue
        title=p.get('short')or p['title'];digest=p['digest'];blocks,sources=paragraphs(pid)
        images=[x for x in (figure(pid,*row)for row in FIGURE_GUIDES[pid]) if x]
        common='https://0ju12.github.io/projects/'+pid+'.html'
        def slide(h,items,note,**extra):return dict(t='bullets',h=h,items=items,note=note,kicker=title,**extra)
        def pictured(fig,h=None):
            return slide(h or fig['caption'],[],fig['note'],img=fig['img'],layout='figure',caption=fig['caption'],credit=fig['credit'],image_source=fig['image_source'])
        diagram={'img':'../assets/presentation/'+pid+'-flow.svg','caption':'원문에 근거해 재구성한 개념도','credit':'도식 재구성: 포트폴리오·회고 자료 기반','image_source':common}
        slides=[{'t':'title','h':title,'kicker':'5~10분 · 그림으로 설명하는 프로젝트','sub':p.get('tagline',''),'note':f'안녕하세요. {name}입니다. 오늘은 {title}의 배경부터 제가 맡은 일, 실제 자료로 확인한 결과와 남은 한계까지 설명하겠습니다. 화면의 사진과 그래프는 기존 공개 포트폴리오 자료이며, 새로 만든 도식은 개념도라고 따로 표시했습니다.'},
         slide('오늘 설명할 세 가지',['어떤 문제를 왜 풀었는가','내가 선택한 방법과 판단 기준','확인한 결과와 아직 검증하지 못한 것'],f'이 발표는 문제, 선택, 검증의 순서로 진행하겠습니다. 구현 과정에서 제가 직접 한 일과 팀 또는 공동연구의 성과를 구분하겠습니다. 지표를 설명할 때는 평가 데이터와 조건을 함께 말씀드리고, 사진이나 사례 화면이 증명할 수 있는 범위도 구분하겠습니다.'),
         slide(story[0][0],story[0][1],story[0][2]),
         slide(story[1][0],story[1][1],story[1][2]),
         pictured(images[0]) if images else slide('입력과 범위를 먼저 고정했습니다',digest.get('did',[])[:2],digest['problem']),
         slide('전체 처리 흐름과 단계별 책임',[], '이 도식은 원문에 있는 처리 순서를 발표용으로 다시 그린 개념도입니다. 왼쪽에서 오른쪽으로 자료가 흐를 때 각 단계의 입력과 출력, 확인해야 할 조건이 무엇인지 설명하겠습니다. 도식의 상자는 실제 실험 결과나 새로운 구성요소를 추가한 것이 아니라 기존 구현과 분석 흐름을 요약한 것입니다.',layout='figure',**diagram),
         slide(story[2][0],story[2][1],story[2][2]),
         pictured(images[1]) if len(images)>1 else slide('구현과 검증을 나눠 보겠습니다',digest.get('did',[])[:3],'구현했다고 주장할 수 있는 범위와 별도 평가가 필요한 범위를 나누겠습니다. '+story[2][2]),
         slide(story[3][0],story[3][1],story[3][2]),
         pictured(images[2]) if len(images)>2 else slide('그림이 설명하는 것과 설명하지 못하는 것',['개별 화면·사례는 전체 성능의 근거가 아님','검증 조건과 추가 확인 과제를 함께 설명'],story[3][2]+' '+story[4][2]),
         slide(story[4][0],story[4][1],story[4][2]),
         slide('이 경험을 다음 업무에 연결하는 방법',['데이터의 생성 조건을 먼저 확인','선택의 근거를 남기고 다른 기준으로 검증','확인한 성과와 다음 과제를 구분'], '이 경험에서 다른 업무로 가져가고 싶은 것은 특정 도구 이름보다 판단하는 순서입니다. 먼저 입력 자료의 생성 조건과 제한을 이해하고, 방법을 선택한 이유를 남기고, 독립된 기준으로 결과를 확인하겠습니다. 새로운 환경에서도 같은 결과가 나올지는 별도로 검증해야 하므로 연구·프로젝트 성과를 곧바로 현장 운영 성과로 표현하지 않겠습니다.'),
         {'t':'end','h':'질문을 받겠습니다','sub':'역할 · 판단 기준 · 평가 조건 · 다음 검증','note':'이상으로 문제와 구현, 결과와 한계를 설명했습니다. 질문을 주시면 제가 직접 담당한 범위와 원자료에서 확인할 수 있는 근거를 기준으로 답변하겠습니다. 확인되지 않은 세부 내용은 추정해서 답하지 않고 자료를 확인하겠습니다. 감사합니다.'}]
        # Add non-overlapping original retrospective passages to the speaker notes.
        # This expands substance, not timers or blank pauses. Keep each passage intact.
        pool=list(blocks);cursor=0;total=sum(len(s.get('note',''))for s in slides)
        while total<2450 and cursor<len(pool):
            block=pool[cursor];slot=2+(cursor%10);cursor+=1
            if total+len(block)>3450:continue
            slides[slot]['note']+='\n\n조금 더 구체적으로 설명드리겠습니다. '+block;total+=len(block)+15
        if total<2050:
            for row in story:
                extra='이 지점에서 확인할 질문은 다음과 같습니다. '+row[0]+'라는 설명을 뒷받침하는 입력 자료와 비교 기준이 무엇인지, 실제로 제가 담당한 범위가 어디까지인지 구분해 답변하겠습니다. '+row[2]
                if total>=2200:break
                slides[10]['note']+='\n\n'+extra;total+=len(extra)
        # Preserve exact metric labels; never turn BERTScore into accuracy.
        metric={'posco-pospeak':('pospeak-score','BERTScore F1 · 학습 전략 비교','BERTScore F1은 의미 유사도 지표이며 교정 정확도가 아닙니다.'),'data-projects':('power-mape','전력 수요 MAPE · 기준선과 비교','서로 다른 문제의 지표를 합치지 않습니다. 낮을수록 좋은 MAPE 지표입니다.')}.get(pid)
        if metric:
            img,caption,warning=metric
            slides.insert(9,slide(caption,[],warning+' '+story[3][2],layout='figure',img='../assets/presentation/'+img+'.svg',caption=caption,credit='수치: 공개 포트폴리오 · 그래프 재구성',image_source=common))
        for s in slides:
            s['seconds']=max(15,round(len(s.get('note',''))/6.5));s['source_url']=common
        d={'id':pid,'title':title+' · 5~10분','kind':'project','min':8,'revision':REVISION,'slides':slides,'sources':[{'title':'프로젝트 원문','url':common}]+sources,'verify':'기존 공개 자료·회고를 바탕으로 확장했습니다. 참고 사진·재구성 도식·실제 결과 그림을 구분해 표시했습니다. 시간은 대본 글자 수 기준 추정이며 실제 속도로 연습하세요.'}
        d['estimated_seconds']=round(sum(len(s.get('note',''))for s in slides)/6.5);project_decks[pid]=d;decks.append(d)
    result=[]
    for role,v in variants.items():
        for kind,pids in [('intro',['data-projects','masters']if role=='data'else['posco-pospeak','ssafy-16']),('role',['data-projects','ssafy-16']if role=='data'else['ssafy-16','posco-pospeak'])]:
            available=[project_decks[p] for p in pids if p in project_decks]
            if not available:continue
            label=v.get('label',role);slides=[{'t':'title','h':name+' · '+label,'kicker':'5~10분 경험 소개'if kind=='intro'else'5~10분 직무 발표','sub':'문제에서 출발해 검증 가능한 결과로 연결한 경험','note':f'안녕하세요. {label} 직무를 준비하는 {name}입니다. 두 가지 경험을 통해 제가 문제를 이해하고 결과를 검증하는 방식을 설명하겠습니다. 특정 기술을 사용했다는 사실뿐 아니라 어떤 기준으로 선택했고 어디까지 확인했는지 보여 드리겠습니다.'}]
            for d in available:
                for j in (2,4,5,6,8,10):
                    s=dict(d['slides'][j]);s['kicker']=d['title'].replace(' · 5~10분','');slides.append(s)
            slides.append({'t':'end','h':'입력의 조건과 결과의 근거를 함께 보겠습니다','sub':'직무·회사별 마지막 문장은 직접 수정할 수 있습니다.','note':'두 경험은 자료의 조건을 이해하고, 판단 기준을 남기고, 결과와 한계를 함께 설명한다는 공통점이 있습니다. 입사 후에도 업무의 기준을 익힌 뒤 작은 개선부터 검증하고 싶습니다. 이 계획은 지원 회사의 실제 업무와 데이터 권한에 맞춰 구체화하겠습니다. 감사합니다.'})
            duration=round(sum(len(s.get('note',''))for s in slides)/6.5)
            # The selected substantive excerpts must themselves reach five minutes.
            if duration<305:
                for source in available:
                    s=dict(source['slides'][7]);slides.insert(-1,s);duration=round(sum(len(x.get('note',''))for x in slides)/6.5)
                    if duration>=305:break
            for s in slides:s['seconds']=max(15,round(len(s.get('note',''))/6.5))
            result.append({'id':kind+'-'+role,'title':('경험 소개'if kind=='intro'else'직무 발표')+' · '+label+' · 5~10분','kind':kind,'role':role,'min':8,'revision':REVISION,'slides':slides,'estimated_seconds':duration,'sources':[x for d in available for x in d['sources']],'verify':'두 프로젝트의 공개 자료로 구성한 경험·직무 발표입니다. 자기평가와 포부는 제안이며 본인의 지원 의사에 맞게 수정하세요.'})
    return result+decks
