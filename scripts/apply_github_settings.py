#!/usr/bin/env python3
"""data/github_settings.yaml 의 저장소 About(설명·웹사이트·토픽)과 프로필 이름·소개를 GitHub 에 적용.

토큰은 환경 변수 GH_ADMIN_TOKEN 에서만 읽고 출력하지 않습니다. 없으면 아무것도 하지 않고 끝납니다.
필요한 fine-grained 토큰 권한: 대상 저장소의 Administration(Read and write) + Metadata(Read),
프로필까지 바꾸려면 Account permissions 의 Profile(Read and write).
사용: GH_ADMIN_TOKEN=... python3 scripts/apply_github_settings.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

CFG = Path(__file__).resolve().parent.parent / "data" / "github_settings.yaml"
API = "https://api.github.com"


def call(method, path, body, token):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "portfolio-settings"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        msg = ""
        try:
            msg = json.loads(e.read() or b"{}").get("message", "")
        except Exception:
            pass
        return e.code, msg


def main():
    token = os.environ.get("GH_ADMIN_TOKEN", "").strip()
    if not token:
        print("GH_ADMIN_TOKEN 이 없어 건너뜁니다 (저장소 Settings → Secrets and variables → Actions 에 등록하면 적용).")
        return 0
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    owner, failures = cfg["owner"], 0
    for name, r in (cfg.get("repos") or {}).items():
        code, msg = call("PATCH", f"/repos/{owner}/{name}", {"description": r.get("description", ""), "homepage": r.get("homepage", "")}, token)
        ok1 = code == 200
        code2, msg2 = call("PUT", f"/repos/{owner}/{name}/topics", {"names": r.get("topics") or []}, token)
        ok2 = code2 == 200
        failures += (not ok1) + (not ok2)
        print(f"{'✔' if ok1 and ok2 else '✗'} {name}: 설명·웹사이트 {code}{' ' + msg if msg else ''} · 토픽 {code2}{' ' + msg2 if msg2 else ''}")
    p = cfg.get("profile") or {}
    if p:
        code, msg = call("PATCH", "/user", {k: p[k] for k in ("name", "bio", "blog") if k in p}, token)
        print(f"{'✔' if code == 200 else '⚠'} 프로필 이름·소개: {code}{' ' + msg if msg else ''}"
              + ("" if code == 200 else " — 토큰에 Profile 쓰기 권한이 없으면 웹에서 직접 바꿔 주세요"))
    print("고정(Pin)과 프로필 사진은 API 가 없어 웹에서 직접 설정해야 합니다.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
