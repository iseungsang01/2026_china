# -*- coding: utf-8 -*-
"""최종안(F)의 물리적 성립 여부를 7개 라운드로 검증한다.
사용법:  python tools/verify_itinerary.py

확정 전제: 8/10 PEK T3 14:00 도착 / 8/14 10:40 출발, 고속철 1등석.
소요시간(DUR)은 모두 (낙관, 보수) 쌍이며 배치는 보수치를 쓴다.

구성 (2026-08-01 3차 개편 · 8안 비교 체제를 전부 폐기하고 단일 최종안으로 좁혔다)

**골격 — 「후허하오터 선행 · 베이징 후행」 (사용자 결정 2026-08-01)**
  8/10 (월)  도착 → 저녁 고속철로 후허하오터 이동. 관광 없음 — 월요일 휴관과 무관해진다
  8/11 (화)  Klook 샹사완 당일 (08:00~20:00 상품 고정)
  8/12 (수)  후허하오터 → 우란차부 → 화산 → 저녁 고속철로 베이징 (뒤로 되돌지 않는 동선)
  8/13 (목)  베이징 종일 — 자금성(오픈런) · 천단 · 이화원 · 베이징덕
  8/14 (금)  첸먼에서 바로 T3 (공항 호텔 없음)

이 골격의 값어치 둘:
  ① 도착일 25분 마진 사슬(구판 천단)이 사라진다 — 8/10 저녁 편은 후속이 4편이라 항공
     지연에 강하다.
  ② 베이징 관광이 8/13 온전한 하루에 들어간다 — 구판은 10:09 도착 후 반나절이었다.

**사용자 지시 (2026-07-31 ~ 2026-08-01)**
  · 사막 필수 · 링크 예약 원칙(전화 예약 배제 — 그 대가로 사막의 밤이 빠진다)
  · 화산 포함 · 베이징은 자금성 · 이화원 · 천단
  · **숙소 이동 최소화** — 후허하오터 2박 + 첸먼 2박, 숙소 2곳 · 짐 싸기 1회
  · **택시는 1대만 운용** — 성인 4인 + 캐리어라 일반 세단이 안 되고 **디디 6인승** 전제
  · **베이징덕 1회** — 8/13 저녁 첸먼(숙소 옆)에 배치해 짐 동선과 겹치지 않는다

**열차 시각 출처** — hao86 제3자 시각표 (2026-08-01 조회). 12306 공식이 아니므로
  예매 시(Trip.com) 시각을 최종 확정하고 어긋나면 이 파일을 고칠 것.
  G2486만은 2026-07-31 조회(바오터우 17:36발)와 교차 일치해 신뢰도가 높다.
"""
import sys, io

if __name__ == "__main__":      # import될 때 stdout을 건드리지 않는다
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

