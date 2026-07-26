# -*- coding: utf-8 -*-
"""verify_itinerary.py의 build()에서 index.html의 TT(시간표) 데이터를 생성한다.
손으로 고치면 검증기와 어긋나므로 항상 이 스크립트로 만든다.

사용법:  python tools/gen_timetable.py          # TT 한 줄을 표준출력에 찍는다
         python tools/gen_timetable.py --write  # index.html의 TT 줄을 교체한다
"""
import sys, io, os, json, re

if __name__ == "__main__":      # import될 때 stdout을 건드리지 않는다
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_itinerary as V

DAYS = ["8/10", "8/11", "8/12", "8/13", "8/14"]


def kind(e):
    if e["k"] != "move":
        return e["k"]
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
        days[i]["b"].append([e["t"], e["dur"], kind(e), e["lab"]])
    return days


def build_tt():
    """A경로(후허하오터 왕복)만 페이지에 싣는다. 1안의 B경로는 검증기에는 살아 있지만
    전환 UI가 없어 시간표로는 쓰이지 않는다."""
    tt = {}
    for o in (1, 4, 5):
        tt["%dA" % o] = to_tt(V.build(o, "", "A"))
    return tt


def line():
    return "var TT=" + json.dumps(build_tt(), ensure_ascii=False, separators=(",", ":")) + ";"


if __name__ == "__main__":
    out = line()
    if "--write" in sys.argv:
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "index.html")
        src = open(p, encoding="utf-8").read()
        new, n = re.subn(r"^var TT=.*?;$", lambda m: out, src, count=1, flags=re.M)
        if n != 1:
            sys.exit("index.html에서 'var TT=...;' 줄을 찾지 못했습니다")
        open(p, "w", encoding="utf-8", newline="\n").write(new)
        print("index.html의 TT를 교체했습니다 — %d바이트" % len(out))
    else:
        print(out)
