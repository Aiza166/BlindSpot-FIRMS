import { defineConfig } from "vitest/config";

export default defineConfig({ test: { include: ["functions/**/*.test.ts", "lib/**/*.test.ts"], environment: "node" } });
