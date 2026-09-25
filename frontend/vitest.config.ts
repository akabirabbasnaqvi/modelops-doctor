import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/test/**",
        "src/main.tsx",
        "src/vite-env.d.ts",
        // Type-only modules compile to nothing, so they have no runtime
        // behaviour to cover and only add noise to the report.
        "src/types/**",
      ],
      // Mirrors the backend's --cov-fail-under=70 so neither side can
      // silently regress. vitest exits non-zero when these are not met.
      thresholds: {
        lines: 70,
        statements: 70,
        branches: 70,
        functions: 70,
      },
    },
  },
});
