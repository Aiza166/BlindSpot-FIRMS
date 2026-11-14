// Cloudflare Pages Function: GET /api/nrt?bbox=w,s,e,n[&month=YYYY-MM][&area=<id>] (D-040).
// The static export in out/ stays static; this file is deployed only by Cloudflare Pages.
// FIRMS_MAP_KEY is a Pages secret (server env). It is never logged or returned.
import { AssetMissing, CACHE_SECONDS, computeNrt, NrtError, redact, TokenBucket, type DetCache } from "../_lib/nrt-core";

interface Env {
  FIRMS_MAP_KEY?: string;
  /** Extra origin allowed to call cross-origin (e.g. "https://example.org"); default: same origin only. */
  ALLOWED_ORIGIN?: string;
  ASSETS: { fetch: (req: Request | string) => Promise<Response> };
}

interface Ctx { request: Request; env: Env }

// Per-IP token bucket (per isolate): burst 20, then one request every 6 s. Repeated areas are
// served from the cache and do not reach FIRMS; a Cloudflare rate-limiting rule can sit in front.
export const limiter = new TokenBucket(20, 1 / 6);

function json(body: unknown, status: number, extra: Record<string, string>): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", vary: "Origin", ...extra } });
}

export async function onRequestGet({ request, env }: Ctx): Promise<Response> {
  const url = new URL(request.url);
  const origin = request.headers.get("origin");
  const allowed = new Set([url.origin, ...(env.ALLOWED_ORIGIN ? [env.ALLOWED_ORIGIN] : [])]);
  const cors: Record<string, string> = origin && allowed.has(origin) ? { "access-control-allow-origin": origin } : {};
  const fail = (status: number, code: string, reason: string, extra: Record<string, string> = {}) =>
    json({ status: "unavailable", code, reason }, status, { ...cors, "cache-control": "no-store", ...extra });

  if (origin && !allowed.has(origin)) return fail(403, "forbidden_origin", "cross-origin requests are not allowed");
  const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
  if (!limiter.take(ip, Date.now())) return fail(429, "rate_limited", "too many requests; try again in a minute", { "retry-after": "60" });

  const edge = (globalThis as { caches?: { default?: Cache } }).caches?.default;
  const cacheUrl = (k: string) => `https://nrt-cache.invalid/${encodeURIComponent(k)}`;
  try {
    const body = await computeNrt(url.searchParams, {
      key: env.FIRMS_MAP_KEY,
      fetchFirms: (u, signal) => fetch(u, { signal }),
      readAsset: async (p) => {
        const r = await env.ASSETS.fetch(new URL(`/${p}`, url.origin).toString());
        // Pages can answer an unknown path with a 200 HTML fallback; only JSON counts (MEDIUM-4).
        if (!r.ok || !/json/i.test(r.headers.get("content-type") ?? "")) throw new AssetMissing(p);
        return r.json();
      },
      cache: edge && {
        get: async (k) => { const r = await edge.match(cacheUrl(k)); return r ? ((await r.json()) as DetCache) : undefined; },
        put: async (k, v) => { await edge.put(cacheUrl(k), new Response(JSON.stringify(v), { headers: { "content-type": "application/json", "cache-control": `max-age=${CACHE_SECONDS}` } })); },
      },
    });
    return json(body, 200, { ...cors, "cache-control": `public, max-age=600, s-maxage=${CACHE_SECONDS}` });
  } catch (e) {
    if (e instanceof NrtError) {
      if (e.status >= 500) console.error(`nrt ${e.code}: ${redact(e.message, env.FIRMS_MAP_KEY)}`);
      return fail(e.status, e.code, e.message);
    }
    console.error(`nrt internal: ${redact(e instanceof Error ? `${e.name}: ${e.message}` : String(e), env.FIRMS_MAP_KEY)}`);
    return fail(500, "internal", "internal error");
  }
}
