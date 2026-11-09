# 채용 플랫폼 프로필 문구 (LinkedIn · 원티드 · 리멤버)

data/portfolio.yaml에서 자동 생성됩니다. 각 칸에 그대로 복사해 붙여넣으세요.
LinkedIn 경력 설명은 2,000자 제한이 있어서, 묶음 활동은 하위 프로젝트마다 칸을 나누고 핵심 문장만 넣었습니다.

## 1. 한 줄 소개 (LinkedIn 헤드라인, 220자 이내)

```
Data & AI Engineer | M.S. (SCIE first author) · Spatiotemporal deep learning · LLM fine-tuning & RAG · Data pipelines
```

## 2. 자기소개 / About

```
M.S. in Environment and Energy (Jeonbuk National University, 2026) with a B.S. in Mineral Resources and Energy Engineering. As an undergraduate researcher I wrote a first-author paper interpreting seismic images of large overseas CO2 storage sites in light of plate-tectonic history, and in the IAB convergence-major capstone I designed and trained a spatiotemporal deep learning model (U-LSTM) that predicts wildfire spread. In my master's I separated overlapping gravity and magnetic signals with wavenumber-domain correlation analysis and published a first-author paper in SPE Journal (SCIE); across both degrees: 3 papers, 6 conference presentations and a best student paper award. At the POSCO Youth AI & Big Data Academy (with POSTECH) I built the training data and ran model experiments for an English expression correction system (FLAN-T5 + RAG) that won an Excellence Award, and at the Samsung Software & AI Academy for Youth (SSAFY) I am building LLM data pipelines and multimodal model ensembles. Two research stays at the University of Calgary; ADsP (Advanced Data Analytics Semi-Professional) certified.

My flagship SSAFY project is a heritage Q&A RAG guide — from collecting the Korea Heritage Service open API to an LLM whose citations are re-checked in code (github.com/0Ju12/heritage-rag-guide).

Looking for: Data Engineer · AI/ML Engineer · Available: H1 2027 · Location: Open to any location

Portfolio: https://0ju12.github.io  (English: https://0ju12.github.io/en.html)
GitHub: https://github.com/0Ju12
Research history: https://www.geoverselab.com/ko/research-history/13/
```

## 3. 경력·활동 항목 (칸 하나씩)

### SSAFY — ThRead LLM comment-analysis pipeline · AI Challenge VQA ensemble
- **직함/역할:** Backend & data pipeline · model training (AI Challenge)
- **회사/기관:** Samsung Software & AI Academy for Youth (SSAFY) · team of 2
- **기간:** 2026.07 – present
- **설명:**
```
Extended a reading-community service across seven projects, from data collection to LLM analysis and web service, plus a multimodal QA challenge
• Comment pipeline: Selenium collects live comments → the LLM returns only the numbers of inappropriate comments and code removes them → pandas/regex cleaning → IQR length thresholds → LLM augmentation (retry on count mismatch) → summary, each step stored
• Streamed progress of 30-second jobs with StreamingHttpResponse (NDJSON) and distinguished failure cases (no company, no comments, LLM failure)
• Relational DB design (project 6): custom AbstractUser; user→book→thread→comment 1:N plus follow (asymmetric), like and favorite-genre M:N; migrations split in three steps to avoid a User↔Category cycle; owner-scoped lookups return 404 for other users' posts; Aladin search results passed through a signed, 1-hour token so ISBN/cover are saved only when title and author still match — 36 tests
• AI proxy server (project 7, FastAPI owner): Django → FastAPI → GMS so keys, model choice and output checks live in one place; JSON-Schema guardrail that fails closed (503) on malformed output; text/image routing and nano/mini model tiers; four Gemini image response shapes normalized to real JPEG; 20 tests
✔ AI Challenge public score 0.94608 (4B baseline) → 0.96961
✔ 142 automated tests passing (45 + 41 + 36 + 20); all project-5 requirements implemented, plus progress streaming and analysis history
Skills: Python, Django, Selenium, Pandas, LLM API
Details: https://0ju12.github.io/projects/ssafy-16-en.html
```

