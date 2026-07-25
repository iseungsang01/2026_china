# -*- coding: utf-8 -*-
"""index.html 정적 점검. 빌드도 테스트도 없는 저장소라 이 스크립트가 회귀 방지선이다.

사용법:  python tools/check_page.py

검사 항목
  1. getElementById로 참조하는 id가 실제로 존재하는가
     — 존재하지 않으면 그 함수는 TypeError로 중단된다. 실제로 cf6b32b에서
       지도 라벨(mn-grass·mn-desert)을 지우고 참조만 남겨 setOrder()가 매번 죽었다.
  2. open_('x')로 여는 시트가 SHEET에 있는가
  3. hidden 속성이 display 규칙에 덮이지 않는가
     — .cbtn{display:block}이 [hidden]을 이겨 빈 버튼이 보이던 문제
  4. 시트 HTML의 태그 균형과 표의 열 개수
  5. TT(시간표)가 검증기와 동기화돼 있는가
"""
import re, sys, io, os, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
fails = []


def check(name, bad):
    print("  %-32s %s" % (name, "통과" if not bad else "%d건" % len(bad)))
    for b in bad:
        print("      · %s" % b)
    fails.extend(bad)


# ---------- 1. getElementById 대상 존재 ----------
ids = set(re.findall(r'\bid="([\w-]+)"', SRC))
ids |= set(re.findall(r"\bid='([\w-]+)'", SRC))
refs = set(re.findall(r"getElementById\('([\w-]+)'\)", SRC))
# 'ob-'+i 처럼 조립하는 것은 접두사로 처리
dynamic = set(re.findall(r"getElementById\('([\w-]+)'\+", SRC))
missing = sorted(r for r in refs - ids if not any(r.startswith(d) for d in dynamic))
check("getElementById 대상 %d개" % len(refs),
      ["없는 id: %s — 참조하는 함수가 TypeError로 중단됩니다" % m for m in missing])

for d in sorted(dynamic):
    got = sorted(i for i in ids if i.startswith(d))
    if not got:
        fails.append("조립 id '%s...'에 맞는 요소가 없음" % d)
if dynamic:
    print("  %-32s %s" % ("조립 id 접두사", ", ".join(sorted(dynamic)) or "없음"))

# ---------- 2. 시트 참조 ----------
region = SRC[SRC.index("var SHEET={"):SRC.index("function open_(k){")]
parts = re.split(r"\n (\w+):\{title:", region)
sheets = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
opened = set(re.findall(r"open_\('(\w+)'\)", SRC))
check("시트 %d개 · 링크 %d개" % (len(sheets), len(opened)),
      ["open_('%s') — SHEET에 없음" % s for s in sorted(opened - set(sheets))])

# ---------- 3. hidden 이 display 규칙에 덮이지 않는가 ----------
bad = []
if not re.search(r"\[hidden\]\s*\{[^}]*display:\s*none", SRC):
    hidden_cls = re.findall(r'class="([^"]+)"[^>]*\shidden\b', SRC) + \
                 re.findall(r'\shidden\b[^>]*class="([^"]+)"', SRC)
    for cls in hidden_cls:
        for c in cls.split():
            if re.search(r"\.%s\{[^}]*display:\s*(block|flex|grid|inline)" % re.escape(c), SRC):
                bad.append("hidden 요소의 .%s 규칙이 display를 지정해 그대로 보입니다" % c)
check("hidden 무력화", sorted(set(bad)))

# ---------- 4. 시트 HTML 구조 ----------
VOID = {"br", "img", "input", "hr", "meta", "link"}
bad = []
for name, body in sheets.items():
    html = "".join(re.findall(r"'([^']*)'", body))
    stack = []
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)[^>]*?(/?)>", html):
        closing, tag, self_close = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or self_close:
            continue
        if closing:
            if stack and stack[-1] == tag:
                stack.pop()
            else:
                bad.append("[%s] </%s> 짝이 안 맞음" % (name, tag))
        else:
            stack.append(tag)
    if stack:
        bad.append("[%s] 안 닫힌 태그 %s" % (name, stack))
    for t in re.findall(r"<table>.*?</table>", html, re.S):
        head = re.search(r"<thead>.*?</thead>", t, re.S)
        if not head:
            continue
        ncol = len(re.findall(r"<th[ >]", head.group(0)))
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t.split("</thead>")[-1], re.S):
            n = 0
            for a in re.findall(r"<td([^>]*)>", tr):
                cs = re.search(r'colspan="(\d+)"', a)
                n += int(cs.group(1)) if cs else 1
            if n and n != ncol:
                bad.append("[%s] 표 열 %d ≠ 헤더 %d — %s" % (name, n, ncol, tr[:50]))
check("시트 HTML 구조", bad)

# ---------- 5. TT 동기화 ----------
import gen_timetable  # noqa: E402
want = gen_timetable.line()
have = re.search(r"^var TT=.*?;$", SRC, re.M)
check("시간표 · 검증기 동기화",
      [] if have and have.group(0) == want
      else ["TT가 검증기와 다릅니다 — python tools/gen_timetable.py --write 를 실행하세요"])

print()
if fails:
    print("문제 %d건" % len(fails))
    sys.exit(1)
print("전부 통과")
