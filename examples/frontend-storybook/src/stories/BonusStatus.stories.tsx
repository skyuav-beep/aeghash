import type { Meta, StoryObj } from "@storybook/react";
import React from "react";
import { BonusAlertBanner } from "../components/bonus/BonusAlertBanner";
import { BonusStatusBadge } from "../components/bonus/BonusStatusBadge";

const meta: Meta<typeof BonusStatusBadge> = {
  title: "Admin/Bonus/StatusMessaging",
  component: BonusStatusBadge
};

export default meta;
type Story = StoryObj<typeof BonusStatusBadge>;

export const Badges: Story = {
  render: () => (
    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
      <BonusStatusBadge status="confirmed" />
      <BonusStatusBadge status="pending" />
      <BonusStatusBadge status="on_hold" />
      <BonusStatusBadge status="retrying" />
      <BonusStatusBadge status="failed" />
    </div>
  )
};

export const AlertFailed: Story = {
  render: () => (
    <BonusAlertBanner
      severity="failed"
      title="보너스 지급 실패 3건이 감지되었습니다."
      description="지급 재시도 후에도 실패했습니다. 로그를 검토하고 수동으로 보정하세요."
      primaryActionLabel="보너스 큐 열기"
      onPrimaryAction={() => {
        // noop for story
      }}
      onDismiss={() => {
        // noop for story
      }}
    />
  )
};

export const AlertOnHold: Story = {
  render: () => (
    <BonusAlertBanner
      severity="on_hold"
      title="보류 중인 보너스가 있습니다."
      description="KYC 검토 대기 중인 지급건이 12건입니다. 12시간 이상 보류된 항목부터 확인하세요."
      primaryActionLabel="보류 큐 확인"
    />
  )
};
