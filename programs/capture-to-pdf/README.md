# CaptureToPDF — 화면 영역 캡처 → PDF 도구

강의 자료·뷰어 화면처럼 **넘겨 가며 보는 자료를 한 장씩 캡처해 목차가 있는 PDF로 묶는** 데스크톱 도구입니다. 공부 자료를 정리하려고 직접 만들었습니다. (Windows / macOS, Python · Tkinter)

## 사용 흐름
1. **영역 지정** — 캡처할 영역을 드래그 (자주 쓰는 영역은 프리셋으로 저장)
2. 페이지를 넘기면서 **F8** (전역 단축키) 또는 [캡처] 버튼
3. 필요한 페이지에 **목차 제목·메모** 입력, 썸네일을 드래그해 순서 변경
4. 파일 이름 입력 → **PDF로 저장**
5. [새 PDF] → 같은 영역으로 다음 자료를 이어서 캡처

## 주요 기능
- **목차(북마크) PDF**: 페이지별 제목을 PDF 북마크로 넣어 바로 이동 (`pikepdf` outline)
- **검색 가능한 PDF (선택)**: Tesseract가 설치돼 있으면 OCR 텍스트 레이어 추가
- **여러 장 모아 찍기(N-up)**, JPEG 압축 옵션으로 용량 조절
- **자동 영역 맞춤**: 여백 색을 기준으로 실제 내용 영역만 잘라내기
- **중복 캡처 방지**: 이미지 해시(MD5)로 직전 페이지와 같은 화면이면 건너뜀
- **세션 저장·복원**: 캡처 이미지와 순서·목차·메모를 폴더(`pages.json`)에 저장해 다시 불러오기
- 고해상도(125%·150% 배율) 화면 좌표 보정, 삭제 되돌리기

## 실행
```bash
pip install mss img2pdf pikepdf pynput
python capture_to_pdf.py
```
Windows 실행 파일(.exe)은 `build_exe.bat`로 만들 수 있습니다 (PyInstaller).

## 기술
Python · Tkinter · mss(화면 캡처) · Pillow · img2pdf · pikepdf · pynput(전역 단축키) · pytesseract(OCR, 선택) · PyInstaller
