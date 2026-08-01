# -*- coding: utf-8 -*-
"""verify_itinerary.py의 build()에서 index.html의 TT(시간표) 데이터를 생성한다.
손으로 고치면 검증기와 어긋나므로 항상 이 스크립트로 만든다.

사용법:  python tools/gen_timetable.py          # TT 한 줄을 표준출력에 찍는다
         python tools/gen_timetable.py --write  # index.html의 TT 줄을 교체한다

(구판 인솔서 guide.html + guide-data.js는 2026-08-01 단일안 개편에서 삭제됐다.
 인솔서를 되살리려면 git 이력에서 꺼내 새 일정으로 다시 쓸 것.)"""
import sys, io, os, json, re

if __name__ == "__main__":      # import될 때 stdout을 건드리지 않는다
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_itinerary as V

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = ["8/10", "8/11", "8/12", "8/13", "8/14"]


def kind(e):
    if e["k"] != "move":
        return e["k"]
    # 도보는 별도 키를 쓰지만 막대 색은 차량과 같이 둔다 — index.html에 새 클래스를 만들지 않기 위함.
    # R3의 피로 집계에서만 갈라진다 (verify_itinerary.R3 참조).
    return "rail" if (e.get("key") or "").startswith("rail") else "car"


def to_tt(P):
    """build()가 만든 일정을 날짜별 막대 배열로 변환.
    자정을 넘긴 취침은 전날의 stay로 붙인다."""
    days = [{"d": d, "b": [], "stay": ""} for d in DAYS]
    idx = {d: i for i, d in enumerate(DAYS)}
    for e in P:
        i = idx[e["d"]]
        if e["k"] == "sleep":
            # 00:00~06:00 사이의 취침은 전날 밤에 속한다
            days[i - 1 if e["t"] < V.M("06:00") and i > 0 else i]["stay"] = e["lab"]
            continue
        # 5번째 요소는 **패키지가 커버하는 구간**이라는 표시다 (index.html에서 테두리로 묶는다).
        # 없는 블록에는 아예 넣지 않아 TT 크기를 키우지 않는다.
        bar = [e["t"], e["dur"], kind(e), e["lab"]]
        if e.get("pkg"):
            bar.append(1)
        days[i]["b"].append(bar)
    return days


def build_tt():
    """검증기의 PLANS를 그대로 따라간다."""
    return {code: to_tt(V.build(code)) for code, _pkg, _price, _nm in V.PLANS}


# index.html에 싣는 플랜 — 단일 확정안 F2 (2026-08-01 가족 결정).
PAGE_PLANS = tuple(code for code, _pkg, _price, _nm in V.PLANS)


def line():
    tt = build_tt()
    page = {k: tt[k] for k in PAGE_PLANS}
    return "var TT=" + json.dumps(page, ensure_ascii=False, separators=(",", ":")) + ";"


# (파일, 바꿀 줄의 정규식, 넣을 내용을 만드는 함수)
TARGETS = [("index.html", r"^var TT=.*?;$", line)]


if __name__ == "__main__":
    if "--write" in sys.argv:
        for name, pat, fn in TARGETS:
            p = os.path.join(ROOT, name)
            src = open(p, encoding="utf-8").read()
            out = fn()
            new, n = re.subn(pat, lambda m: out, src, count=1, flags=re.M)
            if n != 1:
                sys.exit("%s에서 '%s' 줄을 찾지 못했습니다" % (name, pat))
            open(p, "w", encoding="utf-8", newline="\n").write(new)
            print("%s의 시간표를 교체했습니다 — %d바이트" % (name, len(out)))
    else:
        print(line())
