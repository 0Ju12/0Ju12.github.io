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
    from presentation_long import long_decks
    return long_decks(data,variants,projects)
