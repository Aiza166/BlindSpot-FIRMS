// End-to-end checks of every Must feature (PLAN §5) against the static export in out/.
// Usage: node e2e/run.mjs  (expects the server from scripts/serve.mjs on $BASE or http://localhost:4173)
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..");
const BASE = process.env.BASE ?? "http://localhost:4173";
const SHOTS = join(repo, "docs", "screenshots");
const ART = process.env.E2E_ARTIFACTS ?? join(here, "artifacts");
mkdirSync(SHOTS, { recursive: true });
mkdirSync(ART, { recursive: true });
const data = (p) => JSON.parse(readFileSync(join(here, "..", "public", "data", p), "utf-8").replace(/-?Infinity|NaN/g, "null"));

const results = [];
function check(name, ok, detail = "") {
  results.push({ name, ok: !!ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? `  (${detail})` : ""}`);
}
const fmt = (v) => (Number.isInteger(v) ? new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(v) : new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 }).format(v));

const index = data("index.json");
const cons = data("constants.json");
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

const browser = await chromium.launch();
const errors = [];
async function newPage(opts = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true, ...opts });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errors.push(`console: ${m.text()}`); });
  page.on("request", (r) => { if (r.url().includes("/api/nrt")) nrtRequests.push(r.url()); });
  return { ctx, page };
}
const nrtRequests = [];
const status = (page) => page.textContent("[data-testid=status]");
const waitComputed = (page, t = 90000) => page.waitForFunction(() => /Computed in your browser|too many|outside/.test(document.querySelector("[data-testid=status]")?.textContent ?? ""), null, { timeout: t });

try {
  const { page } = await newPage();
  await page.goto(`${BASE}/`);
  await page.waitForSelector("[data-testid=calendar] [data-ym]", { timeout: 30000 });
  check("scope line rendered from constants.json", (await page.textContent("[data-testid=scope]")) === cons.scope);

  // 1a. District search
  await page.fill("[data-testid=district-search]", "Lahore");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.querySelector("[data-testid=aoi-title]")?.textContent === "Lahore");
  const lahoreId = index.districts.find((d) => d.name === "Lahore").id;
  const lahore = data(`districts/${lahoreId}.json`);
  check("district search selects Lahore", true);

  // 3. Calendar: keyboard, tooltip, exact values from district JSON
  const first = page.locator('[data-testid=calendar] [tabindex="0"]');
  await first.focus();
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("ArrowDown");
  const focused = await page.evaluate(() => document.activeElement?.getAttribute("data-ym"));
  check("arrow keys move focus across the calendar grid", focused === "2004-02", `focused ${focused}`);
  const i = lahore.harmonized.value.length && 13; // 2004-02 is index 13 from 2003-01
  const want = `February 2004: ${fmt(lahore.harmonized.value[i])}`;
  const readout = await page.textContent("[data-testid=readout]");
  check("readout shows exact harmonized value from district JSON", readout.startsWith(want), readout);
  check("tooltip visible on keyboard focus", await page.isVisible("[data-testid=tooltip]"));
  await page.keyboard.press("End");
  check("End key jumps to December", (await page.evaluate(() => document.activeElement?.getAttribute("data-ym"))) === "2004-12");
  await page.keyboard.press("Control+End");
  const lastYm = await page.evaluate(() => document.activeElement?.getAttribute("data-ym"));
  check("Ctrl+End jumps to the last month", lastYm === index.period.last, lastYm);
  await page.locator('[data-ym="2015-11"]').hover();
  const tip = await page.textContent("[data-testid=tooltip]");
  check("hover tooltip shows exact value", tip.includes(fmt(lahore.harmonized.value[12 * 12 + 10])), tip);
  check("legend rendered with ticks", (await page.locator("[data-testid=legend] .ticks span").count()) === 3);
  const ariaAll = await page.locator("[data-testid=calendar] [role=gridcell][data-ym]").count();
  check("one grid cell per month of the record", ariaAll === lahore.period.n_months, `${ariaAll}`);

  // Reliability flags (D-039/D-040): marker + notes + banner, all from the district JSON.
  const lFlags = Object.keys(lahore.reliability.caution_years).sort();
  check("flag markers: one per caution year", (await page.locator("[data-testid=calendar] [data-flag-year]").count()) === lFlags.length, lFlags.join(","));
  check("flagged year row header is striped (pattern, not colour only)", (await page.locator(".cal .yr.flag").count()) === lFlags.length);
  const lastFlag = lFlags[lFlags.length - 1];
  const flagAria = await page.locator(`[data-ym="${lastFlag}-11"]`).getAttribute("aria-label");
  check("caution reason in the cell's accessible name (plain words)", flagAria.includes("Caution year:") && flagAria.includes("afternoon pass drifted later"), flagAria);
  check("banner shown when the range includes caution years", (await page.textContent("[data-testid=flag-banner]")).includes(lFlags.join(", ")));
  check("flag notes list each caution year", (await page.locator("[data-testid=flag-notes] li").count()) === lFlags.length);
  await page.fill("[data-testid=to]", `${Number(lFlags[0]) - 1}-12`);
  await page.waitForTimeout(200);
  check("no banner when the range has no caution years", (await page.locator("[data-testid=flag-banner]").count()) === 0);
  await page.fill("[data-testid=to]", index.period.last);

  // NRT fallback: no endpoint in this build -> snapshot, no request to /api/nrt.
  check("NRT falls back to the snapshot when no endpoint is set", (await page.textContent("[data-testid=month-card]")).includes("Near-real-time data is not part of this build") && (await page.locator("[data-testid=card-nrt]").count()) === 0 && !nrtRequests.length);

  // 4. Current month card (cached snapshot)
  const last = index.period.last;
  const [ly, lm] = last.split("-").map(Number);
  const cardText = await page.textContent("[data-testid=month-card]");
  check("card labelled latest available month, not live", cardText.includes("Latest available month, not live") && cardText.includes(`${MONTHS[lm - 1]} ${ly}`));
  const li = lahore.harmonized.value.length - 1;
  const cardH = await page.textContent("[data-testid=card-harmonized]");
  check("card harmonized value and median from JSON", cardH.includes(fmt(lahore.harmonized.value[li])) && cardH.includes(`median ${fmt(lahore.median.harmonized.values[lm - 1])}`), cardH);
  check("card shows all-years and excluding-flagged medians with plain labels, and says which the ratio uses", await (async () => { const t = await page.textContent("[data-testid=card-harmonized]"); const ex = lahore.median_excl_flagged; return t.includes("All years:") && t.includes("(the ratio uses this median)") && t.includes(ex.excluded_years.length ? "Excluding years we flag" : "none flagged") && t.includes(`median ${fmt(ex.values[lm - 1])}`); })(), "card-harmonized");
  check("card keeps 'not live' label and adds the launch note without claiming live", cardText.includes("Latest available month, not live") && (await page.textContent("[data-testid=card-live-note]")).includes("when the near-real-time service is switched on at launch"));
  const crit = lahore.critical, critText = await page.textContent("[data-testid=critical-panel]");
  check("critical panel: month level label, sentence and this-year line from JSON", critText.includes("Month level, not daily") && (crit.peak === null || critText.includes(["January","February","March","April","May","June","July","August","September","October","November","December"][crit.peak - 1])) && (crit.this_year === null || critText.includes("This year vs typical")), critText.slice(0, 120));
  check("critical table has 12 months and a text Critical column", (await page.locator("[data-testid=critical-table] tbody tr").count()) === 12 && (await page.textContent("[data-testid=critical-table]")).includes(crit.months.length ? "Yes" : "No"));
  await page.screenshot({ path: join(ART, "explorer-lahore.png"), fullPage: true });

  // 5. Raw vs harmonized toggle with era shading
  await page.click("[data-testid=toggle-raw]");
  const rawLabel = await page.textContent("[data-testid=series-label]");
  check("raw toggle switches series", rawLabel.startsWith("As recorded"), rawLabel.slice(0, 40));
  await page.locator('[data-ym="2011-11"]').hover();
  const rawTip = await page.textContent("[data-testid=tooltip]");
  check("raw 2011-11 shows Aqua count unscaled", rawTip.includes(`${fmt(lahore.raw.Aqua.n[8 * 12 + 10])} hotspots`), rawTip);
  await page.selectOption("[data-testid=raw-mode]", "NOAA20");
  await page.locator('[data-ym="2015-11"]').hover();
  check("single-platform raw view (NOAA-20 before launch = no data)", (await page.textContent("[data-testid=tooltip]")).includes("no data"));
  check("sensor-era shading present", (await page.locator(".era.modis").count()) === 1 && (await page.locator(".cell.seam").count()) === 12);
  await page.click("[data-testid=toggle-harmonized]");

  // 2. Date range
  await page.fill("[data-testid=from]", "2015-01");
  await page.waitForTimeout(200);
  const out2014 = await page.locator('[data-ym="2014-06"]').getAttribute("class");
  const in2016 = await page.locator('[data-ym="2016-06"]').getAttribute("class");
  check("date range fades months outside the period", out2014.includes("out") && !in2016.includes("out"));

  // 6. Exports: calendar CSV, PNGs
  let dl = page.waitForEvent("download");
  await page.click("[data-testid=csv-calendar]");
  let d = await dl;
  const calCsv = readFileSync(await d.path(), "utf-8");
  const calRows = calCsv.split("\n").filter((l) => /^\d{4}-\d{2},/.test(l));
  check("calendar CSV respects the date range", calRows[0]?.startsWith("2015-01") && calRows.length === (ly - 2015) * 12 + lm, `${calRows.length} rows`);
  check("calendar CSV carries critical months, both medians and a month-level label", calCsv.includes("# critical months (month level, not daily)") && calCsv.includes("median_all_years,median_excl_flagged_years,critical_month"));
  for (const which of ["calendar", "card"]) {
    dl = page.waitForEvent("download");
    await page.click(`[data-testid=png-${which}]`);
    d = await dl;
    const buf = readFileSync(await d.path());
    check(`PNG export of the ${which}`, buf.subarray(1, 4).toString() === "PNG" && buf.length > 5000, `${buf.length} bytes`);
    writeFileSync(join(ART, `export-${which}.png`), buf);
  }
  // Hotspot CSV (district, narrow range): under the cap
  await page.fill("[data-testid=from]", "2024-10");
  await page.fill("[data-testid=to]", "2024-11");
  dl = page.waitForEvent("download", { timeout: 60000 });
  await page.click("[data-testid=csv-hotspots]");
  d = await dl;
  const hs = readFileSync(await d.path(), "utf-8").split("\n").filter((l) => l && !l.startsWith("#"));
  check("hotspot CSV exported for district and range", hs[0]?.startsWith("lat,lon,acq_date") && hs.length > 1, `${hs.length - 1} rows`);
  const badDate = hs.slice(1).find((l) => { const dt = l.split(",")[2]; return dt < "2024-10-01" || dt > "2024-11-30"; });
  check("hotspot CSV rows inside the date range", !badDate, badDate ?? "");

  // CSV cap: Punjab (India), whole record
  await page.fill("[data-testid=district-search]", "Punjab (India)");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.querySelector("[data-testid=aoi-title]")?.textContent === "Punjab (India)");
  await page.fill("[data-testid=from]", index.period.first);
  await page.fill("[data-testid=to]", index.period.last);
  await page.click("[data-testid=csv-hotspots]");
  const capMsg = cons.csv_cap_message.replace("{cap}", cons.csv_row_cap.toLocaleString("en-GB"));
  await page.waitForFunction((m) => document.querySelector("[data-testid=export-status]")?.textContent === m, capMsg, { timeout: 120000 });
  check("CSV cap enforced with 'narrow your range' message", true, capMsg);

  // 1b. Box by typing
  await page.click("text=Box");
  await page.fill("[data-testid=box-w]", "74.4");
  await page.fill("[data-testid=box-e]", "75.2");
  await page.fill("[data-testid=box-s]", "30.9");
  await page.fill("[data-testid=box-n]", "31.6");
  await page.click("[data-testid=box-apply]");
  await waitComputed(page);
  check("box AOI computed client-side from tiles", (await status(page)).includes("Computed in your browser"), await status(page));
  {
    const inF = data("regions/in_punjab.json").reliability.caution_years, pkF = data("regions/pk_punjab.json").reliability.caution_years;
    const union = [...new Set([...Object.keys(inF), ...Object.keys(pkF)])].sort();
    const notes = await page.textContent("[data-testid=flag-notes]");
    check("custom box straddling the border takes the flags of both Punjabs", union.every((y) => notes.includes(y)) && notes.includes("Punjab (India)") && notes.includes("Punjab (Pakistan)"), union.join(","));
  }
  await page.fill("[data-testid=from]", index.period.first);
  dl = page.waitForEvent("download");
  await page.click("[data-testid=csv-calendar]");
  d = await dl;
  writeFileSync(join(ART, "box-calendar-harmonized.csv"), readFileSync(await d.path()));
  await page.click("[data-testid=toggle-raw]");
  await page.selectOption("[data-testid=raw-mode]", "Aqua");
  dl = page.waitForEvent("download");
  await page.click("[data-testid=csv-calendar]");
  d = await dl;
  writeFileSync(join(ART, "box-calendar-aqua.csv"), readFileSync(await d.path()));
  await page.click("[data-testid=toggle-harmonized]");
  writeFileSync(join(ART, "box.json"), JSON.stringify({ bbox: [74.4, 30.9, 75.2, 31.6] }));
  {
    // D-043: a drawn box is complete: critical block, both medians, CSV columns, keyboard, axe.
    const boxCsv = readFileSync(join(ART, "box-calendar-harmonized.csv"), "utf-8");
    const panel = await page.textContent("[data-testid=critical-panel]");
    check("drawn box shows the critical block (sentence, month-level label, drawn-area note)", panel.includes("Month level, not daily") && (await page.locator("[data-testid=critical-sentence]").count()) === 1 && panel.includes("computed in your browser") && !panel.includes("A drawn area has none"), panel.slice(0, 100));
    const cardBox = await page.textContent("[data-testid=card-harmonized]");
    check("drawn box month card shows both medians (all years, excluding years we flag)", cardBox.includes("All years:") && cardBox.includes("Excluding years we flag") && cardBox.includes("(the ratio uses this median)"), cardBox.slice(0, 160));
    check("drawn box calendar CSV has critical months, both medians and the union note", boxCsv.includes("# critical months (month level, not daily)") && boxCsv.includes("median_all_years,median_excl_flagged_years,critical_month") && boxCsv.includes("union of the calibration regions"));
    await page.locator("[data-testid=critical-panel] summary").focus();
    await page.keyboard.press("Enter");
    check("drawn box critical table opens from the keyboard and has 12 months", (await page.locator("[data-testid=critical-table] tbody tr").count()) === 12 && (await page.locator("[data-testid=critical-table]").isVisible()));
    const yesInTable = await page.locator("[data-testid=critical-table] tbody tr td:last-child", { hasText: "Yes" }).count();
    const yesInCsv = new Set(boxCsv.split("\n").filter((l) => /^\d{4}-\d{2},/.test(l)).map((l) => l.split(",")).filter((c) => c[c.length - 1] === "yes").map((c) => c[0].slice(5))).size;
    check("drawn box critical months in the table match the CSV column", yesInTable === yesInCsv && yesInTable > 0, `${yesInTable} vs ${yesInCsv}`);
    check("drawn box table region is keyboard-focusable", (await page.locator("[data-testid=critical-panel] [role=region]").getAttribute("tabindex")) === "0");
    const axeSrcBox = readFileSync(require.resolve("axe-core/axe.min.js", { paths: [join(here, "..")] }), "utf-8");
    await page.evaluate(axeSrcBox);
    const axBox = await page.evaluate(async () => { const r = await window.axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa", "best-practice"] }); return r.violations.map((v) => `${v.id}(${v.nodes.length}) ${v.nodes[0].target.join(" ")}`); });
    check("drawn box explorer: axe 0 violations", axBox.length === 0, axBox.join("; "));
  }

  // 1c. Box drawn on the map
  await page.click("[data-testid=box-draw]");
  const mb = await page.locator("[data-testid=map]").boundingBox();
  await page.mouse.move(mb.x + mb.width * 0.4, mb.y + mb.height * 0.4);
  await page.mouse.down();
  await page.mouse.move(mb.x + mb.width * 0.5, mb.y + mb.height * 0.5, { steps: 5 });
  await page.mouse.move(mb.x + mb.width * 0.6, mb.y + mb.height * 0.6, { steps: 5 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector("[data-testid=aoi-title]")?.textContent?.startsWith("Box"));
  await waitComputed(page);
  const drawnTitle = await page.textContent("[data-testid=aoi-title]");
  check("box drawn on the map becomes the AOI", drawnTitle.startsWith("Box") && !drawnTitle.includes("74.4, 30.9"), drawnTitle);

  // 1d. Point + radius (DuckDB haversine filter)
  await page.click("text=Point + radius");
  await page.fill("[data-testid=pt-lat]", "30.9");
  await page.fill("[data-testid=pt-lon]", "75.85");
  await page.fill("[data-testid=pt-km]", "25");
  await page.click("[data-testid=pt-apply]");
  await page.waitForFunction(() => document.querySelector("[data-testid=aoi-title]")?.textContent?.includes("km around"));
  await waitComputed(page);
  check("point + radius AOI computed from tiles", (await status(page)).includes("Computed in your browser"), await status(page));
  await page.fill("[data-testid=from]", "2024-11");
  await page.fill("[data-testid=to]", "2024-11");
  dl = page.waitForEvent("download", { timeout: 60000 });
  await page.click("[data-testid=csv-hotspots]");
  d = await dl;
  const rr = readFileSync(await d.path(), "utf-8").split("\n").filter((l) => l && !l.startsWith("#")).slice(1);
  const R = 6371.0088, rad = Math.PI / 180;
  const far = rr.map((l) => l.split(",").map(Number)).find(([la, lo]) => 2 * R * Math.asin(Math.sqrt(Math.sin(((la - 30.9) * rad) / 2) ** 2 + Math.cos(30.9 * rad) * Math.cos(la * rad) * Math.sin(((lo - 75.85) * rad) / 2) ** 2)) > 25.001);
  check("radius CSV rows all within the radius", rr.length > 0 && !far, `${rr.length} rows`);

  // Theme toggle button
  await page.click(".theme-btn");
  check("theme toggle sets data-theme", ["dark", "light"].includes(await page.evaluate(() => document.documentElement.dataset.theme)));

  // D-042 flagship rule, recomputed here from the district JSON (not from the page code)
  const flagshipOf = (dd) => {
    const caution = new Set(Object.keys(dd.reliability.caution_years).map(Number));
    const [y0, m0] = dd.period.first.split("-").map(Number);
    let best = null;
    dd.harmonized.value.forEach((v, k) => {
      const t = y0 * 12 + m0 - 1 + k, y = Math.floor(t / 12);
      if (t % 12 !== 10 || y < 2012 || caution.has(y) || dd.harmonized.partial[k] !== false || v === null) return;
      if (!best || v >= best.v) best = { v, y, k, ym: `${y}-11` };
    });
    return best;
  };
  const UC = [["Sangrur", "sangrur", false], ["Kasur", "kasur", false], ["Sangrur", "sangrur-flagged", true], ["Kasur", "kasur-flagged", true]];
  const ucMonth = (nm, flagged) => (flagged ? { ym: "2025-11", k: (2025 - 2003) * 12 + 10 } : (({ ym, k }) => ({ ym, k }))(flagshipOf(data(`districts/${index.districts.find((x) => x.name === nm).id}.json`))));
  // Use-case screenshots (served from public/usecase, also copied into out/)
  {
    const { ctx, page: p } = await newPage({ viewport: { width: 1200, height: 800 }, colorScheme: "light" });
    for (const [nm, slug, flagged] of UC) {
      const id = index.districts.find((x) => x.name === nm).id;
      const um = ucMonth(nm, flagged);
      await p.goto(`${BASE}/?area=${id}&from=2003-01&to=2025-11`);
      await p.waitForFunction((n) => document.querySelector("[data-testid=aoi-title]")?.textContent === n, nm);
      await p.waitForSelector("[data-testid=calendar] [data-ym]");
      await p.waitForTimeout(1200);
      const outs = [join(here, "..", "public", "usecase"), join(here, "..", "out", "usecase")];
      outs.forEach((o) => mkdirSync(o, { recursive: true }));
      const shoot = async (loc, step) => { const buf = await loc.screenshot(); outs.forEach((o) => writeFileSync(join(o, `${slug}-${step}.png`), buf)); writeFileSync(join(SHOTS, `usecase-${slug}-${step}.png`), buf); };
      await shoot(p.locator("main"), 1);
      await p.locator(`[data-ym="${um.ym}"]`).focus();
      await shoot(p.locator(".plate"), 2);
      await shoot(p.locator("[data-testid=flag-notes]"), 3);
      const ro = await p.textContent("[data-testid=readout]");
      check(`use-case deep link opens ${nm} (${slug}) with ${um.ym} readout`, ro.startsWith(`November ${um.ym.slice(0, 4)}`), ro.slice(0, 60));
    }
    await ctx.close();
  }

  // 7. Pages
  const t2 = data("results/t2.json");
  await page.goto(`${BASE}/results/`);
  const res = await page.textContent("main");
  const labels = [...Object.values(t2.t1_reevaluated).map((v) => v.label), ...Object.values(t2.verdict_t2_revised).map((v) => v.label)];
  check("results page shows every verdict label from JSON", labels.every((l) => res.includes(l)), labels.join(" | "));
  check("results page includes inconclusive and fail labels", res.includes("inconclusive") && /fail/.test(res));
  const t1 = data("results/t1.json");
  const pk = Math.round(t1.results.hotspots.PK_Punjab.step_2012.raw_step * 100);
  check("finding sentence uses t1.json raw_step", (await page.textContent("[data-testid=finding]")).includes(`+${pk}%`), `+${pk}%`);
  const t3 = data("results/t3.json");
  const t3rows = await page.locator("[data-testid=t3-table] tbody tr").count();
  check("T3 evidence table: 3 explanations per region", t3rows === t3.regions.length * 3, `${t3rows}`);
  const verdicts = t3.regions.flatMap((r) => ["O", "T", "D"].map((k) => t3.t3[r].evidence[k].verdict));
  const t3text = await page.textContent("[data-testid=t3-table]");
  check("T3 verdicts from t3.json", verdicts.every((v) => t3text.includes(v)), verdicts.join("|"));
  check("T3 charts: day/night per Punjab + NOAA-20/S-NPP ratio", (await page.locator("[data-testid=chart-daynight]").count()) === 2 && (await page.locator("[data-testid=chart-n20ratio]").count()) === 1);
  const r0 = t3.regions[0], y0 = Object.keys(t3.t3[r0].a1_noaa20_snpp.by_year).sort()[0];
  check("T3 ratio table value from JSON", (await page.textContent("[data-testid=t3-ratio-table]")).includes(t3.t3[r0].a1_noaa20_snpp.by_year[y0].ratio.toFixed(3)));
  check("two T2 charts (overpass and ratio) rendered", (await page.locator("[data-testid^=chart-overpass]").count()) >= 1 && (await page.locator("[data-testid^=chart-ratio]").count()) >= 1);
  // Use-case page: values rendered from the district JSON
  await page.goto(`${BASE}/use-case/`);
  for (const [nm, slug, flagged] of UC) {
    const dd = data(`districts/${index.districts.find((x) => x.name === nm).id}.json`);
    const um = ucMonth(nm, flagged), k = um.k, yr = um.ym.slice(0, 4);
    const v = await page.textContent(`[data-testid=uc-value-${slug}]`), med = await page.textContent(`[data-testid=uc-median-${slug}]`), n20 = await page.textContent(`[data-testid=uc-n20-${slug}]`);
    check(`use case ${slug}: ${um.ym} value, median, NOAA-20 from JSON`, v === fmt(dd.harmonized.value[k]) && med === fmt(dd.median.harmonized.values[10]) && n20 === fmt(dd.raw.NOAA20.n[k]), `${v} ${med} ${n20}`);
    check(`use case ${slug}: median excluding flagged years from JSON`, (await page.textContent(`[data-testid=uc-median-excl-${slug}]`)) === fmt(dd.median_excl_flagged.values[10]));
    const flagTxt = await page.textContent(`[data-testid=uc-flag-${slug}]`);
    const isFlagged = !!dd.reliability.caution_years[yr];
    check(`use case ${slug}: ${yr} flag matches JSON, and headline examples are unflagged, contrast examples flagged`, isFlagged === flagged && (isFlagged ? flagTxt.includes("caution") : flagTxt.includes("no reliability flag")), `${yr} flagged=${isFlagged}`);
    const cap = await page.textContent(`[data-testid=uc-caption-${slug}]`);
    check(`use case ${slug}: caption says ${flagged ? "contrast" : "headline"}`, cap.includes(flagged ? "Contrast example" : "Headline example"));
  }
  check("use case page has screenshots for each step", (await page.locator("img.shot").count()) === 12);
  await page.goto(`${BASE}/methods/`);
  check("methods page has month-level line and limitations", (await page.textContent("main")).includes("month level") && (await page.textContent("main")).includes("Limitations"));
  const factorNote = await page.textContent("[data-testid=factor-note]");
  const af = Object.values(JSON.parse(readFileSync(join(here, "../public/data/results/calibration.json"), "utf8")).factors["Aqua->SNPP"]).flatMap((r) => r.factor).filter((x) => x !== null);
  check("methods explains the size of the Aqua to S-NPP factors with the pipeline's range", factorNote.includes(Math.min(...af).toFixed(1)) && factorNote.includes(Math.max(...af).toFixed(1)) && factorNote.includes("Schroeder"), factorNote.slice(0, 120));
  await page.goto(`${BASE}/about/`);
  check("about page has AI-use statement", (await page.textContent("[data-testid=ai-statement]")).includes("Claude Code"));
  await page.goto(`${BASE}/attribution/`);
  const att = await page.textContent("[data-testid=attribution]");
  check("attribution renders ODbL and FIRMS citation", att.includes("ODbL") && att.includes("LANCE FIRMS"));

  // Interface pass (D-044): press feedback on pointer-down, reduced motion, phone targets, answer-first card
  {
    const press = async (page, sel) => {
      await page.locator(sel).first().scrollIntoViewIfNeeded();
      const box = await page.locator(sel).first().boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.waitForTimeout(160);
      const t = await page.locator(sel).first().evaluate((el) => getComputedStyle(el).transform);
      await page.mouse.up();
      return t;
    };
    const { ctx: c1, page: p1 } = await newPage();
    await p1.goto(`${BASE}/`);
    await p1.waitForSelector("[data-testid=calendar] [data-ym]");
    check("eyebrow asks the question before the month card", (await p1.textContent("[data-testid=eyebrow]")) === "Is this month unusual here?" && await p1.evaluate(() => { const e = document.querySelector("[data-testid=eyebrow]"), c = document.querySelector("[data-testid=month-card]"); return !!(e && c && e.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING); }));
    check("month card keeps 'not live' tag and caution/scope text at body size or larger", await p1.evaluate(() => parseFloat(getComputedStyle(document.querySelector("[data-testid=snapshot-label]")).fontSize) >= 13 && parseFloat(getComputedStyle(document.querySelector(".card .foot")).fontSize) >= 13));
    const tBtn = await press(p1, ".seg button:not([aria-pressed=true])");
    check("pressed state shows on pointer-down, before release (button scales)", tBtn !== "none", tBtn);
    const tCell = await press(p1, "[data-testid=calendar] [data-ym='2015-11']");
    check("pressed state shows on pointer-down (calendar cell scales)", tCell !== "none", tCell);
    await p1.locator("[data-testid=calendar] [data-ym='2016-03']").click();
    check("tapping a calendar cell sets the readout", (await p1.textContent("[data-testid=readout]")).startsWith("March 2016"));
    check("no empty state while an area is loaded", (await p1.locator("[data-testid=empty-state]").count()) === 0);
    await p1.getByRole("button", { name: "District" }).click();
    await p1.fill("[data-testid=district-search]", "zzzzqq");
    check("district search with no match shows an empty state with a clear action", (await p1.textContent(".empty-mini")).includes("Clear search"));
    await p1.getByRole("button", { name: "Clear search" }).click();
    check("Clear search restores the list", (await p1.inputValue("[data-testid=district-search]")) === "");
    await c1.close();

    const { ctx: c2, page: p2 } = await newPage({ reducedMotion: "reduce" });
    await p2.goto(`${BASE}/`);
    await p2.waitForSelector("[data-testid=calendar] [data-ym]");
    check("prefers-reduced-motion: media emulated", await p2.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches));
    const rb = await press(p2, ".seg button:not([aria-pressed=true])");
    const rc = await press(p2, "[data-testid=calendar] [data-ym='2015-11']");
    check("reduced motion: pressing a button or cell applies no transform", rb === "none" && rc === "none", `${rb} | ${rc}`);
    const anim = await p2.evaluate(() => { const els = [...document.querySelectorAll(".btn, .seg button, .cell, .tip, .card")]; return els.filter((e) => getComputedStyle(e).animationName !== "none" || /transform/.test(getComputedStyle(e).transitionProperty)).length; });
    check("reduced motion: no transform transitions or animations on controls and cells", anim === 0, `${anim} elements`);
    await c2.close();

    const { ctx: c3, page: p3 } = await newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
    await p3.goto(`${BASE}/`);
    await p3.waitForSelector("[data-testid=calendar] [data-ym]");
    const small = [];
    const audit = async (label) => {
      const bad = await p3.evaluate(() => {
        const sel = ".btn, .seg button, .theme-btn, .nav a, input:not([type=checkbox]), select, .maplibregl-ctrl button, .key:has(input), .results-list li, .wordmark";
        return [...document.querySelectorAll(sel)].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== "hidden" && r.height < 43.5; }).map((e) => `${e.className || e.tagName}:${Math.round(e.getBoundingClientRect().height)}`);
      });
      small.push(...bad.map((b) => `${label} ${b}`));
    };
    check("phone: picker is collapsed and out of the accessibility tree at load", (await p3.locator("#picker").isHidden()) && (await p3.getAttribute("[data-testid=picker-toggle]", "aria-expanded")) === "false");
    {
      const atf = await p3.evaluate(() => { const r = (t) => document.querySelector(`[data-testid=${t}]`).getBoundingClientRect(); return { fig: r("card-harmonized").bottom, eyebrow: r("eyebrow").top, h: window.innerHeight }; });
      check("phone 390x844: the answer (eyebrow, headline figure and its median comparison) is above the fold with the picker collapsed", atf.fig <= atf.h && atf.eyebrow >= 0, `figure bottom ${Math.round(atf.fig)} of ${atf.h}`);
      const order = await p3.evaluate(() => { const q = (s) => document.querySelector(s); const f = (a, b) => !!(q(a).compareDocumentPosition(q(b)) & Node.DOCUMENT_POSITION_FOLLOWING); return f(".aoi-head", "[data-testid=picker-toggle]") && f("[data-testid=picker-toggle]", "[data-testid=month-card]") && f("[data-testid=month-card]", "[data-testid=calendar]"); });
      check("phone: DOM order is area bar, picker toggle, answer, calendar (no CSS order)", order);
      check("phone: caution/scope/not-live text still visible", (await p3.isVisible("[data-testid=scope]")) && (await p3.isVisible("[data-testid=snapshot-label]")));
    }
    await p3.locator("[data-testid=picker-toggle]").click();
    await audit("district");
    await p3.getByRole("button", { name: "Box" }).click();
    await audit("box");
    await p3.getByRole("button", { name: "Point + radius" }).click();
    await audit("radius");
    check("phone: touch targets are at least 44 px high (controls, nav, buttons, map zoom)", small.length === 0, small.slice(0, 5).join(", "));
    const sticky = await p3.evaluate(() => getComputedStyle(document.querySelector(".aoi-head")).position);
    check("phone: area name bar is sticky", sticky === "sticky", sticky);
    await p3.locator("[data-testid=calendar]").scrollIntoViewIfNeeded();
    const headTop = await p3.evaluate(() => Math.round(document.querySelector(".aoi-head").getBoundingClientRect().top));
    check("phone: area name stays at the top while the calendar is in view", headTop === 0, `${headTop}`);
    check("phone: no horizontal scroll with new layout", (await p3.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)) <= 0);
    await c3.close();
  }


  // D-046: phone picker toggle and touch drawing (touch-enabled context, CDP touch events)
  {
    const { ctx, page: p } = await newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
    await p.goto(`${BASE}/`);
    await p.waitForSelector("[data-testid=calendar] [data-ym]");
    const toggle = p.locator("[data-testid=picker-toggle]");
    const expanded = () => toggle.getAttribute("aria-expanded");
    const inPicker = () => p.evaluate(() => !!document.activeElement?.closest("#picker"));
    check("touch: 'Change area' is a labelled button with aria-controls", (await toggle.textContent()) === "Change area" && (await toggle.getAttribute("aria-controls")) === "picker" && (await expanded()) === "false");
    await toggle.tap();
    check("touch: tapping Change area opens the picker and moves focus into it", (await expanded()) === "true" && (await p.locator("#picker").isVisible()) && (await inPicker()));
    await p.keyboard.press("Escape");
    check("Escape closes the picker, hides it and returns focus to the toggle", (await expanded()) === "false" && (await p.locator("#picker").isHidden()) && (await p.evaluate(() => document.activeElement?.getAttribute("data-testid"))) === "picker-toggle");
    await toggle.tap();
    await toggle.tap();
    check("touch: tapping Change area again closes it", (await expanded()) === "false");
    await p.locator("[data-ym='2016-03']").tap();
    check("touch: tapping a calendar cell sets the readout", (await p.textContent("[data-testid=readout]")).startsWith("March 2016"));
    await p.evaluate(() => window.scrollTo(0, 0));
    await toggle.tap();
    await p.getByRole("button", { name: "Box" }).tap();
    await p.locator("[data-testid=box-draw]").tap();
    const canvas = p.locator("[data-testid=map] .maplibregl-canvas");
    check("touch-action is none on the canvas while drawing", (await canvas.evaluate((c) => getComputedStyle(c).touchAction)) === "none");
    await p.waitForTimeout(400);
    await canvas.scrollIntoViewIfNeeded();
    const cb = await canvas.boundingBox();
    const cdp = await ctx.newCDPSession(p);
    const touch = (type, pts) => cdp.send("Input.dispatchTouchEvent", { type, touchPoints: pts.map(([x, y], id) => ({ x, y, id })) });
    const before = await Promise.all(["w", "s", "e", "n"].map((k) => p.inputValue(`[data-testid=box-${k}]`)));
    // two-finger pinch while drawing is ignored
    await touch("touchStart", [[cb.x + 40, cb.y + 60], [cb.x + 120, cb.y + 100]]);
    await touch("touchMove", [[cb.x + 60, cb.y + 60], [cb.x + 140, cb.y + 130]]);
    await touch("touchEnd", []);
    await p.waitForTimeout(300);
    const afterPinch = await Promise.all(["w", "s", "e", "n"].map((k) => p.inputValue(`[data-testid=box-${k}]`)));
    check("two-finger pinch while drawing draws nothing", JSON.stringify(before) === JSON.stringify(afterPinch) && (await expanded()) === "true");
    // cancelled gesture draws nothing
    await touch("touchStart", [[cb.x + 40, cb.y + 60]]);
    await touch("touchMove", [[cb.x + 100, cb.y + 110]]);
    await touch("touchCancel", []);
    await p.waitForTimeout(300);
    check("pointercancel discards the draft", (await Promise.all(["w", "s", "e", "n"].map((k) => p.inputValue(`[data-testid=box-${k}]`)))).join() === before.join() && (await expanded()) === "true");
    // View state before the drag (drawing the box re-fits the map to it afterwards)
    const view = await p.locator("[data-testid=map]").evaluate((m) => ({ lng: +m.dataset.lng, lat: +m.dataset.lat, zoom: +m.dataset.zoom }));
    // the real drag: six moves, finger starts 30% / 30% and ends 70% / 75% of the canvas
    const x0 = cb.x + cb.width * 0.3, y0 = cb.y + cb.height * 0.3, x1 = cb.x + cb.width * 0.7, y1 = cb.y + cb.height * 0.75;
    await touch("touchStart", [[x0, y0]]);
    for (let k = 1; k <= 6; k++) await touch("touchMove", [[x0 + ((x1 - x0) * k) / 6, y0 + ((y1 - y0) * k) / 6]]);
    await touch("touchEnd", []);
    await p.waitForFunction(() => document.querySelector("[data-testid=aoi-title]")?.textContent?.startsWith("Box"), null, { timeout: 15000 });
    await waitComputed(p);
    // Expected corners from the map's own view state (centre, zoom, 512 px world) with Web Mercator
    const W = 512 * 2 ** view.zoom, rad = Math.PI / 180;
    const mercY = (lat) => (0.5 - Math.log(Math.tan(Math.PI / 4 + (lat * rad) / 2)) / (2 * Math.PI)) * W;
    const unY = (y) => (2 * Math.atan(Math.exp((0.5 - y / W) * 2 * Math.PI)) - Math.PI / 2) / rad;
    const at = (px, py) => [view.lng + ((px - cb.x - cb.width / 2) / W) * 360, unY(mercY(view.lat) + (py - cb.y - cb.height / 2))];
    const [ax, ay] = at(x0, y0), [bx, by] = at(x1, y1);
    const want = { w: Math.min(ax, bx), e: Math.max(ax, bx), s: Math.min(ay, by), n: Math.max(ay, by) };
    const got = Object.fromEntries(await Promise.all(["w", "s", "e", "n"].map(async (k) => [k, Number(await p.inputValue(`[data-testid=box-${k}]`))])));
    const TOL = 0.01; // degrees: under 2 screen pixels at this zoom (0.0055 deg per pixel); covers the 0.001 rounding
    const maxErr = Math.max(...["w", "s", "e", "n"].map((k) => Math.abs(got[k] - want[k])));
    check(`touch drag draws the box under the finger (corners within ${TOL} deg, under 2 px, of the drag)`, maxErr <= TOL, `max error ${maxErr.toFixed(4)} deg; got ${JSON.stringify(got)}`);
    check("touch drag: box title and calendar update from the drawn box", (await p.textContent("[data-testid=aoi-title]")).startsWith("Box") && (await p.locator("[data-testid=calendar] [data-ym]").count()) > 100 && (await status(p)).includes("Computed in your browser"));
    check("touch drag: picker closes and focus returns to the toggle", (await expanded()) === "false" && (await p.evaluate(() => document.activeElement?.getAttribute("data-testid"))) === "picker-toggle");
    check("touch-action is not none once drawing ends (panning and page scroll work again)", (await canvas.evaluate((c) => getComputedStyle(c).touchAction)) !== "none");
    await ctx.close();
  }

  // Screenshots: page x viewport x theme
  const pages = { explorer: "/", "use-case": "/use-case/", results: "/results/", methods: "/methods/", about: "/about/", attribution: "/attribution/" };
  const axeSrc = readFileSync(require.resolve("axe-core/axe.min.js", { paths: [join(here, "..")] }), "utf-8");
  const axeRuns = [];
  const vps = { desktop: { width: 1440, height: 900 }, phone: { width: 390, height: 844 } };
  for (const theme of ["light", "dark"]) {
    for (const [vpName, vp] of Object.entries(vps)) {
      const { ctx, page: p } = await newPage({ viewport: vp, colorScheme: theme, deviceScaleFactor: vpName === "phone" ? 2 : 1 });
      for (const [name, path] of Object.entries(pages)) {
        await p.goto(`${BASE}${path}`);
        if (name === "explorer") { await p.waitForSelector("[data-testid=calendar] [data-ym]"); await p.waitForTimeout(1200); }
        if (name === "use-case") await p.evaluate(() => document.querySelectorAll("img.shot").forEach((i) => { i.loading = "eager"; }));
        const bodyText = await p.textContent("body");
        check(`${name} ${vpName} ${theme}: no "Coverage: Coverage" and transfer wording`, !bodyText.includes("Coverage: Coverage") && bodyText.includes(cons.scope));
        await p.evaluate(axeSrc); // evaluate, not addScriptTag: an injected inline tag is (rightly) blocked by the page CSP
        const ax = await p.evaluate(async () => { const r = await window.axe.run(document, { runOnly: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa", "best-practice"] }); return r.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, targets: v.nodes.slice(0, 3).map((n) => n.target.join(" ")) })); });
        axeRuns.push({ page: name, viewport: vpName, theme, violations: ax });
        check(`${name} ${vpName} ${theme}: axe 0 violations`, ax.length === 0, ax.map((v) => `${v.id}(${v.nodes}) ${v.targets[0]}`).join("; "));
        const overflow = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        check(`${name} ${vpName} ${theme}: no horizontal scroll`, overflow <= 0, `${overflow}px`);
        if (name === "explorer" && vpName === "phone") {
          await p.evaluate(() => window.scrollTo(0, 0));
          await p.screenshot({ path: join(SHOTS, `explorer-phone-folded-${theme}.png`) });
          await p.locator("[data-testid=picker-toggle]").click();
          await p.waitForTimeout(500);
          await p.screenshot({ path: join(SHOTS, `explorer-phone-picker-open-${theme}.png`) });
          await p.locator("[data-testid=picker-toggle]").click();
        }
        await p.screenshot({ path: join(SHOTS, `${name}-${vpName}-${theme}.png`), fullPage: true });
      }
      await ctx.close();
    }
  }
  writeFileSync(join(repo, "docs", "review", "axe-after.json"), JSON.stringify({ axe: "4.10.2", generated_by: "web/e2e/run.mjs", runs: axeRuns }, null, 1));
} catch (e) {
  check("e2e run completed without exceptions", false, e.message);
}
const benign = errors.filter((e) => !/GL Driver|WebGL/.test(e));
check("no page or console errors", benign.length === 0, benign.slice(0, 3).join(" | "));
await browser.close();
const failed = results.filter((r) => !r.ok);
writeFileSync(join(ART, "e2e-results.json"), JSON.stringify({ passed: results.length - failed.length, failed: failed.length, results }, null, 1));
console.log(`\n${results.length - failed.length}/${results.length} checks passed`);
process.exit(failed.length ? 1 : 0);
