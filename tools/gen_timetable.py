# -*- coding: utf-8 -*-
"""verify_itinerary.py의 build()에서 index.html의 TT(시간표) 데이터를 생성한다.
손으로 고치면 검증기와 어긋나므로 항상 이 스크립트로 만든다.

사용법:  python tools/gen_timetable.py          # TT 한 줄을 표준출력에 찍는다
         python tools/gen_timetable.py --write  # index.html의 TT 줄을 교체한다

guide.html(인솔서)의 TT4도 여기서 만든다. 2026-07-31에 확정안이 1V로 정해져
GUIDE_PLAN="1V"로 동결을 풀었다 — 인솔서 본문(guide-data.js)도 같은 날 1V 기준으로
다시 썼다. 라벨이 어긋나면 check_guide.py가 잡는다."""
import sys, io, os, json, re

if __name__ == "__main__":      # import될 때 stdout을 건드리지 않는다
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_itinerary as V

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = ["8/10", "8/11", "8/12", "8/13", "8/14"]
TT4_RE = r"^var TT4=.*?;$"
# None이면 TT4를 재생성하지 않고 guide.html의 현재 값을 동결로 취급한다.
# 확정안 1V (2026-07-31). 바꾸면 guide-data.js도 함께 다시 써야 한다.
GUIDE_PLAN = "1V"


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
        days[i]["b"].append([e["t"], e["dur"], kind(e), e["lab"]])
    return days


def build_tt():
    """검증기의 PLANS를 그대로 따라간다. 대안 플랜(1A·2A·2B)은 검증기에만 남아 있고
    페이지에는 PAGE_PLANS(확정안)만 싣는다 — cleanup-plan-1v.md 참조."""
    return {code: to_tt(V.build(o, var)) for o, var, code, _pkg, _nm in V.PLANS}


# index.html에 싣는 플랜. 화면이 1V 단일이 된 뒤로는 하나뿐이다.
PAGE_PLANS = ("1V",)


def line():
    tt = build_tt()
    page = {k: tt[k] for k in PAGE_PLANS}
    return "var TT=" + json.dumps(page, ensure_ascii=False, separators=(",", ":")) + ";"


def frozen4():
    """guide.html에 지금 들어 있는 TT4 줄. 동결 중에는 이것이 곧 정답이다."""
    src = open(os.path.join(ROOT, "guide.html"), encoding="utf-8").read()
    m = re.search(TT4_RE, src, re.M)
    if not m:
        sys.exit("guide.html에서 'var TT4=' 줄을 찾지 못했습니다")
    return m.group(0)


def line4():
    """guide.html(인솔서)용 TT4.
    ⚠️ GUIDE_PLAN이 None인 동안에는 guide.html의 현재 값을 그대로 돌려준다. 즉
    check_guide.py의 「시간표 · 검증기 동기화」 검사는 **동결 중에는 아무것도 검증하지 않는다.**
    구판 인솔서가 계속 통과하게 하려는 의도적 조치이니, 재타깃할 때 반드시 되살릴 것."""
    if GUIDE_PLAN is None:
        return frozen4()
    return "var TT4=" + json.dumps(build_tt()[GUIDE_PLAN], ensure_ascii=False,
                                   separators=(",", ":")) + ";"


def guide_tt():
    """TT4의 내용(일자 배열). check_guide.py가 날짜 키·라벨 대조에 쓴다."""
    return json.loads(line4()[len("var TT4="):-1])


# (파일, 바꿀 줄의 정규식, 넣을 내용을 만드는 함수)
TARGETS = [("index.html", r"^var TT=.*?;$", line)]
if GUIDE_PLAN is not None:
    TARGETS.append(("guide.html", TT4_RE, line4))


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
        if GUIDE_PLAN is None:
            print("guide.html의 TT4는 동결 상태라 건드리지 않았습니다 (GUIDE_PLAN=None)")
    else:
        print(line())
