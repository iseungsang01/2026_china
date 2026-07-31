# -*- coding: utf-8 -*-
"""guide.html + guide-data.js 정적 점검.

사용법:  python tools/check_guide.py

인솔서는 시각(TT4)과 본문(guide-data.js)이 따로 있고 일정 라벨의 부분 문자열로 붙는다.
라벨이 바뀌면 본문이 조용히 사라지고(오류도 안 난다), 「점심」처럼 여러 날에 겹치는 키는
엉뚱한 날에 붙는다. 그 둘을 여기서 잡는다.

검사 항목
  1. TT4가 검증기와 동기화돼 있는가
  2. G의 날짜 키가 실제 일정 날짜와 맞는가
  3. items의 키가 그날 일정에 실제로 붙는가 (안 붙거나 여러 항목에 걸치면 지적)
  4. 본문 HTML의 태그 균형
  5. 링크가 http(s):// 또는 tel: 로 시작하는가
  6. guide.html이 참조하는 것들이 실재하는가
"""
import re, sys, io, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

HTML = open(os.path.join(ROOT, "guide.html"), encoding="utf-8").read()
DATA = open(os.path.join(ROOT, "guide-data.js"), encoding="utf-8").read()
fails = []


def check(name, bad):
    print("  %-34s %s" % (name, "통과" if not bad else "%d건" % len(bad)))
    for b in bad:
        print("      · %s" % b)
    fails.extend(bad)


# ---------- 1. TT4 동기화 ----------
import gen_timetable  # noqa: E402

want = gen_timetable.line4()
have = re.search(r"^var TT4=.*?;$", HTML, re.M)
check("시간표 · 검증기 동기화",
      [] if have and have.group(0) == want
      else ["TT4가 검증기와 다릅니다 — python tools/gen_timetable.py --write 를 실행하세요"])

# 구 4안 키("4A")는 2026-07-30 재설계로 없어졌다. TT4가 동결돼 있으므로
# guide.html에 들어 있는 값을 그대로 읽는다 (gen_timetable.GUIDE_PLAN 주석 참조).
tt4 = gen_timetable.guide_tt()
days = [d["d"] for d in tt4]

# ---------- 2. G의 날짜 키 ----------
gdays = re.findall(r"^G\['([\d/]+)'\]=\{", DATA, re.M)
bad = ["G['%s'] — 일정에 없는 날짜입니다" % d for d in gdays if d not in days]
bad += ["%s — 본문이 없습니다" % d for d in days if d not in gdays]
check("일자 %d개" % len(gdays), bad)

# ---------- 3. items 키가 일정에 붙는가 ----------
# 각 G[...] 블록에서 items 안의 키만 뽑는다. 키는 들여쓰기 두 칸 뒤 '...':{ 형태다.
blocks = re.split(r"^G\['([\d/]+)'\]=\{", DATA, flags=re.M)
keys_by_day, total = {}, 0
for i in range(1, len(blocks), 2):
    day, body = blocks[i], blocks[i + 1]
    m = re.search(r"\n items:\{(.*?)\n \},\n pack:", body, re.S)
    seg = m.group(1) if m else ""
    keys_by_day[day] = re.findall(r"^  '([^']+)':\{", seg, re.M)
    total += len(keys_by_day[day])

bad = []
for d in tt4:
    labs = [b[3] for b in d["b"]]
    for k in keys_by_day.get(d["d"], []):
        kk = k.split("|")[-1]        # '8/13|점심' → '점심'
        if "|" in k and k.split("|")[0] != d["d"]:
            bad.append("[%s] '%s' — 날짜 접두사가 이 날과 다릅니다" % (d["d"], k))
            continue
        hit = [x for x in labs if kk in x]
        if not hit:
            bad.append("[%s] '%s' — 이 날 일정에 없는 라벨이라 본문이 안 붙습니다" % (d["d"], k))
        elif len(hit) > 1:
            bad.append("[%s] '%s' — %d개 항목(%s)에 걸립니다"
                       % (d["d"], k, len(hit), " / ".join(hit)))
