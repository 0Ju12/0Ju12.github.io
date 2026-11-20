#!/usr/bin/env python3
"""공개 데이터 프로젝트(0Ju12/data-projects)의 GitHub Actions 실행 기록을 모아 data/ops_record.json 에 저장.

- 매일 수집(geo-daily.yml)과 매시 API 점검(api-watch.yml)의 완료된 실행만 셉니다.
- 공개 저장소라 토큰 없이도 읽히고, GITHUB_TOKEN 이 있으면 한도가 넉넉해집니다.
- 네트워크가 막히면 기존 파일을 그대로 두고 0으로 끝납니다(빌드를 막지 않음).
사용: python3 scripts/ops_record.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = "0Ju12/data-projects"
WORKFLOWS = {"daily": "geo-daily.yml", "hourly": "api-watch.yml"}
OUT = Path(__file__).resolve().parent.parent / "data" / "ops_record.json"
KST = timezone(timedelta(hours=9))


def get(url, use_token=True):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "portfolio-ops-record"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and use_token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if token and use_token and e.code in (401, 403):   # 다른 저장소 권한이 없는 토큰이면 공개 API로 다시
            return get(url, use_token=False)
        raise


def summarize(workflow):
    runs, page = [], 1
    while page <= 10:  # 최대 1,000건
        d = get(f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow}/runs?status=completed&per_page=100&page={page}")
        batch = d.get("workflow_runs") or []
        runs += batch
        if len(batch) < 100:
            break
        page += 1
    if not runs:
        return None
    first = min(r["created_at"] for r in runs)
    last = max(runs, key=lambda r: r["created_at"])
    fail = [r for r in runs if r.get("conclusion") not in ("success", "skipped", "cancelled")]
    return {
        "workflow": workflow,
        "first": datetime.fromisoformat(first.replace("Z", "+00:00")).astimezone(KST).strftime("%Y-%m-%d"),
        "total": len(runs),
        "success": sum(r.get("conclusion") == "success" for r in runs),
        "failure": len(fail),
        "scheduled": sum(r.get("event") == "schedule" for r in runs),
        "last": datetime.fromisoformat(last["created_at"].replace("Z", "+00:00")).astimezone(KST).strftime("%Y-%m-%d %H:%M"),
        "last_conclusion": last.get("conclusion"),
        "url": f"https://github.com/{REPO}/actions/workflows/{workflow}",
    }


def main():
    try:
        rec = {k: summarize(w) for k, w in WORKFLOWS.items()}
    except Exception as e:  # 네트워크·한도 문제는 기존 기록 유지
        print(f"ops_record: 갱신 건너뜀 ({type(e).__name__}) — 기존 {OUT.name} 유지", file=sys.stderr)
        return 0
    rec = {k: v for k, v in rec.items() if v}
    if not rec:
        print("ops_record: 실행 기록 없음 — 기존 파일 유지", file=sys.stderr)
        return 0
    rec["as_of"] = datetime.now(KST).strftime("%Y-%m-%d")
    rec["repo"] = REPO
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    d = rec.get("daily") or {}
    print(f"✔ {OUT.relative_to(OUT.parent.parent)} — 매일 수집 {d.get('total')}회(실패 {d.get('failure')}), 기준 {rec['as_of']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
