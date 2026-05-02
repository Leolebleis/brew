import { test, expect } from "@playwright/test";

test("theme toggle persists across reload", async ({ page }) => {
  await page.goto("/");
  const toggle = page.getByRole("button", { name: /theme/i });
  await toggle.click(); // → light
  await toggle.click(); // → dark
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});
