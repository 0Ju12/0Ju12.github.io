"""Render real public portfolio data only; optional production PPTX library for exports."""
import argparse,json,sys,urllib.request
from pathlib import Path
import yaml
from jinja2 import Environment,FileSystemLoader
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import interview
from career_content import prepare_essays

def render(with_library=False):
    data=yaml.safe_load((ROOT/'data/portfolio.yaml').read_text())
    data['case_notes']=yaml.safe_load((ROOT/'data/case_notes.yaml').read_text())
    variants=yaml.safe_load((ROOT/'data/resume_variants.yaml').read_text())
    prep=yaml.safe_load((ROOT/'data/prep.yaml').read_text());prep['essays']=prepare_essays(prep,data)
    app={'name':data['profile']['name'],'roles':{k:v['label']for k,v in variants.items()},'cats':interview.CATS,'questions':[{'id':'fixture','q':'검증 질문','a':'검증 답변','g':'검증','c':'인성'}],'decks':interview.decks(data,variants),'prep':prep,'metadata':{'version':'illustrated-qa','sources':[]}}
    target=ROOT/'work/illustrated';target.mkdir(parents=True,exist_ok=True)
    (target/'index.html').write_text(Environment(loader=FileSystemLoader(ROOT/'templates')).get_template('interview.html.j2').render(app=app,profile=data['profile']))
    (target/'decks.json').write_text(json.dumps(app['decks'],ensure_ascii=False))
    if with_library:
        request=urllib.request.Request('https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js',headers={'User-Agent':'portfolio-presentation-qa'})
        with urllib.request.urlopen(request,timeout=60)as response:(target/'pptxgen.bundle.js').write_bytes(response.read())
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--library',action='store_true');render(parser.parse_args().library)
