import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import { LoginForm, type LoginFormProps } from "../components/forms/LoginForm";

const meta: Meta<LoginFormProps> = {
  title: "Authentication/Login Form",
  component: LoginForm,
  parameters: {
    layout: "centered",
    a11y: {
      config: {
        rules: [
          {
            id: "color-contrast",
            enabled: false
          }
        ]
      }
    }
  },
  argTypes: {
    turnstileState: {
      control: { type: "radio" },
      options: ["idle", "loading", "success", "error"]
    }
  },
  args: {
    onSubmit: fn(),
    onForgotPassword: fn(),
    onGoToSignup: fn()
  }
};

export default meta;

type Story = StoryObj<LoginFormProps>;

export const Default: Story = {
  args: {
    turnstileState: "idle"
  }
};

export const ReadyToSubmit: Story = {
  args: {
    defaultEmail: "team@aeg-hash.io",
    turnstileState: "success"
  }
};

export const WithError: Story = {
  args: {
    defaultEmail: "user@example.com",
    turnstileState: "success",
    errorMessage: "로그인에 실패했습니다. 이메일 혹은 비밀번호를 확인하세요."
  }
};

export const TurnstileFailure: Story = {
  args: {
    turnstileState: "error",
    turnstileMessage: "네트워크 문제로 보안 검증이 실패했습니다.",
    onRetryTurnstile: fn()
  }
};