### POSPEAK (KILL KONG) — Konglish → natural English correction AI (FLAN-T5 · Qwen + RAG)
- **직함/역할:** Dataset building & model experiments
- **회사/기관:** POSCO Youth AI & Big Data Academy (with POSTECH) · team project
- **기간:** 2025.06 – 2025.08
- **설명:**
```
A generator plus retrieval (RAG) that rewrites awkward or Konglish sentences into natural English
• [Own] Built and cleaned word-level and context-level correction pairs
• [Own] Fine-tuned FLAN-T5 with LoRA and compared three strategies (word→context, context→word, joint) with BERTScore
• [Final service KILL KONG] Qwen-2.5 (1.5B) fine-tuning + a 630-entry Konglish RAG DB + per-user memory, combined with LangChain in a React Native · FastAPI app
✔ Found catastrophic forgetting in sequential training (BERTScore F1 0.47 → 0.32) and switched to joint training
✔ Joint training reached validation BERTScore F1 ≈ 0.74 · team Excellence Award
Skills: Python, Hugging Face, FLAN-T5, LoRA, RAG, FAISS
Details: https://0ju12.github.io/projects/posco-pospeak-en.html
```

### Wavenumber correlation of gravity & magnetic data for salt/basement structure (M.S. · SPE Journal first author)
- **직함/역할:** Graduate researcher
- **회사/기관:** Geophysical Computing Lab · Dept. of Environment and Energy
- **기간:** 2024.03 – 2026.08
- **설명:**
```
Separated overlapping gravity and magnetic signals in the wavenumber domain to resolve salt and basement structures offshore Abu Dhabi
• Built a wavenumber correlation filtering (WCF) pipeline — upward continuation and normalization, then the correlation coefficient CC(k) between the two signals at each wavenumber
• Designed two indices — SLFI from positively correlated components (basement) and DLFI from weak/negative ones (salt)
• Chose thresholds from energy–correlation trade-off curves instead of by eye (upward continuation 1,500 m at the knee point; SLFI band 0.5–1.0 keeps ~half the energy at correlation 0.85)
• Validated against three independent published models with map, profile and 3-D density comparisons
✔ SLFI basement structure agrees with three independent models at r ≥ 0.94 (profile correlation 0.95–0.98 after shift alignment)
✔ DLFI reproduces the salt distribution and suggests an additional salt uplift west of Ghasha
✔ First-author paper in SPE Journal (SCIE, 2026, with Univ. of Calgary and Khalifa Univ.) · 3 conference talks (2024)
✔ M.S. degree conferred 2026.08.21
Skills: Signal processing, Correlation analysis, Index design, Gravity & magnetic data
Details: https://0ju12.github.io/projects/masters-en.html
```

### Research stay at the University of Calgary — joint interpretation of gravity & magnetic data
- **직함/역할:** Visiting graduate researcher
- **회사/기관:** University of Calgary
- **기간:** 2024.06 – 2024.12
- **설명:**
```
Combined gravity and magnetic surveys to characterize the Ghasha salt dome and basement
• Funded by the MSIT/IITP Global Talent program in digital fields (AI & digital-twin smart CCS)
• Worked with the Department of Geomatics Engineering on wavenumber correlation of airborne gravity and magnetic data
• Extended the work into a 3-institution collaboration with Khalifa University (UAE)
• Joined a field geophysical survey in Kananaskis (Canadian Rockies) and co-wrote the English Field Exploration Report (2024.08)
✔ Led to the first-author SPE Journal paper (SCIE, 2026) and the M.S. thesis
Skills: Gravity & magnetic data, Joint interpretation, International collaboration
Details: https://0ju12.github.io/projects/calgary-2024-en.html
```

### Seismic interpretation of large overseas CO2 storage sites considering plate-tectonic history (first-author paper)
- **직함/역할:** Undergraduate researcher · first author
- **회사/기관:** Geophysical Computing Lab (undergraduate researcher)
- **기간:** 2022 – 2024.02
- **설명:**
```
Reconstructed how large overseas CO2 storage sites formed and interpreted their seismic images from a structural-geology perspective
• Reconstructed the plate-tectonic history of four regions with GPlates (PALEOMAP PaleoAtlas)
• Interpreted seismic images of two representative CCS projects per region — Quest & Weyburn-Midale, Northern Lights & PORTHOS, Gorgon & Moomba, Uthmaniyah & Qatar LNG — focusing on reservoir and cap rock
• Short stay at Univ. of Calgary (2023.12–2024.02): processed gravity data from the Utah FORGE geothermal site → poster at the KSEG Spring Conference 2024
✔ First-author paper: Analysis on Seismic Interpretation for Overseas Large-scale CO2 Storage Considering Geological History Related to Plate Tectonics, Geophysics and Geophysical Exploration 27(1), 1–22 (2024)
✔ Showed that stratigraphy in each seismic image reflects the region's tectonic history → a basis for rejecting geologically unrealistic velocity models when processing domestic data
✔ 1 second-author paper (CarbonNet CCS, Gippsland Basin, 2023) · 3 conference talks (2022–2023)
✔ Best Student Paper Award (poster), KSEG Spring Conference 2024 — accuracy of seismic velocity and density models at the Utah FORGE site
Skills: Seismic interpretation, GPlates, Plate reconstruction, CCS
Details: https://0ju12.github.io/projects/undergrad-research-en.html
```

