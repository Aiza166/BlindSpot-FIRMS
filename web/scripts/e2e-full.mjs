// Cross-platform (Windows, Mac, Linux) replacement for the POSIX "serve & run & kill" shell lines.
// Starts scripts/serve.mjs with the production headers, waits for it, runs e2e/run.mjs, then stops it.
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
const here = new URL(".", import.meta.url);
const PORT = process.env.PORT ?? "4173";
const BASE = `http://localhost:${PORT}`;

const server = spawn(process.execPath, [fileURLToPath(new URL("serve.mjs", here)), "--headers"], {
  env: { ...process.env, PORT },
  stdio: "inherit",
});

async function waitForServer(timeoutMs = 15000) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    try {
      const r = await fetch(`${BASE}/`);
      if (r.ok) return true;
    } catch {
      /* not up yet */
    }
    await new Promise((res) => setTimeout(res, 300));
  }
  return false;
}

let code = 1;
try {
  if (!(await waitForServer())) throw new Error(`server did not start on ${BASE}`);
  const run = spawn(process.execPath, [fileURLToPath(new URL("../e2e/run.mjs", here))], {
    env: { ...process.env, BASE },
    stdio: "inherit",
  });
  code = await new Promise((res) => run.on("exit", (c) => res(c ?? 1)));
} catch (err) {
  console.error(err.message);
} finally {
  server.kill();
}
process.exit(code);
