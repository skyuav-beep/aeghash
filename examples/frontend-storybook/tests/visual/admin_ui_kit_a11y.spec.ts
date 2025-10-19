import { expect, test } from "@playwright/test";

const stories = [
  {
    id: "admin-ui-kit-button--playground",
    selector: "button.aeg-button",
    description: "Button playground renders button element with aeg-button class"
  },
  {
    id: "admin-ui-kit-input--states",
    selector: "label.aeg-form-field__label",
    description: "Input states render labelled form field"
  },
  {
    id: "admin-ui-kit-card--layouts",
    selector: "article.aeg-admin-card",
    description: "Card layouts render admin card articles"
  }
];

test.describe("Admin UI Kit accessibility smoke", () => {
  stories.forEach(({ id, selector, description }) => {
    test(description, async ({ page }) => {
      await page.goto(`/?path=/story/${id}`);
      await page.waitForSelector(selector, { state: "visible" });

      const contrastCheck = await page.evaluate(() => {
        const el = document.querySelector<HTMLElement>("[data-variant='primary']") ?? document.body;
        const style = window.getComputedStyle(el);
        return {
          background: style.backgroundColor,
          color: style.color,
          borderRadius: style.borderRadius
        };
      });

      expect(contrastCheck.background).not.toBe("");
      expect(contrastCheck.color).not.toBe("");
    });
  });

  test("Button loading state announces aria-busy", async ({ page }) => {
    await page.goto("/?path=/story/admin-ui-kit-button--variants");
    const loadingButton = page.locator("button", { hasText: "로딩" });
    await expect(loadingButton).toHaveAttribute("aria-busy", "true");
    await expect(loadingButton).toBeDisabled();
  });
});
