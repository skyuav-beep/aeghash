import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import {
  MerchantPOSPanel,
  type MerchantPOSPanelProps
} from "../components/dashboards/MerchantPOSPanel";

const meta: Meta<MerchantPOSPanelProps> = {
  title: "Dashboard/Merchant POS Panel",
  component: MerchantPOSPanel,
  parameters: {
    layout: "fullscreen"
  },
  args: {
    onGenerateQr: fn(),
    onInviteStaff: fn(),
    onRefund: fn()
  }
};

export default meta;

type Story = StoryObj<MerchantPOSPanelProps>;

export const Default: Story = {
  args: {
    storeName: "AEG Downtown Store",
    qrUrl: "https://dummyimage.com/320x320/0f172a/fdc915.png&text=Scan+to+Pay",
    currencyLabel: "KRW",
    amount: "₩250,000",
    statusMessage: "QR이 생성되었습니다. 5분 내 스캔해주세요.",
    transactions: [
      {
        id: "TX-00045",
        amount: "₩128,000",
        status: "completed",
        timestamp: "2025-10-13 · 14:22"
      },
      {
        id: "TX-00044",
        amount: "₩87,500",
        status: "pending",
        timestamp: "2025-10-13 · 13:58"
      },
      {
        id: "TX-00043",
        amount: "₩42,300",
        status: "refunded",
        timestamp: "2025-10-13 · 13:10"
      }
    ],
    staff: [
      {
        name: "김민지",
        role: "manager",
        permissions: ["결제", "환불", "정산 보고서"],
        invitedAt: "2025-09-20"
      },
      {
        name: "박준혁",
        role: "cashier",
        permissions: ["결제"],
        invitedAt: "2025-09-25"
      }
    ]
  }
};

export const EmptyState: Story = {
  args: {
    storeName: "AEG Mall Shop",
    qrUrl: "https://dummyimage.com/320x320/1e293b/ffffff.png&text=Scan",
    currencyLabel: "KRW",
    amount: "₩0",
    statusMessage: "결제 금액을 입력하면 QR이 생성됩니다.",
    transactions: [],
    staff: []
  }
};

