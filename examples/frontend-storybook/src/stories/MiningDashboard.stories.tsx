import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import {
  MiningDashboard,
  type MiningDashboardProps
} from "../components/dashboards/MiningDashboard";

const meta: Meta<MiningDashboardProps> = {
  title: "Dashboard/Mining Overview",
  component: MiningDashboard,
  parameters: {
    layout: "fullscreen"
  },
  args: {
    onRefresh: fn(),
    onSelectAsset: fn()
  }
};

export default meta;

type Story = StoryObj<MiningDashboardProps>;

export const Default: Story = {
  args: {
    totalHashPower: "128.4 GH/s",
    totalDailyProfit: "₩1,240,000",
    activeAlerts: 2,
    pendingWithdrawals: 5,
    assets: [
      {
        asset: "LTC",
        hashRate: "32.5 GH/s",
        rejectionRate: "1.2%",
        dailyProfit: "₩420,000",
        status: "healthy",
        lastUpdated: "5분 전"
      },
      {
        asset: "DOGE",
        hashRate: "28.7 GH/s",
        rejectionRate: "3.1%",
        dailyProfit: "₩310,000",
        status: "warning",
        lastUpdated: "3분 전"
      },
      {
        asset: "BELLS",
        hashRate: "18.9 GH/s",
        rejectionRate: "0.9%",
        dailyProfit: "₩150,000",
        status: "healthy",
        lastUpdated: "1분 전"
      },
      {
        asset: "JKC",
        hashRate: "12.4 GH/s",
        rejectionRate: "7.5%",
        dailyProfit: "₩90,000",
        status: "critical",
        lastUpdated: "10분 전"
      }
    ]
  }
};

export const NoAlerts: Story = {
  args: {
    totalHashPower: "98.7 GH/s",
    totalDailyProfit: "₩980,000",
    activeAlerts: 0,
    pendingWithdrawals: 1,
    assets: [
      {
        asset: "PEP",
        hashRate: "22.1 GH/s",
        rejectionRate: "0.4%",
        dailyProfit: "₩210,000",
        status: "healthy",
        lastUpdated: "2분 전"
      },
      {
        asset: "SHIC",
        hashRate: "16.3 GH/s",
        rejectionRate: "0.8%",
        dailyProfit: "₩170,000",
        status: "healthy",
        lastUpdated: "4분 전"
      }
    ]
  }
};

