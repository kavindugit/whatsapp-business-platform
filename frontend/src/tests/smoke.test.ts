import { test, expect } from "vitest";

/**
 * Smoke test: confirms the test environment is wired correctly.
 * Real feature tests are added in Day 5+.
 */
test("test environment is configured", () => {
  expect(1 + 1).toBe(2);
});