M = lambda s: int(s[:2]) * 60 + int(s[3:])
HM = lambda t: "%02d:%02d" % ((int(t) // 60) % 24, int(t) % 60)

TOL = 60  # 허용 오차 상한 (분)
DAYS = ["8/10", "8/11", "8/12", "8/13", "8/14"]

# (낙관, 보수) 소요시간 - 2026-07~08 웹 검증치. `.est`는 실측 미확보.
DUR = {
    "immig":         (45, 75),
    # T3 → 베이징북역. 디디 6인승 · 약 28km `.est`
    "car_apt_bjns":  (50, 70),
    # G2485 베이징북 17:48 → 후허하오터동 20:32 (hao86 · 예매 시 확정)
    "rail_bj_hh":    (150, 164),
    # 후허하오터동역 → 위취안구 구시가 (사이상라오제 도보권)
    "car_hhstn_old": (15, 20),
    # D1006 후허하오터동 08:26 → 우란차부 09:11 (hao86 · 아침 D편 다수)
    "rail_hh_ulcb":  (45, 45),
    "car_ulcb_volc": (60, 75),    # 우란차부역 → 화산 경구 직통버스 · 85km
    "car_volc_ulcb": (60, 75),    # 화산 경구 → 우란차부역
    # G2486 우란차부 19:29 → 베이징북 21:19 (hao86 · 바오터우 17:36발과 교차 일치)
    "rail_ulcb_bj":  (110, 110),
    # 베이징북 → 첸먼. 밤이라 정체 없음. 디디 6인승 `.est`
    "car_bjns_qm":   (20, 30),
    # 도보 — R3의 차량 피로 집계에서 빼야 한다
    "walk_qm_tam":   (20, 25),    # 첸먼 → 천안문 광장 남측
    "car_gg_tt":     (20, 30),    # 자금성 신무문 → 천단 동문 `.est`
    "car_tt_yhy":    (40, 55),    # 천단 → 이화원 `.est`
    "car_yhy_qm":    (35, 50),    # 이화원 → 첸먼 `.est`
    # 첸먼 → T3. 새벽 공항고속 `.est` — 유일하게 실측이 없는 출국 사슬
    "car_qm_t3":     (40, 55),
    # 후허하오터 ↔ 샹사완 (Klook 상품 차량 · 실측 2.5h · 보수 3h)
    "car_hh_ds":     (150, 180),
}
# 이동 가능 시간대 06:00 ~ 익일 02:00 (2026-07-30 사용자 지시)
MOVE_WINDOW = (M("06:00"), 26 * 60)
XSW = (M("08:00"), M("18:30"))      # 샹사완 5/1~10/14 운영 (2026-07-31 확정)
# Klook 「후허하오터 샹사완 사막 일일 투어」(201940) — 08:00 출발 · 20:00 복귀가 상품 고정값이다.
# ₩101,700 · 무료취소 · 즉시확정 · 2026-08-02부터 이용 가능 (2026-07-31 실조회).
KLOOK_DAY = (M("08:00"), M("20:00"))
GUGONG = (M("08:30"), M("16:00"))   # 성수기 8:30 개관, 16:00 입장 마감, 월요일 휴관
GUGONG_CLOSE = M("17:00")
YIHE = (M("06:00"), M("20:00"))     # 성수기 6:00 개방 ~ 20:00 폐원 (2026-08-01 재확인)
YIHE_LAST = M("19:00")              # 입장 마감
YIHE_HALL_LAST = M("18:00")         # 불향각 등 내부 경점 마감
TIANTAN_ENTRY_LAST = M("17:30")     # 경점(기년전·회음벽·환구) 입장 마감 · 통표 34元
TIANTAN_CLOSE = M("18:00")          # 경점 폐문
# 천안문 광장 — 자금성 예약 기록이 있으면 별도 광장 예약 없이 진입한다 (2026-08-01 확인)
TAM = (M("06:00"), M("20:00"))
VOLC = (M("07:30"), M("20:00"))     # 우란하다 화산군 — 17:30 매표 종료, 18:00 입원 종료
VOLC_LAST = M("18:00")
VOLC_NEED = 185                     # 관람에 필요한 최소 시간 (구판 검증치)
# 우란차부역 ↔ 화산 직통버스 (2026-07-16 개통) — 편도 35元 · 하루 여섯 편이 전부
VOLC_BUS_OUT = (M("10:10"), M("11:40"), M("13:10"))
VOLC_BUS_BACK = (M("16:00"), M("17:00"), M("18:00"))
# 열차 화이트리스트 — hao86 2026-08-01 조회. 일정을 먼저 짜고 편을 맞추는 순서이므로
# 어긋나면 지적이 아니라 NOTES로 가장 가까운 편을 알린다. 예매 시 12306/Trip.com에서 확정.
RAIL_BJ_HH_OUT = {M("16:55"): "G2495", M("17:48"): "G2485", M("19:03"): "G2457",
                  M("19:42"): "G2475", M("20:58"): "G2477"}
RAIL_HH_ULCB_OUT = {M("08:08"): "D1004", M("08:26"): "D1006", M("08:55"): "G3780",
                    M("08:59"): "D1008"}
RAIL_ULCB_BJ_OUT = {M("19:29"): "G2486", M("20:24"): "G2478", M("21:11"): "D1034"}
SSLJ_LAST = M("22:00")              # 사이상라오제 점포 폐점 (麦香村 21:30 근거의 보수 추정)
SHAOMAI_LATE = M("21:30")


def E(d, t, dur, k, lab, pl="", key=None, pkg=False):
    """pkg=True는 **패키지 상품이 커버하는 구간**이라는 뜻이다.
    시간표에서 테두리로 묶어 「어디까지가 산 것이고 어디부터가 자력인지」를 보이게 한다."""
    return dict(d=d, t=M(t), dur=dur, k=k, lab=lab, pl=pl, key=key, pkg=pkg)


# 지적을 세 갈래로 나눈다. GIVEN은 설계가 알고 고른 포기, FIXED는 항공편이 고정해 버린 것.
GIVEN, FIXED = "(의도된 포기)", "(전 구성 공통)"
NOTES = []      # 라운드가 지적이 아니라 참고 수치를 남길 때

# 「1인 1,000元 언저리가 걸린 미확정」 — 단일안에도 이 관행은 유지한다
RISK = {
    # 2026-07-31 Klook 상품 페이지 「포함사항」 실확인:
    #   포함 — 왕복 버스 · 샹사완 입장권 + 왕복 케이블카 + 셴사다오 엔터테인먼트 패키지 ·
    #          중국어 기사 · 여행 상해보험(10만元)
    #   불포함 — 식사 · 웨사다오 · 추가 요금 · 복장/장비
    #   ⚠️ 단체가 6인 미만이면 운전기사만 배정되고 가이드가 관광지에 들어가지 않는다.
    "F": ("Klook 사막 상품이 <b>셴사다오 등급</b>이라 웨사다오가 빠지고(차액 약 120元), "
          "<b>6인 미만이면 가이드 없이 기사만</b> 배정된다 — 우리는 4인이다. "
          "웨사다오 추가 + 4인 식사로 현장 지출이 1,000元 언저리. "
          "돈과 별개의 최대 관문은 **자금성 8/6 20:00 오픈런**이다 — 실패하면 8/13 오전을 "
          "징산공원·경산 전망으로 바꾸고 취소표(매일 갱신)를 노린다"),
}


# ===================== 일정 =====================
def d0810():
    """8/10 (월) — 이동일. 관광이 없어 월요일 휴관(자금성·광장)과 무관하다.
    구판의 급소였던 「도착 25분 마진」 사슬이 사라졌다 — G2485를 놓쳐도
    19:03 · 19:42 · 20:58 후속이 있어 항공 지연이 일정을 무너뜨리지 않는다."""
    return [E("8/10", "14:00", 75, "transit", "PEK T3 도착 · 입국심사 · 수하물", "공항", "immig"),
            E("8/10", "15:15", 70, "move", "T3 → 베이징북역 (디디 6인승 · 예약콜)", "베이징", "car_apt_bjns"),
            E("8/10", "16:25", 25, "transit", "역 도착 · 발권 · 보안 (외국 여권은 유인 통로)", "베이징북역"),
            E("8/10", "16:50", 45, "meal", "역 구내 저녁 (개찰 17:33 시작 · 17:43 마감)", "베이징북역"),
            E("8/10", "17:48", 164, "move", "G2485 1등석 → 후허하오터동 (20:32 착)", "철도", "rail_bj_hh"),
            E("8/10", "20:32", 20, "transit", "하차 · 짐 · 택시 승차 (6인승)", "후허하오터동역"),
            E("8/10", "20:52", 20, "move", "역 → 구시가 호텔 (사이상라오제 50m)", "후허하오터", "car_hhstn_old"),
            E("8/10", "21:12", 18, "rest", "체크인 · 짐 정리 (여기서 2박)", "후허하오터"),
            E("8/10", "21:30", 30, "activity", "사이상라오제 첫 산책 · 통순대항 야식", "사이상라오제"),
            E("8/10", "22:30", 495, "sleep", "후허하오터 1박째 (구시가)", "후허하오터")]


def d0811():
    """8/11 (화) — Klook 샹사완 당일. 08:00 출발 · 20:00 복귀가 상품 고정값이라
    우리가 시각을 정하지 않는다. 경구 체류 6시간 · 17:00 퇴장이라 일몰(20:00)은 못 본다 —
    링크 예약 원칙의 대가다.

    ⚠️ 상품 페이지 실확인(2026-07-31): 포함은 입장권 + 왕복 케이블카 + 셴사다오 패키지이고
    웨사다오와 식사는 빠진다. 단체 6인 미만이면 운전기사만 배정 — 우리는 4인이다."""
    return [E("8/11", "07:00", 30, "meal", "조식", "후허하오터"),
            E("8/11", "07:30", 25, "move", "호텔 → 집합지 (신화광장 서쪽 중신은행 아래 · 택시 1대)", "후허하오터"),
            E("8/11", "08:00", 180, "move", "Klook 패키지 차량 → 샹사완", "차량", "car_hh_ds"),
            E("8/11", "11:00", 40, "transit", "화롄 접대센터 수속 · 팔찌 · 짐 위탁", "사막"),
            E("8/11", "11:40", 55, "meal", "점심 (불포함 · 현장 지출)", "사막"),
            E("8/11", "12:35", 65, "activity", "케이블카 → 셴사다오", "사막"),
            E("8/11", "13:40", 90, "activity", "낙타 타기", "사막"),
            E("8/11", "15:10", 105, "activity", "모래썰매 · 사막 액티비티", "사막"),
            E("8/11", "16:55", 5, "transit", "집합 · 인원 확인", "사막"),
            E("8/11", "17:00", 180, "move", "Klook 패키지 차량 → 후허하오터", "차량", "car_hh_ds"),
            E("8/11", "20:10", 70, "meal", "사오마이 저녁 (麦香村 · 06:30~21:30 종일)", "후허하오터"),
            E("8/11", "21:30", 30, "activity", "사이상라오제 야경", "사이상라오제"),
            E("8/11", "22:20", 500, "sleep", "후허하오터 2박째 (같은 호텔 — 짐 안 쌈)", "후허하오터")]


def d0812():
    """8/12 (수) — 화산을 「나가는 길」에 놓는다. 우란차부가 베이징~후허하오터 선상이라
    화산을 본 뒤 후허하오터로 되돌지 않고 그대로 동쪽 베이징행을 탄다.
    ⚠️ 이 날이 짐과 함께 움직이는 유일한 날이다 — 우란차부역 짐 보관을 전제로 하며
    보관소 유무는 아직 미확인이다 (없으면 경구 게스트센터 보관을 현장 협의)."""
    return [E("8/12", "06:40", 35, "meal", "조식 · 체크아웃 (짐 싸기 — 이번 여행 한 번뿐)", "후허하오터"),
            E("8/12", "07:15", 20, "move", "호텔 → 후허하오터동역 (택시 1대)", "후허하오터", "car_hhstn_old"),
            E("8/12", "07:35", 30, "transit", "발권 · 보안 · 대합실 (외국 여권은 유인 통로)", "후허하오터동역"),
            E("8/12", "08:26", 45, "move", "D1006 1등석 → 우란차부 (09:11 착)", "철도", "rail_hh_ulcb"),
            E("8/12", "09:11", 20, "transit", "하차 · 역 짐 보관 (보관소 확인 필요)", "우란차부역"),
            E("8/12", "09:31", 30, "meal", "역에서 이른 점심 조달 · 승차장", "우란차부역"),
            E("8/12", "10:10", 75, "move", "직통버스 → 우란하다 화산군 (편도 35元)", "차량", "car_ulcb_volc"),
            E("8/12", "11:25", 320, "activity", "화산 관람 (셔틀 30元 · 6·5·4·3호 화산 · 필요 185분)", "화산"),
            E("8/12", "16:45", 5, "transit", "귀환버스 승차장 집합", "화산"),
            E("8/12", "17:00", 75, "move", "직통버스 → 우란차부역", "차량", "car_volc_ulcb"),
            E("8/12", "18:15", 65, "meal", "역 저녁 · 짐 회수 · 발권 (개찰 19:14 시작)", "우란차부역"),
            E("8/12", "19:29", 110, "move", "G2486 1등석 → 베이징북 (21:19 착)", "철도", "rail_ulcb_bj"),
            E("8/12", "21:19", 20, "transit", "하차 · 택시 승차 (6인승)", "베이징북역"),
            E("8/12", "21:39", 30, "move", "베이징북 → 첸먼 호텔 (디디 6인승)", "베이징", "car_bjns_qm"),
            E("8/12", "22:09", 21, "rest", "체크인 · 짐 정리 (여기서 2박)", "첸먼"),
            E("8/12", "22:45", 495, "sleep", "베이징 1박째 (첸먼)", "베이징")]


def d0813():
    """8/13 (목) — 베이징 종일. 자금성이 열리는 요일이고(월요일 휴관), 아침 기차가 없어
    08:30 개관에 맞춰 들어간다. 짐 없는 날 — 숙소를 안 옮기므로 저녁 베이징덕이
    숙소 옆(첸먼)에서 끝난다.
    천안문 광장은 자금성 예약 기록으로 진입하므로 별도 광장 예약이 필요 없다 (2026-08-01 확인)."""
    return [E("8/13", "07:00", 40, "meal", "조식", "첸먼"),
            E("8/13", "07:40", 25, "move", "첸먼 → 천안문 광장 남측 (도보)", "베이징", "walk_qm_tam"),
            E("8/13", "08:05", 20, "activity", "천안문 광장 통과 (자금성 예약 기록으로 진입 · 여권 원본)", "천안문광장"),
            E("8/13", "08:25", 20, "transit", "오문 대기 · 검표", "자금성"),
            E("8/13", "08:45", 195, "activity", "자금성 관람 (08:30 개관 · 16:00 입장 마감 · 월요일 휴관)", "자금성"),
            E("8/13", "12:00", 55, "meal", "점심 (신무문 일대)", "베이징"),
            E("8/13", "12:55", 30, "move", "자금성 → 천단 동문 (택시 1대)", "베이징", "car_gg_tt"),
            E("8/13", "13:25", 115, "activity", "천단 관람 (통표 34元 · 기년전·회음벽·환구 · 17:30 입장 마감)", "천단"),
            E("8/13", "15:20", 55, "move", "천단 → 이화원 (택시 1대)", "베이징", "car_tt_yhy"),
            E("8/13", "16:15", 145, "activity", "이화원 관람 (19:00 입장 마감 · 내부 전각 18:00 마감 · 장랑·쿤밍호)", "이화원"),
            E("8/13", "18:40", 50, "move", "이화원 → 첸먼 (디디 6인승)", "베이징", "car_yhy_qm"),
            E("8/13", "19:30", 90, "meal", "베이징덕 저녁 (볜이팡 — 예약 권장 · 숙소 도보권)", "첸먼"),
            E("8/13", "21:00", 45, "activity", "첸먼다제 · 다잔란 야간 산책", "첸먼"),
            E("8/13", "22:15", 445, "sleep", "베이징 2박째 (같은 호텔 — 짐 안 쌈)", "베이징")]


def d0814():
    """출국일 — 첸먼에서 바로 T3. 공항 호텔을 없앤 대가가 이 새벽이다:
    06:20 출발(디디 6인승 예약콜) → 보수 07:15 도착으로 마지노선 08:40에 85분 여유.
    금요일 아침 정체가 걱정되면 06:00 출발로 당긴다."""
    return [E("8/14", "06:00", 20, "meal", "간단 조식 · 체크아웃 (짐은 전날 밤 정리)", "첸먼"),
            E("8/14", "06:20", 55, "move", "첸먼 → PEK T3 (디디 6인승 · 전날 예약콜)", "공항", "car_qm_t3"),
            E("8/14", "07:15", 205, "transit", "체크인 · 보안 · 출국심사 (10:40 출발)", "공항")]


def build(code="F"):
    """단일 최종안. code 인자는 gen_timetable.py와의 계약을 위해 남긴다."""
    return d0810() + d0811() + d0812() + d0813() + d0814()


# ===================== 검증 라운드 =====================
def R1(P, code=""):
    I, prev = [], None
    for e in P:
        if prev and e["d"] == prev["d"]:
            end = prev["t"] + prev["dur"]
            if e["t"] < end - 1:
                I.append("겹침 %s: %s(~%s) 위에 %s(%s)" % (e["d"], prev["lab"], HM(end), e["lab"], HM(e["t"])))
        prev = e
    return I


def R2(P, code=""):
    I = []
    for e in P:
        if e["k"] != "sleep":
            if e["t"] < MOVE_WINDOW[0] or e["t"] + e["dur"] > MOVE_WINDOW[1]:
                I.append("이동 가능 시간대(06:00~익일 02:00) 밖: %s %s %s~%s"
                         % (e["d"], e["lab"], HM(e["t"]), HM(e["t"] + e["dur"])))
        # 열차 시각은 화이트리스트와 대조한다 — 어긋나면 가장 가까운 편을 참고로 남긴다.
        for key, pool, nm in (("rail_bj_hh", RAIL_BJ_HH_OUT, "베이징북→후허하오터동"),
                              ("rail_hh_ulcb", RAIL_HH_ULCB_OUT, "후허하오터동→우란차부"),
                              ("rail_ulcb_bj", RAIL_ULCB_BJ_OUT, "우란차부→베이징북")):
            if e.get("key") == key:
                if e["t"] not in pool:
                    near = min(pool, key=lambda t: abs(t - e["t"]))
                    NOTES.append("%s %s 출발은 조회된 편에 없다 — 가장 가까운 편이 %s %s. "
                                 "예매 때 맞추면 되는 값이다" % (nm, HM(e["t"]), HM(near), pool[near]))
                else:
                    nxt = sorted(t for t in pool if t > e["t"])
                    NOTES.append("%s %s %s — 놓치면 후속 %s"
                                 % (nm, pool[e["t"]], HM(e["t"]),
                                    " · ".join("%s %s" % (pool[t], HM(t)) for t in nxt) or "없음"))
        if e["pl"] == "사막" and e["k"] == "activity" and any(
                w in e["lab"] for w in ("케이블카", "낙타", "썰매", "자유")):
            if e["t"] < XSW[0] or e["t"] + e["dur"] > XSW[1]:
                I.append("샹사완 운영(08:00~18:30) 밖: %s %s %s~%s"
                         % (e["d"], e["lab"], HM(e["t"]), HM(e["t"] + e["dur"])))
        # Klook 당일 패키지는 08:00 출발 · 20:00 복귀가 상품 고정값이라 우리가 못 바꾼다
        if "Klook 패키지" in e["lab"] and e["k"] == "move":
            if e["t"] < KLOOK_DAY[0]:
                I.append("Klook 당일 패키지는 08:00 출발 고정: %s %s" % (e["d"], HM(e["t"])))
            if e["t"] + e["dur"] > KLOOK_DAY[1]:
                I.append("Klook 당일 패키지는 20:00 복귀 고정: %s ~%s"
                         % (e["d"], HM(e["t"] + e["dur"])))
        if "자금성 관람" in e["lab"] and e["k"] == "activity":
            if e["t"] < GUGONG[0] or e["t"] > GUGONG[1]:
                I.append("자금성 운영(08:30 개관 · 16:00 입장 마감) 밖: %s" % HM(e["t"]))
            if e["t"] + e["dur"] > GUGONG_CLOSE:
                I.append("자금성 폐관(17:00) 초과: %s~%s" % (HM(e["t"]), HM(e["t"] + e["dur"])))
            if e["d"] == "8/10":
                I.append("자금성은 월요일 휴관 — 8/10은 월요일")
        if "이화원 관람" in e["lab"] and e["k"] == "activity":
            if e["t"] < YIHE[0] or e["t"] + e["dur"] > YIHE[1]:
                I.append("이화원 운영(06:00~20:00) 밖: %s~%s" % (HM(e["t"]), HM(e["t"] + e["dur"])))
            if e["t"] > YIHE_LAST:
                I.append("이화원 입장 마감(19:00) 초과: %s" % HM(e["t"]))
            if e["t"] > YIHE_HALL_LAST:
                NOTES.append("이화원 도착 %s — 내부 전각 마감(18:00)까지 %d분"
                             % (HM(e["t"]), YIHE_HALL_LAST - e["t"]))
        if "천단 관람" in e["lab"] and e["k"] == "activity":
            if e["t"] > TIANTAN_ENTRY_LAST:
                I.append("천단 경점 입장 마감(17:30) 초과: %s %s" % (e["d"], HM(e["t"])))
            if e["t"] + e["dur"] > TIANTAN_CLOSE:
                I.append("천단 경점 폐문(18:00) 초과: %s %s~%s" % (e["d"], HM(e["t"]), HM(e["t"] + e["dur"])))
        if "천안문 광장" in e["lab"] and e["k"] == "activity":
            if e["d"] == "8/10":
                I.append("천안문 광장은 월요일 폐쇄 — 8/10은 월요일")
            if e["t"] < TAM[0] or e["t"] + e["dur"] > TAM[1]:
                I.append("천안문 광장 개방(%s~%s `.est`) 밖: %s~%s"
                         % (HM(TAM[0]), HM(TAM[1]), HM(e["t"]), HM(e["t"] + e["dur"])))
        if "사이상라오제" in e["lab"] and e["k"] == "activity":
            if e["t"] + e["dur"] > SSLJ_LAST:
                I.append("사이상라오제 점포 폐점(22:00 추정) 초과: %s~%s"
                         % (HM(e["t"]), HM(e["t"] + e["dur"])))
        if "사오마이" in e["lab"] and e["k"] == "meal" and e["t"] + e["dur"] > SHAOMAI_LATE:
            I.append("사오마이 저녁 영업점 폐점(21:30) 초과: %s~%s"
                     % (HM(e["t"]), HM(e["t"] + e["dur"])))
        if "화산 관람" in e["lab"] and e["k"] == "activity":
            if e["t"] < VOLC[0] or e["t"] + e["dur"] > VOLC[1]:
                I.append("화산 개방(07:30~20:00) 밖: %s~%s" % (HM(e["t"]), HM(e["t"] + e["dur"])))
            if e["t"] > VOLC_LAST:
                I.append("화산 입원 마감(18:00) 초과: %s" % HM(e["t"]))
            if e["dur"] < VOLC_NEED:
                I.append("화산 체류 %d분 — 필요 %d분 미달" % (e["dur"], VOLC_NEED))
            else:
                NOTES.append("화산 체류 %d분 (필요 %d분 · 여유 %d분)"
                             % (e["dur"], VOLC_NEED, e["dur"] - VOLC_NEED))
        if e.get("key") == "car_ulcb_volc" and e["t"] not in VOLC_BUS_OUT:
            I.append("화산행 직통버스 시각(10:10·11:40·13:10)에 없음: %s" % HM(e["t"]))
        if e.get("key") == "car_volc_ulcb" and e["t"] not in VOLC_BUS_BACK:
            I.append("화산발 직통버스 시각(16:00·17:00·18:00)에 없음: %s" % HM(e["t"]))
    # 화산 귀환버스 → 저녁 열차 연결. 버스가 하루 세 편뿐이라 놓치면 대안이 없다.
    bus = [x for x in P if x.get("key") == "car_volc_ulcb"]
    rail = [x for x in P if x.get("key") == "rail_ulcb_bj"]
    if bus and rail:
        arr = bus[0]["t"] + bus[0]["dur"]           # 보수치 도착
        gate = rail[0]["t"] - 5                     # 개찰은 발차 5분 전 마감
        nxt = sorted(t for t in RAIL_ULCB_BJ_OUT if t > rail[0]["t"])
        if gate - arr < 45:
            I.append("화산 귀환버스 → 열차 연결이 빠듯: 버스 보수 도착 %s → 개찰 마감 %s = %d분"
                     % (HM(arr), HM(gate), gate - arr))
        else:
            NOTES.append("화산 귀환버스 → 열차 연결 %d분 (버스 보수 도착 %s · 개찰 마감 %s · "
                         "다음 편 %s)" % (gate - arr, HM(arr), HM(gate),
                                       HM(nxt[0]) if nxt else "없음"))
    return I


def R3(P, code=""):
    I, byday = [], {}
    for e in P:
        byday.setdefault(e["d"], []).append(e)
    for d, es in byday.items():
        car = sum(x["dur"] for x in es if x["k"] == "move"
                  and not (x.get("key") or "").startswith(("rail", "walk")))
        rail = sum(x["dur"] for x in es if (x.get("key") or "").startswith("rail"))
        walk = sum(x["dur"] for x in es if (x.get("key") or "").startswith("walk"))
        tail = " (도보 %dm 별도)" % walk if walk else ""
        if car > 300:
            I.append("[%s] 차량 이동 %dh%02dm — 5시간 초과, 이동 과부하%s" % (d, car // 60, car % 60, tail))
        elif car > 240:
            I.append("[%s] 차량 이동 %dh%02dm — 4시간 초과, 주의%s" % (d, car // 60, car % 60, tail))
        if car + rail > 480:
            I.append("[%s] 총 이동 %dh%02dm — 하루의 절반 초과%s" % (d, (car + rail) // 60, (car + rail) % 60, tail))
        for s in [x for x in es if x["k"] == "sleep"]:
            if s["dur"] < 420:
                I.append("[%s] 수면 %dh%02dm — 7시간 미만" % (d, s["dur"] // 60, s["dur"] % 60))
        for w in [x for x in es if x["k"] == "meal" and "조식" in x["lab"]]:
            if w["t"] < M("07:00"):
                mark = " %s 출국편 10:40 고정" % FIXED if d == "8/14" else ""
                I.append("[%s] 기상 %s — 이른 기상%s" % (d, HM(w["t"] - 30), mark))
    return I


def R4(P, code=""):
    """이동 구간에 누적 지연을 주입해 기차·폐장 시각을 놓치는지 확인"""
    I, byday = [], {}
    for e in P:
        byday.setdefault(e["d"], []).append(e)
    for d, es in byday.items():
        lag = 0
        for e in es:
            if e["k"] == "move" and e.get("key") and "rail" not in e["key"]:
                lo, hi = DUR[e["key"]]
                lag += max(0, hi - lo)          # 보수-낙관 폭만큼 밀릴 수 있다고 가정
            if (e.get("key") or "").startswith("rail") and lag > 0:
                buf = 0
                for p in es:
                    if p["k"] in ("meal", "transit", "rest") and p["t"] < e["t"]:
                        buf += p["dur"]
                if lag > buf:
                    I.append("[%s] 누적지연 %dm > 버퍼 %dm — %s 놓칠 위험" % (d, lag, buf, e["lab"]))
            if e["pl"] == "사막" and any(w in e["lab"] for w in ("케이블카", "낙타", "썰매")) and lag > 0:
                if e["t"] + e["dur"] + lag > XSW[1]:
                    I.append("[%s] 지연 %dm 시 폐장 전 %s 불가" % (d, lag, e["lab"]))
    return I


def R5(P, code=""):
    """오차 총량 <= 60분"""
    I, byday = [], {}
    for e in P:
        byday.setdefault(e["d"], []).append(e)
    for d, es in byday.items():
        span = sum(max(0, DUR[e["key"]][1] - DUR[e["key"]][0])
                   for e in es if e.get("key") in DUR and not e["key"].startswith("rail"))
        if span > TOL:
            I.append("[%s] 누적 불확실성 %dm — 허용치 %dm 초과" % (d, span, TOL))
    return I


def R6(P, code=""):
    """목표 달성 — 사용자 지시 (2026-08-01 최종)

    하드 제약: 사막 · 링크 예약 이동 · 화산 · 자금성 · 이화원 · 천단 · 베이징덕 1회 ·
    숙소 2곳(짐 싸기 1회) · 택시 1대 운용."""
    I, txt = [], " ".join(x["lab"] + x["pl"] for x in P)
    for name, key in [("사막", "사막"), ("낙타", "낙타"), ("모래썰매", "썰매"),
                      ("화산", "화산 관람"), ("자금성", "자금성 관람"),
                      ("이화원", "이화원 관람"), ("천단", "천단 관람"),
                      ("베이징덕", "베이징덕")]:
        if key not in txt:
            I.append("P0 미달: %s 없음 (하드 제약)" % name)
    # 「링크로 간다」는 사막행 차량 구간이 상품에 들어 있는가로 본다
    if not any(x.get("key") == "car_hh_ds" for x in P):
        I.append("P0 미달: 사막행 패키지 차량이 없음 (하드 제약 — 대중교통이 없어 자력으로는 못 간다)")
    # 숙소 2곳 — sleep 라벨의 도시가 둘이어야 한다
    stays = set()
    for x in P:
        if x["k"] == "sleep":
            stays.add(x["lab"].split(" ")[0])
    if len(stays) > 2:
        I.append("숙소가 %d곳 — 「숙소 이동 최소화」 위배: %s" % (len(stays), " · ".join(stays)))
    else:
        NOTES.append("숙소 %d곳 (%s) — 짐 싸기 1회" % (len(stays), " · ".join(sorted(stays))))
    # 사막의 밤은 「전화 예약 배제」의 대가다
    if "사막 일몰" not in txt:
        I.append("%s 사막 일몰·별밤 — 링크로 살 수 있는 사막 상품은 전부 당일 투어다. "
                 "경구 내 텐트는 전화뿐이고, 링크가 되는 경구 내 숙박은 연꽃호텔(1인 약 1,980元)"
                 "뿐이라 배제했다" % GIVEN)
    if "천안문 광장" not in txt:
        I.append("P1 미달: 천안문 광장 없음")
    if "만리장성" not in txt:
        I.append("%s 만리장성 — 낮에는 시간이 없고 야간 개방은 귀환 막차가 급소다" % GIVEN)
    if "승마" not in txt:
        I.append("%s 초원 승마 — 사용자 지시로 초원을 제외했다" % GIVEN)
    return I


def R7(P, code=""):
    """확정 항공편 기준 — 8/10 PEK 14:00 도착 / 8/14 10:40 출발."""
    I = []
    ARR, DEP = M("14:00"), M("10:40")
    # 8/10 — 도착 사슬이 저녁 열차 개찰에 닿는가. 보수 사슬 = 입국 + 차량 + 발권·보안.
    first_rail = [e for e in P if e["d"] == "8/10" and (e.get("key") or "").startswith("rail")]
    if first_rail:
        r = first_rail[0]
        gate = r["t"] - 5
        chain = DUR["immig"][1] + DUR["car_apt_bjns"][1] + 25
        done = ARR + chain
        if done > gate:
            I.append("8/10 보수 사슬 도착 %s — 개찰 마감 %s 초과. 후속 편으로 개첨"
                     % (HM(done), HM(gate)))
        else:
            NOTES.append("8/10 보수 사슬(입국 75 + 차량 70 + 발권·보안 25) 완료 %s / "
                         "개찰 마감 %s → 여유 %d분. 놓치면 19:03 · 19:42 · 20:58 후속"
                         % (HM(done), HM(gate), gate - done))
    need = DEP - 120
    for e in P:
        if e["d"] == "8/14" and "공항" in e["pl"] and e["k"] == "move":
            arr = e["t"] + e["dur"]
            if arr > need:
                I.append("공항 도착 %s — 출발 2시간 전(%s)보다 늦음" % (HM(arr), HM(need)))
            else:
                NOTES.append("공항 도착(보수) %s / 마지노선 %s → 여유 %d분"
                             % (HM(arr), HM(need), need - arr))
    return I


ROUNDS = [("R1 시각 연속성", R1), ("R2 운영시간·이동창", R2), ("R3 체력 현실성", R3),
          ("R4 지연 스트레스", R4), ("R5 오차 60분 이내", R5), ("R6 목표 달성", R6),
          ("R7 항공편 민감도", R7)]
# (TT 키, 패키지, 1인 값, 표시 이름) — TT 키는 gen_timetable.py와 index.html이 함께 쓴다
PLANS = [("F", "Klook 샹사완 당일 + 화산 자력", "₩101,700 + 100元",
          "후허하오터 선행 · 베이징 후행 — 숙소 2곳 · 베이징 종일 하루 확보")]


def main():
    total = 0
    for code, pkg, price, nm in PLANS:
        P = build(code)
        print("\n" + "=" * 76)
        print("[%s] %s" % (code, nm))
        print("      패키지: %s · 1인 %s" % (pkg, price))
        print("=" * 76)
        found = []
        for i, (rn, fn) in enumerate(ROUNDS, 1):
            del NOTES[:]
            iss = fn(P, code)
            found += iss
            print("  [%d/7] %-20s %s" % (i, rn, "통과" if not iss else "%d건" % len(iss)))
            for x in iss:
                print("         · %s" % x)
            for x in NOTES:
                print("         + %s" % x)
        given = [x for x in found if x.startswith(GIVEN)]
        fixed = [x for x in found if FIXED in x]
        real = len(found) - len(given) - len(fixed)
        print("  " + "-" * 72)
        print("  종합: %s" % ("전 라운드 통과" if not found else "%d건 지적" % len(found)))
        print("        의도된 포기 %d건 · 항공편 고정 %d건 · **실질 %d건**"
              % (len(given), len(fixed), real))
        print("  1,000元 리스크: %s" % RISK[code])
        SCORE[code] = dict(total=len(found), real=real)
        total += len(found)
    return total


SCORE = {}

if __name__ == "__main__":
    main()
