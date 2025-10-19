import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import { TwoFactorPrompt, type TwoFactorPromptProps } from "../components/forms/TwoFactorPrompt";

const meta: Meta<TwoFactorPromptProps> = {
  title: "Authentication/Two Factor Prompt",
  component: TwoFactorPrompt,
  parameters: {
    layout: "centered"
  },
  args: {
    onSubmit: fn(),
    onResend: fn(),
    onChangeDevice: fn()
  }
};

export default meta;

type Story = StoryObj<TwoFactorPromptProps>;

export const Default: Story = {};

export const WithError: Story = {
  args: {
    errorMessage: "코드가 올바르지 않습니다. 다시 입력하세요.",
    attemptsRemaining: 2
  }
};

export const Lockout: Story = {
  args: {
    lockoutMessage: "보안을 위해 로그인을 잠시 차단했습니다. 5분 후 다시 시도해주세요.",
    attemptsRemaining: 0
  }
};
