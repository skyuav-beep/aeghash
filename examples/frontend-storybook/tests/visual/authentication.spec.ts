import { test, expect } from "@playwright/test";

const baseUrl = "http://127.0.0.1:6006/iframe.html";

test.describe("Authentication flows", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 430, height: 920 });
  });

  test("login form default state", async ({ page }) => {
    await page.goto(`${baseUrl}?id=authentication-login-form--default`);
    const card = page.locator(".aeg-auth-card");
    await expect(card).toHaveScreenshot("login-default.png");
  });

  test("login form with error", async ({ page }) => {
    await page.goto(`${baseUrl}?id=authentication-login-form--with-error`);
    const card = page.locator(".aeg-auth-card");
    await expect(card).toHaveScreenshot("login-error.png");
  });

  test("signup stepper security step", async ({ page }) => {
    await page.goto(`${baseUrl}?id=authentication-signup-stepper--security-step`);
    const card = page.locator(".aeg-auth-card");
    await expect(card).toHaveScreenshot("signup-security.png");
  });

  test("two factor lockout state", async ({ page }) => {
    await page.goto(`${baseUrl}?id=authentication-two-factor-prompt--lockout`);
    const card = page.locator(".aeg-auth-card");
    await expect(card).toHaveScreenshot("two-factor-lockout.png");
  });
});
