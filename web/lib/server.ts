// Build-time reads of public/data for statically rendered pages (server components only).
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(process.cwd(), "public", "data");

export function readData<T>(rel: string): T {
  // Python's json writes Infinity/NaN (e.g. open-ended bins in t2.json); JSON.parse rejects them.
  const text = readFileSync(join(ROOT, rel), "utf-8").replace(/([:\[,]\s*)(-?Infinity|NaN)(?=\s*[,\]}])/g, "$1null");
  return JSON.parse(text) as T;
}

export function readText(rel: string): string {
  return readFileSync(join(ROOT, rel), "utf-8");
}
