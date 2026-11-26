"""Reproducible explanatory diagrams; no simulated experimental results."""
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets/presentation'
FLOWS={
 'masters':('WCF · 신호 분리 과정',['중력·자력 입력','상향 연속·정규화','파수 상관 CC(k)','SLFI · DLFI','독립 모델 비교']),
 'calgary-2024':('서로 다른 물리량을 비교하는 순서',['생성 조건 확인','단위·감도 차이','정규화','파수 영역 비교','해석·추가 검증']),
 'undergrad-research':('형성사와 현재 구조를 함께 해석',['4개 지역·8개 사례','GPlates 복원','저장층·덮개암','탄성파 해석','공통점·한계 비교']),
 'wildfire-capstone':('원래 구현과 회고에서 확인한 한계',['300×300 입력','Conv2D: 75×75','공간축 5,625 시퀀스','LSTM 처리','300×300 예측']),
 'posco-pospeak':('교정 데이터와 모델 비교 과정',['교정 데이터 구축','정제·학습 분할','LoRA 전략 비교','BERTScore 평가','RAG·오답노트']),
 'portfolio-site':('원본 한 곳에서 여러 결과물로',['YAML 원본','Python·Jinja','웹·이력서·문서','링크·레이아웃 검사','GitHub Pages']),
 'prep-apps':('잠긴 배포 자료와 개인 기록의 경계',['원자료·질문','암호화 빌드','잠금 해제','브라우저에 편집 저장','파일 백업·복구']),
 'hankki':('모델은 해석, 판정은 코드',['상황 문장','분석·계획(모델+규칙)','실행·판정(코드)','재계획 ≤3회','확인된 값으로 응답']),
 'data-projects':('수집 이후의 변경과 품질을 추적',['공개 API 수집','원본·수정 이력','dbt 정제·집계','품질 검사','DAG 실행·대시보드']),
}
def build():
 OUT.mkdir(parents=True,exist_ok=True)
 for key,(title,steps) in FLOWS.items():
  svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="760" viewBox="0 0 1440 760"><rect width="1440" height="760" fill="#f4f7fb"/>',f'<text x="70" y="100" font-family="sans-serif" font-size="38" font-weight="700" fill="#132940">{escape(title)}</text>','<text x="70" y="148" font-family="sans-serif" font-size="22" fill="#607083">포트폴리오·회고 원문에 근거해 재구성한 개념도 · 실제 측정 그래프 아님</text>']
  for i,label in enumerate(steps):
   x=70+i*270;y=280
   svg.append(f'<rect x="{x}" y="{y}" width="235" height="210" rx="18" fill="'+('#132940' if i%2==0 else '#e4ebf3')+'"/>')
   svg.append(f'<text x="{x+25}" y="{y+55}" font-family="sans-serif" font-size="24" fill="#c48c3b">0{i+1}</text>')
   # two lines on a word boundary, preserving the technical label
   words=label.split();mid=max(1,len(words)//2);lines=[' '.join(words[:mid]),' '.join(words[mid:])]
   for j,line in enumerate(lines):svg.append(f'<text x="{x+25}" y="{y+110+j*36}" font-family="sans-serif" font-size="24" font-weight="700" fill="'+('#fff' if i%2==0 else '#132940')+'">'+escape(line)+'</text>')
   if i<4:svg.append(f'<path d="M{x+242} {y+105}h20m-8-8 8 8-8 8" fill="none" stroke="#c48c3b" stroke-width="4"/>')
  svg.append('<text x="70" y="650" font-family="sans-serif" font-size="22" fill="#607083">입력의 조건 → 처리의 책임 → 평가의 범위를 구분해 설명합니다.</text></svg>')
  (OUT/(key+'-flow.svg')).write_text(''.join(svg),encoding='utf-8')
 # Metric comparisons are separate panels: never equate unrelated datasets or metrics.
 import os
 os.environ.setdefault('MPLCONFIGDIR','/tmp/portfolio-matplotlib')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 for key,labels,values,title,note in [
  ('pospeak-score',['Sequential','Combined'],[.32,.74],'BERTScore F1 · learning strategy','Semantic-similarity metric, not correction accuracy.'),
  ('power-mape',['Last-week baseline','Ensemble'],[6.17,3.23],'Power demand · MAPE (%)','Lower is better. Reported project test period only.'),
  ('sensor-split',['Random split','Time-series CV (5 folds)'],[.99,.81],'Sensor diagnosis · valve accuracy (RandomForest)','Different evaluation splits, not a model improvement. LDA holds 0.99 under the same CV.'),
 ]:
  fig,ax=plt.subplots(figsize=(12,5.6));fig.patch.set_facecolor('#f4f7fb');ax.set_facecolor('#f4f7fb');bars=ax.barh(labels,values,color=['#95a8bb','#c48c3b'],height=.45)
  ax.set_xlim(0,max(values)*1.35);ax.invert_yaxis();ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0,labelsize=15);ax.set_title(title,loc='left',fontsize=20,fontweight='bold',pad=28,color='#132940')
  for bar,v in zip(bars,values):ax.text(v+max(values)*.03,bar.get_y()+bar.get_height()/2,str(v),va='center',fontsize=20,fontweight='bold',color='#132940')
  fig.text(.02,.025,note,fontsize=11,color='#52657b');fig.tight_layout(rect=(0,.06,1,1));fig.savefig(OUT/(key+'.svg'),format='svg');plt.close(fig)
if __name__=='__main__':build()
