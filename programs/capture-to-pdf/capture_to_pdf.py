"""
화면 영역 캡처 → PDF 도구 (Windows / macOS)

설치:  pip install mss img2pdf pikepdf pynput
       (검색 가능한 PDF를 원하면 추가로: pip install pytesseract + Tesseract 설치)
실행:  python capture_to_pdf.py

1) [영역 지정] → 캡처할 영역을 드래그 (Esc: 취소)
2) 페이지를 넘기면서 F8 (또는 [캡처] 버튼)
3) 필요하면 페이지마다 목차 제목·메모 입력
4) 파일 이름 입력 → [PDF로 저장]
5) [새 PDF] → 같은 영역으로 다음 자료를 이어서 캡처

캡처 이미지는 이 프로그램 옆의 Capture 폴더에 세션별로 저장됩니다.
"""
import ctypes
import hashlib
import io
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# 고해상도(배율 125%, 150% 등) 화면에서 좌표가 어긋나지 않도록 DPI 인식 설정
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import mss
import mss.tools
import img2pdf
import pikepdf
from PIL import Image, ImageChops, ImageDraw, ImageTk

try:
    from pynput import keyboard
except ImportError:  # 단축키 없이 버튼만으로도 동작
    keyboard = None
try:
    import pytesseract
except ImportError:  # OCR은 선택 기능
    pytesseract = None

HOTKEY = "<f8>"
if getattr(sys, "frozen", False):  # exe로 묶었을 때는 exe 옆에 저장
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURE_ROOT = os.path.join(BASE_DIR, "Capture")
SETTINGS_PATH = os.path.join(BASE_DIR, "capture_settings.json")
PAGES_JSON = "pages.json"
TRASH_DIR = ".trash"
IMG_EXT = (".png", ".jpg", ".jpeg")

NUP_CHOICES = {"안 함": 0, "2쪽씩": 2, "4쪽씩": 4, "6쪽씩": 6}
NUP_LAYOUT = {2: (1, 2, False), 4: (2, 2, True), 6: (2, 3, False)}  # 열, 행, A4 가로 여부

DEFAULTS = {
    "region": None,
    "save_dir": "",
    "autofit": True,
    "jpeg": False,
    "ocr": False,
    "nup": "안 함",
    "sound": True,
    "topmost": True,
    "geometry": "1180x760",
    "presets": {},
}

SHORTCUTS = [
    ("F8", "캡처 (다른 창에서도 동작)"),
    ("← / →", "페이지 넘겨 보기"),
    ("Ctrl + ← / →", "선택한 페이지 순서 이동"),
    ("Delete", "선택한 페이지 삭제"),
    ("Ctrl + Z", "삭제 되돌리기"),
    ("Ctrl + S", "PDF로 저장"),
    ("드래그", "아래 목록에서 썸네일을 끌어 순서 변경"),
]

# ---------- 디자인 ----------
C = {
    "bg": "#16181d",
    "panel": "#1b1e24",
    "card": "#20232b",
    "card2": "#2a2e38",
    "line": "#323744",
    "text": "#e9ebf0",
    "sub": "#9aa1b1",
    "dim": "#6b7280",
    "primary": "#5b8cff",
    "primary_h": "#7aa2ff",
    "accent": "#22c55e",
    "accent_h": "#3ad574",
    "danger": "#f05252",
    "danger_h": "#f47272",
    "warn": "#f5b942",
}
if sys.platform == "win32":
    FONT = "Malgun Gothic"
elif sys.platform == "darwin":
    FONT = "Apple SD Gothic Neo"
else:
    FONT = "Noto Sans CJK KR"


def F(size, weight="normal"):
    return (FONT, size, weight)


