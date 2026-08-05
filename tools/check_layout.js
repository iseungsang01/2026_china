/* 화면 점검 — 폰·노트북 뷰포트에서 index.html을 실제로 그려 보고 재는 스크립트.
   check_page.py가 소스를 보는 정적 점검이라면, 이쪽은 브라우저가 계산한 결과를 본다.

   쓰는 법 (저장소 밖 아무 폴더에서):
     npm i playwright && npx playwright install chromium
     node <저장소>/tools/check_layout.js
   스크린샷은 실행한 폴더에 shot-*.png로 떨어진다. 서버는 필요 없다 — file:// 로 연다
   (외부 요청이 0인 페이지라 그대로 열린다).

   잡는 것
     · 시간 격자가 한 화면에 들어오는가 (데스크톱) / 글이 살아 있는가 (폰)
     · 블록끼리 겹치거나 글이 반 줄 잘리지 않는가
     · 표가 화면 밖으로 넘치지 않는가 — 3열 이상 표에는 class="stack"이 필요하다
     · 콘솔 에러 · 페이지 예외 */

const path = require('path');
/* playwright는 이 저장소가 아니라 「실행한 폴더」에 설치한다 (여기에는 node_modules를 두지 않는다).
   node는 스크립트 위치 기준으로만 모듈을 찾으므로 실행 폴더도 뒤지게 해 준다. */
module.paths.push(path.join(process.cwd(), 'node_modules'));
let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) {
  console.error('playwright가 없습니다. 아무 폴더에서:\n' +
    '  npm i playwright && npx playwright install chromium\n' +
    '  node ' + __filename);
  process.exit(2);
}

const URL = 'file:///' + path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/');
const SHEETS = ['pre', 'trip', 'chk', 'resv', 'prep', 'sch', 'move', 'onsite', 'food', 'planb'];

const CASES = [
  { name: 'phone-390x844', viewport: { width: 390, height: 844 }, mobile: true },
  { name: 'phone-land-844x390', viewport: { width: 844, height: 390 }, mobile: true },
  { name: 'laptop-1280x800', viewport: { width: 1280, height: 800 } },
  { name: 'desktop-1512x860', viewport: { width: 1512, height: 860 } },
];

/* 시간 격자 — 페이지 안에서 잰다 */
function measureGrid() {
  const q = s => document.querySelector(s);
  const blocks = [...document.querySelectorAll('.blk')];
  let tiny = 0; const clipped = [], overlap = [];
  for (const b of blocks) {
    if (b.classList.contains('tiny')) { tiny++; continue; }
    if (b.scrollHeight > b.clientHeight + 1)
      clipped.push(b.textContent.slice(0, 20) + ` (${b.clientHeight}→${b.scrollHeight})`);
  }
  for (const col of document.querySelectorAll('.tgc.day .tgb')) {
    const rs = [...col.querySelectorAll('.blk')]
      .map(e => ({ t: e.offsetTop, b: e.offsetTop + e.offsetHeight, x: e.textContent.slice(0, 14) }))
      .sort((a, b) => a.t - b.t);
    for (let i = 1; i < rs.length; i++)
      if (rs[i - 1].b > rs[i].t + 0.5) overlap.push(`${rs[i - 1].x} ↔ ${rs[i].x}`);
  }
  return {
    격자: q('.tgb').offsetHeight, 열: Math.round(q('.tgc.day').getBoundingClientRect().width),
    격자바닥: Math.round(q('.tgwrap').getBoundingClientRect().bottom), 창높이: innerHeight,
    한화면: q('.tgwrap').getBoundingClientRect().bottom <= innerHeight,
    블록: blocks.length, 글숨김: tiny, 잘림: clipped, 겹침: overlap,
  };
}

/* 표 — 상자 밖으로 넘치는 것을 찾는다 */
function measureTables() {
  const bad = [];
  document.querySelectorAll('.sh-b .tw').forEach(w => {
    if (w.scrollWidth > w.clientWidth + 1) {
      const t = w.querySelector('table');
      const cols = t.querySelector('thead tr') ? t.querySelector('thead tr').children.length : '?';
      bad.push(`${cols}열 표가 ${w.scrollWidth}px (상자 ${w.clientWidth}px)` +
        (t.classList.contains('stack') ? '' : ' — class="stack"이 없습니다'));
    }
  });
  return bad;
}

(async () => {
  const browser = await chromium.launch();
  let fails = 0;
  for (const c of CASES) {
    const ctx = await browser.newContext({
      viewport: c.viewport, isMobile: !!c.mobile, hasTouch: !!c.mobile, deviceScaleFactor: 2,
    });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
    await page.goto(URL);

    console.log('\n== ' + c.name + ' ==');
    for (const k of SHEETS) {
      await page.evaluate(s => open_(s), k);
      await page.waitForTimeout(120);
      const over = await page.evaluate(measureTables);
      if (over.length) { fails += over.length; console.log(`  [${k}] ` + over.join(' / ')); }
      if (k === 'sch') {
        const g = await page.evaluate(measureGrid);
        console.log('  [sch] ' + JSON.stringify(g));
        if (g.잘림.length || g.겹침.length) fails += g.잘림.length + g.겹침.length;
        if (!c.mobile && !g.한화면) { fails++; console.log('  [sch] 격자가 한 화면을 넘습니다'); }
        await page.screenshot({ path: `shot-sch-${c.name}.png` });
      }
    }
    if (errs.length) { fails += errs.length; console.log('  !! 에러: ' + errs.join(' | ')); }
    await ctx.close();
  }
  await browser.close();
  console.log(fails ? `\n문제 ${fails}건` : '\n전부 통과');
  process.exit(fails ? 1 : 0);
})();