### IAB capstone — Wildfire spread prediction with spatiotemporal deep learning
- **직함/역할:** Model design & training
- **회사/기관:** Jeonbuk National University · IAB convergence major
- **기간:** 2023.09 – 2023.12
- **설명:**
```
A U-LSTM that predicts the next wildfire front from the current front, weather and terrain
• Rasterized fire fronts from Korea Forest Service maps plus wind, NDVI and elevation in ArcGIS for four large fires (3 for training, 1 held out)
• Designed a shallow U-LSTM (2,736 parameters) to fit the small dataset (4 fires, 35 time steps)
• Expanded the sequences with sliding windows (length 1–19) into 151 training batches; evaluated with Overall Accuracy and F1
✔ Unseen fire (Gangneung): Accuracy 0.90 · F1 0.85 (validation 0.95 · 0.81)
✔ Refactored the team notebooks into a tested Python package and documented the limitations on GitHub
Skills: Python, TensorFlow, PyTorch, U-LSTM, ArcGIS
Details: https://0ju12.github.io/projects/wildfire-capstone-en.html
```

## 4. 논문·발표 (LinkedIn "Publications")
- Wavenumber Correlation of Gravity and Magnetic Anomalies for Constraining Salt/Basement Structure in Offshore Abu Dhabi (SPE Journal (SCIE) · first author, 2026) — https://doi.org/10.2118/236968-PA
- Analysis on Seismic Interpretation for Overseas Large-scale CO2 Storage Considering Geological History Related to Plate Tectonics (Geophysics and Geophysical Exploration 27(1), 1–22 · first author (in Korean), 2024) — https://koreascience.or.kr/article/JAKO202410348585789.page
- Geological Analysis of the CarbonNet CCS Project in the Gippsland Basin, Australia (Geophysics and Geophysical Exploration · second author (in Korean), 2023) — https://koreascience.or.kr/article/JAKO202335272000266.page
- [학회 발표] A global talent program for smart CO2 storage operation through AI and digital-twin convergence (2024)
- [학회 발표] Status of overseas CCS demonstration projects and strategy for international collaboration (2024)
- [학회 발표] A global talent program for smart CO2 geological storage site operation (2024)
- [학회 발표] Geophysical monitoring case analysis of Sleipner, Norway, and international collaboration plan (2023)
- [학회 발표] Deep-learning seismic imaging research in Saudi Arabia and international collaboration plan (2023)
- [학회 발표] Applicability of GPU-based 4D seismic monitoring (2022)

## 5. 스킬 (LinkedIn Skills — 최대 50개, 상위 5개가 프로필에 노출)

```
Python, TensorFlow, PyTorch, Hugging Face Transformers, Pandas, Django, Selenium, SQL, Spatiotemporal DL (U-LSTM), LLM fine-tuning (LoRA/QLoRA), Model ensembles, RAG (LangGraph · ChromaDB · FAISS), F1 · BERTScore, ArcGIS, Rasters, Gravity & magnetics, Wavenumber correlation, Seismic interpretation, GPlates, CCS, Energy & resources, Wildfire prediction
```

## 6. 수상·자격 (LinkedIn "Honors & awards" / "Licenses & certifications")
- Project Excellence Award, POSCO Youth AI & Big Data Academy (30th) — POSCO HRD Center · POSTECH (2025.08)
- Best Student Paper Award (poster), KSEG Spring Conference 2024 — Korean Society of Earth and Exploration Geophysicists (2024.10)
- ADsP (Advanced Data Analytics Semi-Professional) — Korea Data Agency (2022.09)
