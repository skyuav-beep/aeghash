import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import { OnboardingCard, type OnboardingCardProps } from "../components/education/OnboardingCard";

const meta: Meta<OnboardingCardProps> = {
  title: "Education/Onboarding Card",
  component: OnboardingCard,
  parameters: {
    layout: "centered"
  },
  args: {
    onAction: fn()
  }
};

export default meta;

type Story = StoryObj<OnboardingCardProps>;

export const MiningSummary: Story = {
  args: {
    step: 1,
    title: "채굴 요약 카드 살펴보기",
    description: "총 해시 파워와 일일 수익으로 오늘의 성과를 빠르게 확인하세요.",
    ctaLabel: "채굴 현황 보기"
  }
};

export const MerchantRoles: Story = {
  args: {
    step: 5,
    title: "직원 권한 관리",
    description: "점장/캐셔 권한을 분리해 안전한 결제를 유지하세요.",
    ctaLabel: "직원 초대"
  }
};

