import { test, expect } from "@playwright/test";

test.describe("Tokens/Button", () => {
  test("primary button visual baseline", async ({ page }) => {
    await page.goto("http://127.0.0.1:6006/iframe.html?id=tokens-button--primary");
    await page.setViewportSize({ width: 400, height: 200 });
    const button = page.locator("button.aeg-button").first();
    await expect(button).toHaveScreenshot("button-primary.png");
  });
});
