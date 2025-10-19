import { test, expect } from "@playwright/test";

const storyUrl = "http://127.0.0.1:6006/iframe.html";

test.describe("Dashboard · Mining & Merchant", () => {
  test("채굴 대시보드 모바일 뷰", async ({ page }) => {
    await page.setViewportSize({ width: 430, height: 920 });
    await page.goto(`${storyUrl}?id=dashboard-mining-overview--default&viewMode=story`);
    const dashboard = page.locator("section[aria-label='채굴 현황 대시보드']");
    await expect(dashboard).toHaveScreenshot("mining-dashboard-mobile.png");
  });

  test("채굴 대시보드 태블릿 뷰", async ({ page }) => {
    await page.setViewportSize({ width: 834, height: 1024 });
    await page.goto(`${storyUrl}?id=dashboard-mining-overview--default&viewMode=story`);
    const dashboard = page.locator("section[aria-label='채굴 현황 대시보드']");
    await expect(dashboard).toHaveScreenshot("mining-dashboard-tablet.png");
  });

  test("POS 패널 모바일 뷰", async ({ page }) => {
    await page.setViewportSize({ width: 430, height: 920 });
    await page.goto(`${storyUrl}?id=dashboard-merchant-pos-panel--default&viewMode=story`);
    const panel = page.locator("section[aria-label='가맹점 POS 및 QR 패널']");
    await expect(panel).toHaveScreenshot("merchant-pos-mobile.png");
  });

  test("POS 패널 태블릿 뷰", async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 900 });
    await page.goto(`${storyUrl}?id=dashboard-merchant-pos-panel--default&viewMode=story`);
    const panel = page.locator("section[aria-label='가맹점 POS 및 QR 패널']");
    await expect(panel).toHaveScreenshot("merchant-pos-tablet.png");
  });
});