# =====================================================================
# 이미지 / PDF 처리 (UI와 무관 → 백그라운드 스레드에서 실행 가능)
# =====================================================================
def md5_file(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def content_bbox(im, tol=24):
    """가장자리 배경색(네 모서리 중 가장 흔한 색)과 다른 부분의 경계 상자"""
    w, h = im.size
    corners = [im.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    bg = max(set(corners), key=corners.count)
    diff = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L")
    return diff.point(lambda p: 255 if p > tol else 0).getbbox()


def detect_ocr():
    """(언어 문자열 또는 None, 안내 메시지)"""
    if pytesseract is None:
        return None, "pytesseract 미설치"
    if sys.platform == "win32":
        for p in (r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                  r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break
    try:
        pytesseract.get_tesseract_version()
        langs = set(pytesseract.get_languages(config=""))
    except Exception:
        return None, "Tesseract 미설치"
    if "kor" in langs:
        return ("kor+eng" if "eng" in langs else "kor"), ""
    if "eng" in langs:
        return "eng", "한국어 데이터 없음 · 영어만 인식"
    return None, "언어 데이터 없음"


def build_pdf(pages, out_path, jpeg, ocr_lang, nup, progress):
    """pages: [{"path","title","memo"}] → PDF 저장. 결과 정보를 dict로 반환"""
    n = len(pages)

    # 1) 이미지 → PDF 페이지 (기본 무손실 PNG, 옵션이면 더 작은 쪽 선택)
    progress("이미지를 PDF로 묶는 중…")
    imgs = []
    for p in pages:
        src = p["path"]
        if jpeg:
            with Image.open(src) as im:
                buf = io.BytesIO()
                im.convert("RGB").save(buf, "JPEG", quality=92, optimize=True)
            data = buf.getvalue()
            imgs.append(data if len(data) < os.path.getsize(src) else src)
        else:
            imgs.append(src)
    pdf = pikepdf.open(io.BytesIO(img2pdf.convert(imgs)))
    keep = []  # 오버레이 원본 PDF는 저장할 때까지 열어둬야 함

    # 2) OCR: 보이지 않는 글자 층을 덧입혀 검색·복사 가능하게
    if ocr_lang:
        for i, p in enumerate(pages):
            progress(f"글자 인식 중… {i + 1}/{n}")
            with Image.open(p["path"]) as im:
                txt = pytesseract.image_to_pdf_or_hocr(
                    im.convert("RGB"), lang=ocr_lang, extension="pdf",
                    # psm 4: 크기가 제각각인 글줄이 위에서 아래로 놓인 화면(강의 슬라이드)에 가장 잘 맞음
                    config="--dpi 96 --psm 4 -c textonly_pdf=1")
            tp = pikepdf.open(io.BytesIO(txt))
            keep.append(tp)
            target = pdf.pages[i]
            target.add_overlay(tp.pages[0], pikepdf.Rectangle(target.mediabox))

    # 3) 목차(북마크)
    titled = [(i, p["title"]) for i, p in enumerate(pages) if p.get("title")]
    if titled:
        with pdf.open_outline() as ol:
            for i, t in titled:
                ol.root.append(pikepdf.OutlineItem(t, i))
        pdf.Root.PageMode = pikepdf.Name.UseOutlines

    # 4) 페이지 메모 → PDF 메모(스티커) 주석
    memos = 0
    for i, p in enumerate(pages):
        memo = (p.get("memo") or "").strip()
        if not memo:
            continue
        pg = pdf.pages[i]
        r = pikepdf.Rectangle(pg.mediabox)
        annot = pdf.make_indirect(pikepdf.Dictionary(
            Type=pikepdf.Name.Annot, Subtype=pikepdf.Name.Text,
            Rect=[r.urx - 30, r.ury - 30, r.urx - 8, r.ury - 8],
            Contents=pikepdf.String(memo), T=pikepdf.String("메모"),
            Name=pikepdf.Name.Comment, C=[1, 0.8, 0.2], F=4, Open=False,
        ))
        if "/Annots" in pg.obj:
            pg.obj.Annots.append(annot)
        else:
            pg.obj.Annots = pdf.make_indirect(pikepdf.Array([annot]))
        memos += 1

    progress("PDF 저장 중…")
    pdf.save(out_path)
    pdf.close()
    for tp in keep:
        tp.close()
    result = {"path": out_path, "pages": n, "titles": len(titled), "memos": memos,
              "ocr": bool(ocr_lang), "nup_path": None}

    # 5) 인쇄용 모아찍기
    if nup:
        progress(f"인쇄용 {nup}쪽 모아찍기 만드는 중…")
        root, _ = os.path.splitext(out_path)
        nup_path = f"{root}_인쇄용_{nup}쪽.pdf"
        make_nup([p["path"] for p in pages], nup, nup_path)
        result["nup_path"] = nup_path
    return result


def make_nup(paths, nup, out_path, dpi=200):
    cols, rows, landscape = NUP_LAYOUT[nup]
    W, H = (2339, 1654) if landscape else (1654, 2339)  # A4 @200dpi
    margin, gap = int(dpi * 0.4), int(dpi * 0.2)
    cw = (W - 2 * margin - (cols - 1) * gap) // cols
    ch = (H - 2 * margin - (rows - 1) * gap) // rows
    sheets = []
    for s in range(0, len(paths), nup):
        sheet = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(sheet)
        for k, p in enumerate(paths[s:s + nup]):
            r, c = divmod(k, cols)
            x, y = margin + c * (cw + gap), margin + r * (ch + gap)
            with Image.open(p) as im:
                im = im.convert("RGB")
            sc = min(cw / im.width, ch / im.height)
            im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
            ox, oy = x + (cw - im.width) // 2, y + (ch - im.height) // 2
            sheet.paste(im, (ox, oy))
            d.rectangle([ox - 1, oy - 1, ox + im.width, oy + im.height], outline="#bbbbbb")
        buf = io.BytesIO()
        sheet.save(buf, "JPEG", quality=90, dpi=(dpi, dpi))
        sheets.append(buf.getvalue())
    mm = img2pdf.mm_to_pt
    size = (mm(297), mm(210)) if landscape else (mm(210), mm(297))
    with open(out_path, "wb") as f:
        f.write(img2pdf.convert(sheets, layout_fun=img2pdf.get_layout_fun(size)))


# =====================================================================
# UI
# =====================================================================
class FlatButton(tk.Label):
    """OS와 상관없이 같은 모양으로 보이는 평면 버튼 (macOS의 tk.Button은 배경색을 무시함)"""

    def __init__(self, master, text, command, bg, hover, fg="#ffffff", size=10, bold=True, pady=8, **kw):
        super().__init__(master, text=text, bg=bg, fg=fg, cursor="hand2",
                         font=F(size, "bold" if bold else "normal"), padx=10, pady=pady, **kw)
        self._bg, self._hover, self._fg, self._cmd = bg, hover, fg, command
        self._enabled = True
        self.bind("<Enter>", lambda e: self._enabled and self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg if self._enabled else C["card2"]))
        self.bind("<ButtonRelease-1>", self._click)

    def _click(self, e):
        if self._enabled and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self._cmd()

    def set_enabled(self, on):
        self._enabled = on
        self.config(bg=self._bg if on else C["card2"],
                    fg=self._fg if on else C["dim"],
                    cursor="hand2" if on else "arrow")


class App:
    SIDEBAR_W = 310
    STRIP_H = 100     # 아래 페이지 목록 높이
    STRIP_THUMB = 70  # 목록 썸네일 높이

    def __init__(self):
        self.cfg = self._load_settings()
        self.ocr_lang, self.ocr_note = detect_ocr()

        self.root = tk.Tk()
        self.root.title("캡처 → PDF")
        self.root.configure(bg=C["bg"])
        self.root.minsize(960, 700)
        try:
            self.root.geometry(self.cfg["geometry"])
        except tk.TclError:
            self.root.geometry(DEFAULTS["geometry"])
        self.root.attributes("-topmost", self.cfg["topmost"])

        self.region = self.cfg["region"]
        self.events = queue.Queue()
        self.busy = False
        self.thumb_cache = {}             # 파일 해시 → 목록용 썸네일
        self._preview_src = (None, None)  # (경로, PIL 이미지)
        self._preview_tk = None
        self._jobs = {}
        self._drag = None
        self._loading_meta = False
        self.slots = []
        self._new_session()

        self._build_ui()
        self._bind_keys()
        self._refresh_all()

        if keyboard:
            self.hotkeys = keyboard.GlobalHotKeys({HOTKEY: lambda: self.events.put("capture")})
            self.hotkeys.daemon = True
            self.hotkeys.start()
        else:
            self.toast("pynput이 없어 F8을 쓸 수 없어요. 버튼을 사용하세요.", "warn")
        if self.region:
            self.toast("지난번 영역을 불러왔어요. 바로 F8로 캡처할 수 있어요.", "ok")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(50, self._poll_events)

    # ---------- 설정 ----------
    @staticmethod
    def _load_settings():
        cfg = json.loads(json.dumps(DEFAULTS))
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                cfg.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
        except (OSError, ValueError):
            pass
        if cfg["nup"] not in NUP_CHOICES:
            cfg["nup"] = "안 함"
        return cfg

    def _save_settings(self):
        self.cfg.update({
            "region": self.region,
            "autofit": self.autofit_var.get(),
            "jpeg": self.jpeg_var.get(),
            "ocr": self.ocr_var.get(),
            "nup": self.nup_var.get(),
            "sound": self.sound_var.get(),
            "topmost": self.pin_var.get(),
            "geometry": self.root.geometry(),
        })
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ---------- 세션 ----------
    def _new_session(self):
        self.pages = []   # [{"path","hash","title","memo"}]
        self.trash = []   # [(원래 위치, page)] 되돌리기용
        self.sel = None
        self.saved = False
        self.out_dir = os.path.join(CAPTURE_ROOT, datetime.now().strftime("%Y%m%d_%H%M%S"))

    def _end_session(self):
        """휴지통 비우고, 이미지가 하나도 없는 Capture 하위 폴더는 정리"""
        shutil.rmtree(os.path.join(self.out_dir, TRASH_DIR), ignore_errors=True)
        try:
            inside = os.path.commonpath([os.path.abspath(self.out_dir), os.path.abspath(CAPTURE_ROOT)]) \
                     == os.path.abspath(CAPTURE_ROOT)
            if inside and os.path.isdir(self.out_dir) and \
                    not any(f.lower().endswith(IMG_EXT) for f in os.listdir(self.out_dir)):
                shutil.rmtree(self.out_dir, ignore_errors=True)
        except (OSError, ValueError):
            pass

    def _persist(self):
        """페이지 순서·목차·메모를 폴더의 pages.json에 저장 (폴더 불러오기 때 복원)"""
        if not os.path.isdir(self.out_dir):
            return
        data = {"pages": [{"file": os.path.basename(p["path"]), "title": p["title"], "memo": p["memo"]}
                          for p in self.pages]}
        try:
            with open(os.path.join(self.out_dir, PAGES_JSON), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _confirm_discard(self, title, action):
        if self.pages and not self.saved:
            return messagebox.askyesno(
                title, f"PDF로 저장하지 않은 캡처 {len(self.pages)}장이 있어요.\n{action}\n\n"
                       "(캡처 이미지는 Capture 폴더에 그대로 남아요)", parent=self.root)
        return True

    def _check_busy(self):
        if self.busy:
            self.toast("PDF를 만드는 중이에요. 끝난 뒤에 다시 해주세요.", "warn")
        return self.busy

    # ---------- UI 구성 ----------
    def _build_ui(self):
        r = self.root
        r.columnconfigure(0, weight=1)
        r.rowconfigure(0, weight=1)

        # ===== 왼쪽: 큰 미리보기 + 페이지 정보 + 페이지 목록 =====
        left = tk.Frame(r, bg=C["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        self.pv = tk.Canvas(left, bg=C["card"], highlightthickness=2, highlightbackground=C["line"])
        self.pv.grid(row=0, column=0, sticky="nsew")
        self.pv.bind("<Configure>", lambda e: self._later("preview", 40, self._render_preview))

        nav = tk.Frame(left, bg=C["bg"])
        nav.grid(row=1, column=0, sticky="ew", pady=(10, 6))
        self.btn_prev = FlatButton(nav, "◀", lambda: self.select(self.sel - 1), C["card2"], C["line"], pady=4)
        self.btn_prev.pack(side="left")
        self.page_lbl = tk.Label(nav, text="", bg=C["bg"], fg=C["text"], font=F(10, "bold"), width=9)
        self.page_lbl.pack(side="left", padx=4)
        self.btn_next = FlatButton(nav, "▶", lambda: self.select(self.sel + 1), C["card2"], C["line"], pady=4)
        self.btn_next.pack(side="left")
        self.btn_del = FlatButton(nav, "선택 삭제", self.delete_selected, C["danger"], C["danger_h"],
                                  bold=False, pady=4)
        self.btn_del.pack(side="right")
        self.btn_undo = FlatButton(nav, "↶ 되돌리기", self.undo_delete, C["card2"], C["line"], bold=False, pady=4)
        self.btn_undo.pack(side="right", padx=(0, 6))

        meta = tk.Frame(left, bg=C["bg"])
        meta.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        meta.columnconfigure(1, weight=2)
        meta.columnconfigure(3, weight=3)
        self.title_var = tk.StringVar()
        self.memo_var = tk.StringVar()
        tk.Label(meta, text="목차 제목", bg=C["bg"], fg=C["sub"], font=F(9)).grid(row=0, column=0, padx=(0, 6))
        self.title_entry = self._entry(meta, self.title_var)
        self.title_entry.master.grid(row=0, column=1, sticky="ew")
        tk.Label(meta, text="메모", bg=C["bg"], fg=C["sub"], font=F(9)).grid(row=0, column=2, padx=(12, 6))
        self.memo_entry = self._entry(meta, self.memo_var)
        self.memo_entry.master.grid(row=0, column=3, sticky="ew")
        self.title_var.trace_add("write", lambda *a: self._on_meta())
        self.memo_var.trace_add("write", lambda *a: self._on_meta())

        self.strip = tk.Canvas(left, height=self.STRIP_H, bg=C["panel"], highlightthickness=0,
                               xscrollincrement=40)
        self.strip.grid(row=3, column=0, sticky="ew")
        self.strip.bind("<ButtonPress-1>", self._strip_press)
        self.strip.bind("<B1-Motion>", self._strip_motion)
        self.strip.bind("<ButtonRelease-1>", self._strip_release)
        self.strip.bind("<MouseWheel>", lambda e: self.strip.xview_scroll(-1 if e.delta > 0 else 1, "units"))
        self.strip.bind("<Button-4>", lambda e: self.strip.xview_scroll(-1, "units"))  # Linux
        self.strip.bind("<Button-5>", lambda e: self.strip.xview_scroll(1, "units"))
        self.strip.bind("<Configure>", lambda e: self._later("strip", 60, self._render_strip))

        # ===== 오른쪽: 조작 패널 =====
        side = tk.Frame(r, bg=C["bg"], width=self.SIDEBAR_W)
        side.grid(row=0, column=1, sticky="ns", padx=(8, 16), pady=16)
        side.pack_propagate(False)

        head = tk.Frame(side, bg=C["bg"])
        head.pack(fill="x")
        tk.Label(head, text="캡처 → PDF", bg=C["bg"], fg=C["text"], font=F(15, "bold")).pack(side="left")
        FlatButton(head, "단축키 ?", self.show_help, C["bg"], C["card"], fg=C["sub"],
                   bold=False, size=9, pady=2).pack(side="right")
        self.region_lbl = tk.Label(side, bg=C["bg"], fg=C["sub"], font=F(9), anchor="w", justify="left")
        self.region_lbl.pack(fill="x", pady=(2, 6))
        self.btn_preset = FlatButton(side, "영역 프리셋  ▾", self.preset_menu, C["card"], C["card2"],
                                     fg=C["sub"], bold=False, size=9, pady=5)
        self.btn_preset.pack(fill="x", pady=(0, 10))

        card = tk.Frame(side, bg=C["card"], highlightbackground=C["line"], highlightthickness=1, padx=12, pady=8)
        card.pack(fill="x")
        self.count_lbl = tk.Label(card, text="0", bg=C["card"], fg=C["text"], font=F(24, "bold"))
        self.count_lbl.pack(side="left")
        tk.Label(card, text=" 페이지", bg=C["card"], fg=C["sub"], font=F(11)).pack(side="left", anchor="s", pady=(0, 6))
        self.save_badge = tk.Label(card, text="", bg=C["card"], font=F(9, "bold"))
        self.save_badge.pack(side="right")

        g = tk.Frame(side, bg=C["bg"])
        g.pack(fill="x", pady=(12, 0))
        g.columnconfigure((0, 1), weight=1, uniform="b")
        FlatButton(g, "영역 지정", self.select_region, C["card2"], C["line"]).grid(
            row=0, column=0, sticky="ew", padx=(0, 4))
        self.btn_cap = FlatButton(g, "캡처  F8", self.capture, C["primary"], C["primary_h"])
        self.btn_cap.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        FlatButton(g, "＋ 새 PDF", self.new_pdf, C["card2"], C["line"], bold=False).grid(
            row=1, column=0, sticky="ew", padx=(0, 4), pady=(8, 0))
        FlatButton(g, "폴더 불러오기", self.load_folder, C["card2"], C["line"], bold=False).grid(
            row=1, column=1, sticky="ew", padx=(4, 0), pady=(8, 0))
        FlatButton(side, "Capture 폴더 열기", lambda: self._open_folder(CAPTURE_ROOT, create=True),
                   C["bg"], C["card"], fg=C["sub"], bold=False, size=9, pady=4).pack(fill="x", pady=(6, 0))

        # --- 아래쪽 고정 영역 (아래에서 위로 쌓음) ---
        self.status = tk.Label(side, text="", bg=C["bg"], fg=C["sub"], font=F(9), anchor="w",
                               wraplength=self.SIDEBAR_W - 8, justify="left")
        self.status.pack(side="bottom", fill="x", pady=(10, 0))
        self.btn_save = FlatButton(side, "PDF로 저장   Ctrl+S", self.make_pdf, C["accent"], C["accent_h"], size=11)
        self.btn_save.pack(side="bottom", fill="x", pady=(10, 0))

        nup = tk.Frame(side, bg=C["bg"])
        nup.pack(side="bottom", fill="x", pady=(6, 0))
        tk.Label(nup, text="인쇄용 모아찍기 PDF도 만들기", bg=C["bg"], fg=C["sub"], font=F(9)).pack(side="left")
        self.nup_var = tk.StringVar(value=self.cfg["nup"])
        om = tk.OptionMenu(nup, self.nup_var, *NUP_CHOICES, command=lambda v: self._save_settings())
        om.config(bg=C["card2"], fg=C["text"], activebackground=C["line"], activeforeground=C["text"],
                  highlightthickness=0, relief="flat", bd=0, font=F(9), width=7, indicatoron=False,
                  cursor="hand2", padx=6, pady=3)
        om["menu"].config(bg=C["card"], fg=C["text"], activebackground=C["primary"], font=F(9))
        om.pack(side="right")

        opts = tk.Frame(side, bg=C["bg"])
        opts.pack(side="bottom", fill="x", pady=(10, 0))
        self.autofit_var = tk.BooleanVar(value=self.cfg["autofit"])
        self.jpeg_var = tk.BooleanVar(value=self.cfg["jpeg"])
        self.ocr_var = tk.BooleanVar(value=self.cfg["ocr"] and bool(self.ocr_lang))
        self.sound_var = tk.BooleanVar(value=self.cfg["sound"])
        self.pin_var = tk.BooleanVar(value=self.cfg["topmost"])
        self._check(opts, "영역 지정 시 여백 자동 맞춤", self.autofit_var)
        self._check(opts, "PDF 용량 줄이기 (사진 많은 자료에 효과적)", self.jpeg_var)
        ocr_text = "검색 가능한 PDF (글자 인식·OCR)"
        if self.ocr_note:
            ocr_text += f"  ·  {self.ocr_note}"
        cb = self._check(opts, ocr_text, self.ocr_var)
        if not self.ocr_lang:
            cb.config(state="disabled", disabledforeground=C["dim"])
        self._check(opts, "캡처할 때 소리", self.sound_var)
        self._check(opts, "창을 항상 위에", self.pin_var, self._toggle_pin)

        ef = tk.Frame(side, bg=C["card"], highlightbackground=C["line"], highlightthickness=1)
        ef.pack(side="bottom", fill="x")
        self.name_var = tk.StringVar(value=self._default_name())
        tk.Entry(ef, textvariable=self.name_var, bg=C["card"], fg=C["text"], insertbackground=C["text"],
                 relief="flat", bd=0, highlightthickness=0, font=F(10)).pack(
            side="left", fill="x", expand=True, padx=10, ipady=6)
        tk.Label(ef, text=".pdf", bg=C["card"], fg=C["dim"], font=F(10)).pack(side="right", padx=(0, 10))
        tk.Label(side, text="파일 이름", bg=C["bg"], fg=C["sub"], font=F(9), anchor="w").pack(
            side="bottom", fill="x", pady=(0, 4))

    def _entry(self, parent, var):
        box = tk.Frame(parent, bg=C["card"], highlightbackground=C["line"], highlightthickness=1)
        e = tk.Entry(box, textvariable=var, bg=C["card"], fg=C["text"], insertbackground=C["text"],
                     disabledbackground=C["panel"], relief="flat", bd=0, highlightthickness=0, font=F(10))
        e.pack(fill="x", padx=8, ipady=5)
        e.bind("<Return>", lambda ev: self.pv.focus_set())
        return e

    def _check(self, parent, text, var, command=None):
        cb = tk.Checkbutton(parent, text=text, variable=var, command=command or self._save_settings,
                            bg=C["bg"], fg=C["sub"], selectcolor=C["card"], activebackground=C["bg"],
                            activeforeground=C["text"], font=F(9), bd=0, highlightthickness=0, anchor="w")
        cb.pack(fill="x")
        return cb

    def _bind_keys(self):
        def guard(fn):
            # 입력칸에 글을 쓰는 중에는 방향키/Delete/Ctrl+Z를 가로채지 않음
            return lambda e: None if isinstance(self.root.focus_get(), tk.Entry) else (fn(), "break")[1]

        self.root.bind("<Left>", guard(lambda: self.select((self.sel or 0) - 1)))
        self.root.bind("<Right>", guard(lambda: self.select((self.sel or 0) + 1)))
        self.root.bind("<Control-Left>", guard(lambda: self.move(-1)))
        self.root.bind("<Control-Right>", guard(lambda: self.move(1)))
        self.root.bind("<Delete>", guard(self.delete_selected))
        self.root.bind("<Control-z>", guard(self.undo_delete))
        self.root.bind("<Control-s>", lambda e: self.make_pdf())
        if sys.platform == "darwin":
            self.root.bind("<Command-s>", lambda e: self.make_pdf())
            self.root.bind("<Command-z>", guard(self.undo_delete))
        # 미리보기를 클릭하면 입력칸에서 빠져나와 단축키가 동작
        self.pv.bind("<Button-1>", lambda e: self.pv.focus_set())

    def _default_name(self):
        return "강의자료_" + datetime.now().strftime("%m%d_%H%M")

    def _toggle_pin(self):
        self.root.attributes("-topmost", self.pin_var.get())
        self._save_settings()

    def _later(self, key, ms, fn):
        if self._jobs.get(key):
            self.root.after_cancel(self._jobs[key])
        self._jobs[key] = self.root.after(ms, lambda: (self._jobs.pop(key, None), fn()))

    def toast(self, msg, kind="info"):
        color = {"info": C["sub"], "ok": C["accent"], "warn": C["warn"], "err": C["danger"]}[kind]
        self.status.config(text=msg, fg=color)

    def show_help(self):
        text = "\n".join(f"{k:<14}{v}" for k, v in SHORTCUTS)
        messagebox.showinfo("단축키", text, parent=self.root)

    # ---------- 화면 갱신 ----------
    def _refresh_all(self):
        self._refresh()
        self._load_meta()
        self._render_strip()
        self._later("preview", 10, self._render_preview)

    def _refresh(self):
        n = len(self.pages)
        self.count_lbl.config(text=str(n))
        if self.region:
            r = self.region
            self.region_lbl.config(text=f"영역  {r['width']} × {r['height']} px  ·  위치 ({r['left']}, {r['top']})")
        else:
            self.region_lbl.config(text="영역이 아직 지정되지 않았어요")
        if n == 0:
            self.save_badge.config(text="")
        elif self.saved:
            self.save_badge.config(text="● 저장됨", fg=C["accent"])
        else:
            self.save_badge.config(text="● 저장 안 됨", fg=C["warn"])
        self.page_lbl.config(text=f"{self.sel + 1} / {n}" if self.sel is not None else "– / –")

        has_sel = self.sel is not None
        self.btn_cap.set_enabled(self.region is not None)
        self.btn_save.set_enabled(n > 0 and not self.busy)
        self.btn_del.set_enabled(has_sel)
        self.btn_undo.set_enabled(bool(self.trash))
        self.btn_prev.set_enabled(has_sel and self.sel > 0)
        self.btn_next.set_enabled(has_sel and self.sel < n - 1)

    def _load_meta(self):
        self._loading_meta = True
        page = self.pages[self.sel] if self.sel is not None else None
        self.title_var.set(page["title"] if page else "")
        self.memo_var.set(page["memo"] if page else "")
        state = "normal" if page else "disabled"
        self.title_entry.config(state=state)
        self.memo_entry.config(state=state)
        self._loading_meta = False

    def _on_meta(self):
        if self._loading_meta or self.sel is None:
            return
        page = self.pages[self.sel]
        page["title"] = self.title_var.get().strip()
        page["memo"] = self.memo_var.get()
        self.saved = False
        self._refresh()
        self._later("persist", 500, self._persist)
        self._later("strip", 250, self._render_strip)

    def _render_preview(self):
        cv = self.pv
        cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 20 or h < 20:
            return
        if self.sel is None:
            if self.region:
                lines = ["F8을 누르면 지정한 영역이 캡처돼요",
                         "페이지를 넘길 때마다 F8 → 다 찍으면 PDF로 저장"]
            else:
                lines = ["① 오른쪽의 [영역 지정]으로 캡처할 부분을 드래그하세요",
                         "② 페이지를 넘기면서 F8   ③ PDF로 저장"]
            cv.create_text(w // 2, h // 2 - 14, text=lines[0], fill=C["sub"], font=F(12, "bold"))
            cv.create_text(w // 2, h // 2 + 14, text=lines[1], fill=C["dim"], font=F(10))
            return

        page = self.pages[self.sel]
        path = page["path"]
        if self._preview_src[0] != path:
            try:
                with Image.open(path) as im:
                    self._preview_src = (path, im.convert("RGB"))
            except OSError:
                cv.create_text(w // 2, h // 2, text="이미지를 열 수 없어요", fill=C["danger"], font=F(11))
                return
        src = self._preview_src[1]
        pad = 14
        scale = min((w - pad * 2) / src.width, (h - pad * 2) / src.height, 2.0)
        size = (max(1, int(src.width * scale)), max(1, int(src.height * scale)))
        self._preview_tk = ImageTk.PhotoImage(src.resize(size, Image.LANCZOS))
        cv.create_image(w // 2, h // 2, image=self._preview_tk)
        cv.create_text(w - 10, h - 8, anchor="se", fill=C["dim"], font=F(9),
                       text=f"{src.width}×{src.height}  ·  {int(scale * 100)}%")
        if page["title"]:
            tid = cv.create_text(20, 16, anchor="nw", fill="white", font=F(10, "bold"), text=f"목차  {page['title']}")
            x0, y0, x1, y1 = cv.bbox(tid)
            bg = cv.create_rectangle(x0 - 8, y0 - 4, x1 + 8, y1 + 4, fill=C["primary"], outline="")
            cv.tag_lower(bg, tid)

    # ---------- 페이지 목록 (클릭 선택 + 드래그 정렬) ----------
    def _strip_thumb(self, idx):
        key = self.pages[idx]["hash"]
        if key not in self.thumb_cache:
            try:
                with Image.open(self.pages[idx]["path"]) as im:
                    im = im.convert("RGB")
                    im.thumbnail((self.STRIP_THUMB * 2, self.STRIP_THUMB), Image.LANCZOS)
                    self.thumb_cache[key] = ImageTk.PhotoImage(im)
            except OSError:
                self.thumb_cache[key] = ImageTk.PhotoImage(Image.new("RGB", (50, self.STRIP_THUMB), C["card2"]))
        return self.thumb_cache[key]

    def _render_strip(self):
        s = self.strip
        s.delete("all")
        self.slots = []
        if not self.pages:
            s.create_text(14, self.STRIP_H // 2, anchor="w", fill=C["dim"], font=F(9),
                          text="캡처한 페이지가 여기에 쌓여요 · 클릭해서 크게 보기 · 끌어서 순서 바꾸기")
            s.config(scrollregion=(0, 0, 0, 0))
            return
        x, gap, top = 12, 12, (self.STRIP_H - self.STRIP_THUMB) // 2 - 6
        for i, page in enumerate(self.pages):
            img = self._strip_thumb(i)
            tw = img.width()
            if i == self.sel:
                s.create_rectangle(x - 3, top - 3, x + tw + 3, top + self.STRIP_THUMB + 3,
                                   outline=C["primary"], width=3)
            s.create_image(x, top, anchor="nw", image=img)
            if page["title"]:
                s.create_rectangle(x, top, x + 30, top + 15, fill=C["primary"], outline="")
                s.create_text(x + 15, top + 7, text="목차", fill="white", font=F(7, "bold"))
            if (page["memo"] or "").strip():
                s.create_oval(x + tw - 13, top + 3, x + tw - 3, top + 13, fill=C["warn"], outline="")
            s.create_text(x + tw // 2, top + self.STRIP_THUMB + 12, text=str(i + 1),
                          fill=C["text"] if i == self.sel else C["dim"], font=F(8, "bold"))
            self.slots.append((x, x + tw))
            x += tw + gap
        s.config(scrollregion=(0, 0, x, self.STRIP_H))
        # 선택한 썸네일이 보이도록 스크롤
        view_w = s.winfo_width() or 1
        if x <= view_w:
            s.xview_moveto(0)
        elif self.sel is not None:
            sx0, sx1 = self.slots[self.sel]
            if sx0 < s.canvasx(0) or sx1 > s.canvasx(view_w):
                s.xview_moveto(max(0, (sx0 - view_w / 2) / x))

    def _slot_at(self, cx):
        for i, (x0, x1) in enumerate(self.slots):
            if x0 - 6 <= cx <= x1 + 6:
                return i
        return None

    def _insert_index(self, cx):
        for i, (x0, x1) in enumerate(self.slots):
            if cx < (x0 + x1) / 2:
                return i
        return len(self.slots)

    def _strip_press(self, e):
        self.strip.focus_set()
        i = self._slot_at(self.strip.canvasx(e.x))
        self._drag = {"i": i, "x": e.x, "moved": False, "t": None} if i is not None else None

    def _strip_motion(self, e):
        d = self._drag
        if not d or self.busy:
            return
        if abs(e.x - d["x"]) > 6:
            d["moved"] = True
        if not d["moved"]:
            return
        w = self.strip.winfo_width()
        if e.x < 30:
            self.strip.xview_scroll(-1, "units")
        elif e.x > w - 30:
            self.strip.xview_scroll(1, "units")
        t = self._insert_index(self.strip.canvasx(e.x))
        d["t"] = t
        lx = self.slots[t][0] - 6 if t < len(self.slots) else self.slots[-1][1] + 6
        self.strip.delete("ins")
        self.strip.create_line(lx, 4, lx, self.STRIP_H - 4, fill=C["accent"], width=3, tags="ins")

    def _strip_release(self, e):
        d, self._drag = self._drag, None
        self.strip.delete("ins")
        if not d:
            return
        if not d["moved"]:
            self.select(d["i"])
            return
        if d["t"] is None:
            return
        i, t = d["i"], d["t"]
        if t > i:
            t -= 1
        if t != i:
            self.move_to(i, t)

    def select(self, i):
        if not self.pages:
            return
        self.sel = max(0, min(i, len(self.pages) - 1))
        self._refresh_all()

    def _poll_events(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev == "capture":
                    self.capture()
                elif ev[0] == "progress":
                    self.toast(ev[1])
                elif ev[0] == "saved":
                    self._on_saved(ev[1])
                elif ev[0] == "error":
                    self._on_save_error(ev[1])
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    # ---------- 영역 지정 / 프리셋 ----------
    def select_region(self):
        self.root.withdraw()
        self.root.after(200, self._open_overlay)

    def _open_overlay(self):
        with mss.mss() as sct:
            mon = sct.monitors[0]  # 모든 모니터를 합친 전체 영역
        L, T, W, H = mon["left"], mon["top"], mon["width"], mon["height"]

        ov = tk.Toplevel(self.root)
        ov.overrideredirect(True)
        ov.geometry(f"{W}x{H}{L:+d}{T:+d}")
        ov.attributes("-topmost", True)
        ov.attributes("-alpha", 0.35)
        cv = tk.Canvas(ov, cursor="cross", bg="black", highlightthickness=0)
        cv.pack(fill="both", expand=True)
        hint = "캡처할 영역을 드래그하세요   (Esc: 취소)"
        if self.autofit_var.get():
            hint += "\n조금 넉넉하게 잡아도 가장자리 여백은 자동으로 맞춰져요"
        cv.create_text(40 - L, 40 - T, anchor="nw", fill="white", font=F(18, "bold"), text=hint)
        st = {}

        def press(e):
            st["x0"], st["y0"] = e.x, e.y
            st["rect"] = cv.create_rectangle(e.x, e.y, e.x, e.y, outline=C["primary"], width=3)
            st["size"] = cv.create_text(e.x, e.y - 8, anchor="sw", fill="white", font=F(12, "bold"))

        def drag(e):
            if "rect" in st:
                cv.coords(st["rect"], st["x0"], st["y0"], e.x, e.y)
                cv.coords(st["size"], min(st["x0"], e.x), min(st["y0"], e.y) - 8)
                cv.itemconfig(st["size"], text=f"{abs(e.x - st['x0'])} × {abs(e.y - st['y0'])}")

        def release(e):
            if "x0" not in st:
                return
            x0, y0 = st["x0"], st["y0"]
            w, h = abs(e.x - x0), abs(e.y - y0)
            region = {"left": L + min(x0, e.x), "top": T + min(y0, e.y), "width": w, "height": h}
            ov.destroy()
            if w < 10 or h < 10:
                self.root.deiconify()
                self.toast("영역이 너무 작아요. 다시 지정하세요.", "warn")
                return
            # 오버레이가 사라진 뒤 화면을 확인해야 하므로 잠깐 기다림
            self.root.after(150, lambda: self._finish_region(region, self.autofit_var.get()))

        def cancel(e=None):
            ov.destroy()
            self.root.deiconify()

        cv.bind("<ButtonPress-1>", press)
        cv.bind("<B1-Motion>", drag)
        cv.bind("<ButtonRelease-1>", release)
        ov.bind("<Escape>", cancel)
        ov.focus_force()

    def _finish_region(self, region, fit):
        msg = "영역을 지정했어요. 페이지를 넘기며 F8을 누르세요."
        if fit:
            fitted = self._autofit(region)
            if fitted:
                msg = (f"가장자리 여백을 잘라 {fitted['width']}×{fitted['height']}로 맞췄어요. "
                       "페이지를 넘기며 F8을 누르세요.")
                region = fitted
        self.region = region
        self.root.deiconify()
        self._save_settings()
        self.toast(msg, "ok")
        self._refresh_all()

    @staticmethod
    def _autofit(region):
        try:
            with mss.mss() as sct:
                shot = sct.grab(region)
        except Exception:
            return None
        im = Image.frombytes("RGB", shot.size, shot.rgb)
        bbox = content_bbox(im)
        if not bbox:
            return None
        l, t, r, b = bbox
        w, h = im.size
        if (r - l) * (b - t) < 0.2 * w * h:  # 내용이 너무 작게 잡히면 오판일 가능성 → 그대로 둠
            return None
        if l <= 3 and t <= 3 and r >= w - 3 and b >= h - 3:  # 잘라낼 여백이 거의 없음
            return None
        return {"left": region["left"] + l, "top": region["top"] + t, "width": r - l, "height": b - t}

    def preset_menu(self):
        m = tk.Menu(self.root, tearoff=0, bg=C["card"], fg=C["text"], activebackground=C["primary"],
                    activeforeground="white", font=F(10))
        presets = self.cfg["presets"]
        for name, reg in presets.items():
            m.add_command(label=f"{name}    ({reg['width']}×{reg['height']})",
                          command=lambda n=name, r=reg: self._apply_preset(n, r))
        if presets:
            m.add_separator()
        m.add_command(label="현재 영역을 프리셋으로 저장…", command=self._save_preset,
                      state="normal" if self.region else "disabled")
        if presets:
            dm = tk.Menu(m, tearoff=0, bg=C["card"], fg=C["text"], activebackground=C["danger"], font=F(10))
            for name in presets:
                dm.add_command(label=name, command=lambda n=name: self._del_preset(n))
            m.add_cascade(label="프리셋 삭제", menu=dm)
        b = self.btn_preset
        m.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height())

    def _apply_preset(self, name, reg):
        self.region = dict(reg)
        self._save_settings()
        self.toast(f"'{name}' 영역을 적용했어요.", "ok")
        self._refresh_all()

    def _save_preset(self):
        name = simpledialog.askstring("프리셋 저장", "프리셋 이름 (예: 강의 뷰어, 코드 화면)", parent=self.root)
        if not name or not name.strip():
            return
        self.cfg["presets"][name.strip()] = dict(self.region)
        self._save_settings()
        self.toast(f"'{name.strip()}' 프리셋을 저장했어요.", "ok")

    def _del_preset(self, name):
        self.cfg["presets"].pop(name, None)
        self._save_settings()
        self.toast(f"'{name}' 프리셋을 삭제했어요.")

    # ---------- 캡처 ----------
    def _window_overlaps_region(self):
        r = self.region
        x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        return not (x + w <= r["left"] or r["left"] + r["width"] <= x or
                    y + h <= r["top"] or r["top"] + r["height"] <= y)

    def capture(self):
        if not self.region:
            self.toast("먼저 영역을 지정하세요.", "warn")
            return
        # 창이 캡처 영역과 겹치면 잠깐 투명하게 (숨기지 않으므로 브라우저 포커스를 뺏지 않음)
        if self._window_overlaps_region():
            self.root.attributes("-alpha", 0.0)
            self.root.update_idletasks()
            self.root.after(120, lambda: self._grab(restore=True))
        else:
            self._grab(restore=False)

    def _grab(self, restore):
        try:
            with mss.mss() as sct:
                shot = sct.grab(self.region)
            png = mss.tools.to_png(shot.rgb, shot.size)
        except Exception as ex:
            self.toast(f"캡처 실패: {ex}", "err")
            return
        finally:
            if restore:
                self.root.attributes("-alpha", 1.0)

        digest = hashlib.md5(png).hexdigest()
        if self.pages and digest == self.pages[-1]["hash"]:
            self.toast("직전과 같은 화면이라 건너뛰었어요.", "warn")
            return

        os.makedirs(self.out_dir, exist_ok=True)
        path = self._free_path(len(self.pages) + 1)
        with open(path, "wb") as f:
            f.write(png)
        self.pages.append({"path": path, "hash": digest, "title": "", "memo": ""})
        self.sel = len(self.pages) - 1
        self.saved = False
        self._persist()
        self._feedback()
        self.toast(f"{len(self.pages)}페이지 캡처 완료", "ok")
        self._refresh_all()

    def _free_path(self, n, ext=".png"):
        path = os.path.join(self.out_dir, f"{n:04d}{ext}")
        k = 1
        while os.path.exists(path):  # 같은 이름이 있으면 겹치지 않게
            path = os.path.join(self.out_dir, f"{n:04d}_{k}{ext}")
            k += 1
        return path

    def _feedback(self):
        # 미리보기 테두리를 잠깐 초록색으로 깜빡여 캡처됐음을 알림
        self.pv.config(highlightbackground=C["accent"])
        self.root.after(220, lambda: self.pv.config(highlightbackground=C["line"]))
        if self.sound_var.get():
            try:
                if sys.platform == "win32":
                    import winsound
                    winsound.MessageBeep(winsound.MB_OK)
                else:
                    self.root.bell()
            except Exception:
                pass

    # ---------- 페이지 편집 ----------
    def delete_selected(self):
        if self.sel is None or self._check_busy():
            return
        i = self.sel
        page = self.pages.pop(i)
        trash = os.path.join(self.out_dir, TRASH_DIR)
        try:
            os.makedirs(trash, exist_ok=True)
            dst = os.path.join(trash, f"{len(self.trash):04d}_{os.path.basename(page['path'])}")
            os.replace(page["path"], dst)
            page["path"] = dst
            self.trash.append((i, page))
        except OSError as ex:
            self.toast(f"삭제 실패: {ex}", "err")
            self.pages.insert(i, page)
            return
        self._renumber()
        self.sel = None if not self.pages else min(i, len(self.pages) - 1)
        self.saved = False
        self._persist()
        self.toast(f"{i + 1}페이지를 삭제했어요. Ctrl+Z로 되돌릴 수 있어요.")
        self._refresh_all()

    def undo_delete(self):
        if not self.trash or self._check_busy():
            return
        i, page = self.trash.pop()
        i = min(i, len(self.pages))
        ext = os.path.splitext(page["path"])[1].lower()
        dst = os.path.join(self.out_dir, f".__restore{ext}")
        try:
            os.replace(page["path"], dst)
        except OSError as ex:
            self.toast(f"되돌리기 실패: {ex}", "err")
            return
        page["path"] = dst
        self.pages.insert(i, page)
        self._renumber()
        self.sel = i
        self.saved = False
        self._persist()
        self.toast(f"{i + 1}페이지를 되살렸어요.", "ok")
        self._refresh_all()

    def move(self, delta):
        if self.sel is None:
            return
        j = self.sel + delta
        if 0 <= j < len(self.pages):
            self.move_to(self.sel, j)

    def move_to(self, i, j):
        if self._check_busy():
            return
        self.pages.insert(j, self.pages.pop(i))
        self._renumber()
        self.sel = j
        self.saved = False
        self._persist()
        self.toast(f"{i + 1}번째 페이지를 {j + 1}번째로 옮겼어요.")
        self._refresh_all()

    def _renumber(self):
        """폴더 안 파일 이름을 현재 순서(0001, 0002 …)에 맞춤"""
        wanted = [os.path.join(self.out_dir, f"{k + 1:04d}{os.path.splitext(p['path'])[1].lower()}")
                  for k, p in enumerate(self.pages)]
        if wanted == [p["path"] for p in self.pages]:
            return
        try:
            tmp = []
            for k, p in enumerate(self.pages):
                t = os.path.join(self.out_dir, f".__tmp_{k:04d}{os.path.splitext(p['path'])[1].lower()}")
                os.replace(p["path"], t)
                tmp.append(t)
            for p, t, w in zip(self.pages, tmp, wanted):
                os.replace(t, w)
                p["path"] = w
            self._preview_src = (None, None)
        except OSError as ex:
            self.toast(f"파일 이름 정리 실패: {ex}", "err")

    # ---------- 새 PDF / 불러오기 ----------
    def new_pdf(self, ask=True):
        if self._check_busy():
            return
        if ask and not self._confirm_discard("새 PDF", "그래도 새로 시작할까요?"):
            return
        self._end_session()
        self._new_session()
        self.name_var.set(self._default_name())
        self.toast("새 PDF를 시작했어요. 영역은 그대로 유지돼요.", "ok")
        self._refresh_all()

    def load_folder(self):
        if self._check_busy() or not self._confirm_discard("폴더 불러오기", "다른 폴더를 불러올까요?"):
            return
        os.makedirs(CAPTURE_ROOT, exist_ok=True)
        folder = filedialog.askdirectory(parent=self.root, initialdir=CAPTURE_ROOT,
                                         title="이어서 작업할 캡처 폴더 선택")
        if not folder:
            return
        folder = os.path.normpath(folder)
        imgs = sorted(f for f in os.listdir(folder)
                      if f.lower().endswith(IMG_EXT) and not f.startswith("."))
        if not imgs:
            messagebox.showinfo("폴더 불러오기", "이 폴더에는 이미지가 없어요.", parent=self.root)
            return
        meta, order = {}, []
        try:
            with open(os.path.join(folder, PAGES_JSON), encoding="utf-8") as f:
                for item in json.load(f).get("pages", []):
                    fn = item.get("file")
                    if fn in imgs and fn not in meta:
                        order.append(fn)
                        meta[fn] = item
        except (OSError, ValueError, AttributeError):
            pass
        order += [f for f in imgs if f not in meta]

        self._end_session()
        self._new_session()
        self.out_dir = folder
        self.pages = [{"path": os.path.join(folder, f), "hash": md5_file(os.path.join(folder, f)),
                       "title": meta.get(f, {}).get("title", "") or "",
                       "memo": meta.get(f, {}).get("memo", "") or ""} for f in order]
        self.sel = len(self.pages) - 1
        self.name_var.set(os.path.basename(folder))
        titles = sum(1 for p in self.pages if p["title"])
        extra = f" (목차 {titles}개 포함)" if titles else ""
        self.toast(f"{len(self.pages)}장을 불러왔어요{extra}. 이어서 캡처하면 뒤에 추가돼요.", "ok")
        self._refresh_all()

    # ---------- PDF 저장 ----------
    def make_pdf(self):
        if not self.pages or self.busy:
            return
        name = self.name_var.get().strip() or self._default_name()
        for ch in '\\/:*?"<>|':
            name = name.replace(ch, "_")
        save_dir = self.cfg.get("save_dir") or BASE_DIR
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".pdf", initialdir=save_dir,
            filetypes=[("PDF", "*.pdf")], initialfile=name + ".pdf",
        )
        if not path:
            return
        self._persist()
        pages = [dict(p) for p in self.pages]
        jpeg = self.jpeg_var.get()
        ocr_lang = self.ocr_lang if self.ocr_var.get() else None
        nup = NUP_CHOICES[self.nup_var.get()]

        self.busy = True
        self.btn_save.config(text="PDF 만드는 중…")
        self._refresh()

        def work():
            try:
                res = build_pdf(pages, path, jpeg, ocr_lang, nup,
                                progress=lambda t: self.events.put(("progress", t)))
                self.events.put(("saved", res))
            except Exception as ex:
                self.events.put(("error", str(ex)))

        threading.Thread(target=work, daemon=True).start()

    def _save_done(self):
        self.busy = False
        self.btn_save.config(text="PDF로 저장   Ctrl+S")
        self._refresh()

    def _on_save_error(self, msg):
        self._save_done()
        self.toast("PDF 생성 실패", "err")
        messagebox.showerror("오류", f"PDF 생성 실패: {msg}", parent=self.root)

    def _on_saved(self, res):
        self._save_done()
        self.saved = True
        self.cfg["save_dir"] = os.path.dirname(res["path"])
        self._save_settings()
        self._refresh()
        size_mb = os.path.getsize(res["path"]) / 1024 / 1024
        parts = [f"{res['pages']}페이지", f"{size_mb:.1f}MB"]
        if res["titles"]:
            parts.append(f"목차 {res['titles']}개")
        if res["memos"]:
            parts.append(f"메모 {res['memos']}개")
        if res["ocr"]:
            parts.append("검색 가능")
        summary = " · ".join(parts)
        self.toast(f"저장 완료 · {summary}", "ok")

        detail = f"{os.path.basename(res['path'])}\n{summary}"
        if res["nup_path"]:
            detail += f"\n\n인쇄용: {os.path.basename(res['nup_path'])}"
        if messagebox.askyesno("저장 완료", f"{detail}\n\n저장한 폴더를 열까요?", parent=self.root):
            self._open_folder(os.path.dirname(res["path"]))
        if messagebox.askyesno("새 PDF", "이어서 다른 PDF를 만들까요?", parent=self.root):
            self.new_pdf(ask=False)

    @staticmethod
    def _open_folder(folder, create=False):
        try:
            if create:
                os.makedirs(folder, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    # ---------- 종료 ----------
    def on_close(self):
        if self.busy and not messagebox.askyesno("종료", "PDF를 만드는 중이에요. 그래도 종료할까요?",
                                                 parent=self.root):
            return
        if not self.busy and not self._confirm_discard("종료", "그래도 종료할까요?"):
            return
        self._persist()
        self._save_settings()
        self._end_session()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
