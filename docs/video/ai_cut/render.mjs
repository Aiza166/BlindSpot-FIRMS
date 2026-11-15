import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { pathToFileURL } from "node:url";
const mode = process.argv[2] || "check";
const b = await chromium.launch();
const p = await (await b.newContext({ viewport: { width: 1920, height: 1080 } })).newPage();
await p.goto(pathToFileURL("comp.html").href);
await p.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map((i) => i.decode())); });
if (mode === "check") {
  mkdirSync("check", { recursive: true });
  for (const t of [0.5, 3, 4.8, 5.4, 8.5, 9.85, 12, 18.5, 22, 25.5, 28.5]) { await p.evaluate((x) => window.seek(x), t); await p.screenshot({ path: `check/t${String(t).padStart(5, "0")}.jpg`, type: "jpeg", quality: 80 }); }
} else {
  mkdirSync("frames", { recursive: true });
  const N = 899;
  for (let i = 0; i < N; i++) { await p.evaluate((x) => window.seek(x), i / 30); await p.screenshot({ path: `frames/f${String(i).padStart(4, "0")}.jpg`, type: "jpeg", quality: 95 }); }
  console.log("frames", N);
}
await b.close();