check("본문 %d개가 일정에 붙는가" % total, bad)

# 어느 본문도 안 붙은 활동·식사
naked = []
for d in tt4:
    ks = [k.split("|")[-1] for k in keys_by_day.get(d["d"], [])]
    for b in d["b"]:
        if b[2] in ("activity", "meal") and not any(k in b[3] for k in ks):
            naked.append("%s %s" % (d["d"], b[3]))
worth = sum(1 for d in tt4 for b in d["b"] if b[2] in ("activity", "meal"))
print("  %-34s %d/%d개" % ("본문이 붙은 활동·식사", worth - len(naked), worth))
for n in naked:
    print("      · 본문 없음: %s" % n)

# ---------- 4. HTML 태그 균형 ----------
VOID = {"br", "img", "input", "hr", "meta", "link"}
bad, stack = [], []
html = "".join(re.findall(r"'([^']*)'", DATA))
for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)[^>]*?(/?)>", html):
    closing, tag, self_close = m.group(1), m.group(2).lower(), m.group(3)
    if tag in VOID or self_close:
        continue
    if closing:
        if stack and stack[-1] == tag:
            stack.pop()
        else:
            bad.append("</%s> 짝이 안 맞음 (주변: %s)" % (tag, html[max(0, m.start() - 40):m.start()][-40:]))
    else:
        stack.append(tag)
if stack:
    bad.append("안 닫힌 태그 %s" % stack[:8])
check("본문 HTML 구조", bad[:10])

# ---------- 5. 링크가 확인된 도메인인가 ----------
# 이 문서의 링크는 전부 2026-07-30에 접속을 확인한 것이다. 새 도메인이 들어오면
# 확인을 거쳤는지 묻기 위해 여기서 걸린다 — 확인했다면 ALLOW에 추가할 것.
ALLOW = {
    "www.12306.cn",              # 중국철도 영문
    "ticket.dpm.org.cn",         # 자금성 매표
    "www.dpm.org.cn",            # 고궁박물원
    "www.bjgyol.com.cn",         # 창유공원 (이화원·천단)
    "www.summerpalace-china.com",
    "www.ixsw.cn",               # 샹사완
    "www.bcia.com.cn",           # 수도공항
    "m.dianping.com",            # 大众点评
    "www.weather.com.cn",        # 中国天气网
    "overseas.mofa.go.kr",       # 주중대사관
    "www.0404.go.kr",            # 해외안전여행
    "www.amap.com",              # 가오더 지도
}
urls = set(re.findall(r"https?://[^\s'\"<>]+", DATA))
tels = set(re.findall(r"tel:\+?\d+", DATA))
bad = []
for u in urls:
    host = u.split("/")[2]
    if host not in ALLOW:
        bad.append("확인되지 않은 도메인: %s — 접속을 확인하고 ALLOW에 넣으세요" % host)
for t in tels:
    if not re.fullmatch(r"tel:\+?\d{3,15}", t):
        bad.append("전화 링크 형식: %s" % t)
check("링크 %d개 · 전화 %d개" % (len(urls), len(tels)), sorted(set(bad)))

# ---------- 6. guide.html 참조 ----------
bad = []
for need in ("guide-data.js", "var TT4=", "COVER", "REF", "G[", "id=\"nav\"", "id=\"main\""):
    if need not in HTML:
        bad.append("guide.html에 '%s'가 없습니다" % need)
for need in ("var COVER", "var REF", "G['8/10']"):
    if need not in DATA:
        bad.append("guide-data.js에 '%s'가 없습니다" % need)
if not os.path.exists(os.path.join(ROOT, "guide-data.js")):
    bad.append("guide-data.js가 없습니다")
check("파일 참조", bad)

# ---------- 7. index.html에서 인솔서로 가는 길 ----------
IDX = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
check("index.html에서 연결",
      [] if "guide.html" in IDX else ["index.html에 guide.html 링크가 없습니다"])

print()
if fails:
    print("문제 %d건" % len(fails))
    sys.exit(1)
print("전부 통과")
