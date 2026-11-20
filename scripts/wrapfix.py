"""한국어 줄바꿈 다듬기 — 모든 페이지에 같은 규칙을 적용합니다.

1) CSS: 단어 중간에서 끊지 않기(keep-all), 문단 끝 한두 글자만 남는 줄 줄이기(pretty), 제목 줄 길이 맞추기(balance).
   선택자는 :where() 로 감싸 우선순위가 0이라, 각 페이지가 이미 정한 규칙(영문 페이지의 normal 등)이 그대로 이깁니다.
2) 글자: 구분 기호가 줄 맨 앞으로 내려가지 않게 앞 공백을 붙는 공백으로 바꿉니다.
   ' · ' ' — ' ' → ' 는 앞에 붙이고, 기간 ' – ' 는 양쪽을 붙이고, 띄어쓰기 없는 'A·B' 는 '·' 앞에서 끊지 않게 합니다.
   <script> <style> <pre> <code> <textarea> <svg> <math> 안과 태그 속성은 건드리지 않습니다.
3) WRAP_JS: 화면을 자바스크립트로 그리는 준비 공간 앱에서 새로 그려진 글자에 2)를 적용합니다.
"""
import re

MARK = "data-wrapfix"
NBSP, WJ, ZWSP = "\u00a0", "\u2060", "\u200b"

WRAP_CSS = (
    f'<style {MARK}>'
    ':where(html:lang(ko)) :where(body){word-break:keep-all;overflow-wrap:anywhere}'
    ':where(body){text-wrap-style:pretty}'
    ':where(h1,h2,h3,h4,h5,h6,figcaption,summary,dt,th,caption){text-wrap-style:balance}'
    ':where(pre,code,kbd,samp,textarea,input){word-break:normal;text-wrap-style:auto}'
    ':where(td,th){overflow-wrap:break-word}'   # 표 칸이 한 글자 폭으로 좁아지지 않게 (단어 단위로만 접기)
    '</style>'
)

_SKIP = ("script", "style", "pre", "code", "textarea", "svg", "math", "kbd", "samp")
_TAG = re.compile(r"(<[^>]+>)")
_RULES = [
    (re.compile(r" · "), NBSP + "· "),
    (re.compile(r" — "), NBSP + "— "),
    (re.compile(r" → "), NBSP + "→ "),
    (re.compile(r" – "), NBSP + "–" + NBSP),
    (re.compile("(?<=[^\\s\u00a0\u2060])\u00b7(?=[^\\s\u00a0\u200b])"), WJ + "\u00b7" + ZWSP),   # 점 앞은 붙이고 점 뒤에서만 접기
]


def polish_text(s: str) -> str:
    for pat, rep in _RULES:
        s = pat.sub(rep, s)
    return s


def polish_html(html: str, css: bool = True, js: bool = False) -> str:
    """HTML 문서의 글자 부분만 다듬고, <head> 끝에 줄바꿈 CSS 를 한 번 넣습니다."""
    out, skip = [], []
    for part in _TAG.split(html):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            if m:
                name = m.group(1).lower()
                if name in _SKIP and not part.endswith("/>"):
                    if part.startswith("</"):
                        if skip and skip[-1] == name:
                            skip.pop()
                    else:
                        skip.append(name)
            out.append(part)
        else:
            out.append(part if skip else polish_text(part))
    html = "".join(out)
    if css and MARK not in html and "</head>" in html:
        html = html.replace("</head>", WRAP_CSS + "</head>", 1)
    if js and "wrapfix-js" not in html and "</body>" in html:   # 자바스크립트로 그리는 부분(지도·검색·데모)도 같은 규칙
        html = html.replace("</body>", WRAP_JS + "</body>", 1)
    return html


# 자바스크립트로 그리는 화면용: 새로 들어온 글자에 같은 규칙 적용 (입력란·코드는 제외)
WRAP_JS = r"""<script id="wrapfix-js">(function(){var R=[[/ \u00b7 /g,'\u00a0\u00b7 '],[/ \u2014 /g,'\u00a0\u2014 '],[/ \u2192 /g,'\u00a0\u2192 '],[/ \u2013 /g,'\u00a0\u2013\u00a0'],[/([^\s\u00a0\u2060])\u00b7(?=[^\s\u00a0\u200b])/g,'$1\u2060\u00b7\u200b']];
var SKIP=/^(SCRIPT|STYLE|PRE|CODE|TEXTAREA|INPUT|SVG|MATH|KBD|SAMP|OPTION)$/;
function fix(root){if(!root)return;if(root.nodeType===3){one(root);return}if(root.nodeType!==1||SKIP.test(root.nodeName)||root.isContentEditable)return;
var w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:function(n){for(var p=n.parentNode;p&&p!==root.parentNode;p=p.parentNode){if(p.nodeType===1&&(SKIP.test(p.nodeName)||p.isContentEditable))return 2}return 1}}),n;while((n=w.nextNode()))one(n)}
function one(n){var v=n.nodeValue,o=v;if(!v||v.length<3)return;for(var i=0;i<R.length;i++)v=v.replace(R[i][0],R[i][1]);if(v!==o)n.nodeValue=v}
var q=[],t=0;function flush(){t=0;var a=q;q=[];for(var i=0;i<a.length;i++)fix(a[i])}
function start(){fix(document.body);new MutationObserver(function(ms){for(var i=0;i<ms.length;i++)for(var j=0;j<ms[i].addedNodes.length;j++)q.push(ms[i].addedNodes[j]);if(!t)t=requestAnimationFrame(flush)}).observe(document.body,{childList:true,subtree:true})}
if(document.body)start();else document.addEventListener('DOMContentLoaded',start)})();</script>"""
