import type { Meta, StoryObj } from "@storybook/react";
import React from "react";
import { KpiSummaryCard } from "../components/dashboard/KpiSummaryCard";

const meta: Meta<typeof KpiSummaryCard> = {
  title: "Admin/KPI/KpiSummaryCard",
  component: KpiSummaryCard
};

export default meta;
type Story = StoryObj<typeof KpiSummaryCard>;

export const Default: Story = {
  args: {
    label: "총 매출 PV",
    value: "182,450",
    deltaLabel: "전일 대비 +12.4%",
    trend: "up",
    caption: "목표 대비 92%"
  }
};

export const Loading: Story = {
  args: {
    label: "보너스 지급액",
    value: "0",
    isLoading: true
  }
};

export const ErrorState: Story = {
  args: {
    label: "보류 보너스",
    value: "0",
    hasError: true
  }
};

export const FlatTrend: Story = {
  args: {
    label: "신규 가입자",
    value: "1,024",
    deltaLabel: "전주 대비 +0.4%",
    trend: "flat",
    caption: "월 목표 대비 48%"
  }
};
