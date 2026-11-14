// QA section C gap checks. Uses the built site served with production headers.
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
const require = createRequire("/home/user/blindspot/web/");
const { chromium } = require("playwright");
const PORT = "4181", BASE = `http://localhost:${PORT}`;
const srv = spawn(process.execPath, ["/home/user/blindspot/web/scripts/serve.mjs", "--headers"], { env: { ...process.env, PORT }, cwd: "/home/user/blindspot/web", stdio: "ignore" });
for (let i = 0; i < 50; i++) { try { if ((await fetch(BASE + "/")).ok) break; } catch {} await new Promise(r => setTimeout(r, 300)); }
const idx = await (await fetch(`${BASE}/data/index.json`)).json();
const sangrur = idx.districts.find(d => d.name === "Sangrur" && d.country === "IND").id;
const url = `${BASE}/?area=${sangrur}&from=2003-01&to=2025-11`;
const out = []; const rec = (id, ok, note = "") => { out.push({ id, ok, note }); console.log(`${ok ? "PASS" : "FAIL"}  ${id}  ${note}`); };
const browser = await chromium.launch();
try {
  // C2: widths, overflow, answer above the fold on a phone
  for (const [w, h] of [[360, 740], [390, 844], [414, 896], [768, 1024], [1024, 768], [1280, 800]]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } }); const p = await ctx.newPage();
    await p.goto(url); await p.waitForSelector('[data-testid="month-card"]', { timeout: 60000 });
    const ov = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth }));
    rec(`C2 no horizontal scroll ${w}x${h}`, ov.sw <= ov.iw, `scrollWidth ${ov.sw} <= ${ov.iw}`);
    if (w <= 414) {
      const top = await p.evaluate(() => { const r = document.querySelector('[data-testid="month-card"]').getBoundingClientRect(); return { top: r.top, bottom: r.bottom }; });
      rec(`C2 month card starts above the fold ${w}x${h}`, top.top < h, `top ${Math.round(top.top)} of ${h}`);
    }
    await ctx.close();
  }
  // C3: keyboard order on phone
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } }); const p = await ctx.newPage();
    await p.goto(url); await p.waitForSelector('[data-testid="month-card"]', { timeout: 60000 });
    const order = [];
    for (let i = 0; i < 14; i++) { await p.keyboard.press("Tab"); order.push(await p.evaluate(() => { const a = document.activeElement; return (a.getAttribute("data-testid") || a.getAttribute("aria-label") || a.textContent || a.tagName).trim().slice(0, 28); })); }
    console.log("   tab order (390px):", order.join(" > "));
    const iT = order.findIndex(s => /picker-toggle|Change area/.test(s)), iC = order.findIndex(s => /calendar|toggle-raw|Raw|Harmonized/.test(s));
    rec("C3 'Change area' is reachable by Tab", iT >= 0, `position ${iT}`);
    rec("C3 no keyboard trap (focus moves through 14 tabs to distinct elements)", new Set(order).size >= 8, `${new Set(order).size} distinct`);
    const vis = await p.evaluate(() => { const a = document.activeElement; const s = getComputedStyle(a); return s.outlineStyle !== "none" || s.boxShadow !== "none"; });
    rec("C3 focused element shows a focus indicator", vis);
    await ctx.close(); }
  // C6: invalid / empty input
  { const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } }); const p = await ctx.newPage();
    await p.goto(`${BASE}/`); await p.waitForSelector('[data-testid="district-search"]', { timeout: 60000 });
    await p.fill('[data-testid="district-search"]', "zzzzqqq"); await p.waitForTimeout(500);
    const txt = (await p.textContent("body")) || "";
    rec("C6 search with no match gives a message, not a blank", /no (district|match|result)|not found|try/i.test(txt) || (await p.locator('[data-testid="empty-state"]').count()) > 0, "");
    await p.click("text=Box");
    for (const [t, v] of [["box-n", "95"], ["box-s", "10"], ["box-e", "74"], ["box-w", "80"]]) await p.fill(`[data-testid="${t}"]`, v);
    await p.click('[data-testid="box-apply"]'); await p.waitForTimeout(800);
    const st = ((await p.textContent('[data-testid="status"]').catch(() => "")) || "").trim();
    rec("C6 impossible box (north 95, west > east) is refused with a message", st.length > 0 && !/Computed in your browser/.test(st), `status: "${st.slice(0, 90)}"`);
    await ctx.close(); }
  // C6: engine load failure
  { const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } }); const p = await ctx.newPage();
    const errs = []; p.on("pageerror", e => errs.push(e.message));
    await p.route("**/*.wasm", r => r.abort());
    await p.goto(url); await p.waitForTimeout(6000);
    const body = ((await p.textContent("body")) || "").length;
    rec("C6 page still renders district view when the DuckDB engine is blocked", body > 500, `${body} chars, ${errs.length} uncaught errors`);
    await ctx.close(); }
  // C7: cold load under throttling
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } }); const p = await ctx.newPage(); const cdp = await ctx.newCDPSession(p);
    await cdp.send("Network.enable"); await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 });
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    let bytes = 0; p.on("response", async r => { try { const b = r.headers()["content-length"]; if (b) bytes += +b; } catch {} });
    const t0 = Date.now(); await p.goto(url); await p.waitForSelector('[data-testid="month-card"]', { timeout: 120000 });
    const tCard = Date.now() - t0;
    await p.waitForSelector('[data-testid="calendar"]', { timeout: 120000 }); const tCal = Date.now() - t0;
    console.log(`   cold load, 390px, ~1.6 Mbps/150 ms/4x CPU: month card ${(tCard / 1000).toFixed(1)} s, calendar ${(tCal / 1000).toFixed(1)} s, ~${(bytes / 1048576).toFixed(1)} MiB by content-length`);
    rec("C7 month card visible within 20 s on throttled mobile (QA budget, not a product target)", tCard < 20000, `${(tCard / 1000).toFixed(1)} s`);
    await ctx.close(); }
} finally { await browser.close(); srv.kill(); }
const bad = out.filter(o => !o.ok); console.log(`\n${out.length - bad.length}/${out.length} QA browser checks passed`); process.exit(bad.length ? 1 : 0);
