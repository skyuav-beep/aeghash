import type { Meta, StoryObj } from "@storybook/react";
import React from "react";
import { Button } from "../../../components/Button";
import { AdminCard } from "../../../components/admin/AdminCard";

const meta: Meta<typeof AdminCard> = {
  title: "Admin/UI Kit/Card",
  component: AdminCard,
  parameters: {
    docs: {
      description: {
        component:
          "카드 컴포넌트는 KPI, 데이터 요약, 상태 알림 등 관리자 대시보드에서 반복되는 패턴을 포괄합니다. `components.card.*`와 `typography.subtitle|display` 토큰을 사용합니다."
      }
    }
  },
  args: {
    title: "일일 PV",
    value: "128,420",
    deltaLabel: "+12.4% WoW",
    description: "전일 대비 PV 증가폭입니다."
  }
};

export default meta;
type Story = StoryObj<typeof AdminCard>;

export const Playground: Story = {};

export const Layouts: Story = {
  render: () => (
    <div
      style={{
        display: "grid",
        gap: "20px",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        alignItems: "stretch"
      }}
    >
      <AdminCard
        variant="info"
        title="신규 회원"
        value="342"
        deltaLabel="+5.8% WoW"
        description="추천 + 후원 가입 합계"
        footer="지난 7일 동안 1,980명이 Onboarding 진행"
      />
      <AdminCard
        variant="data"
        title="보너스 지급액"
        value="₩ 48,200,000"
        description="확정 + 보류 금액 포함"
        actions={
          <Button
            variant="secondary"
            style={{ padding: "8px 14px", fontSize: "14px", lineHeight: "20px", borderRadius: "10px" }}
          >
            리포트
          </Button>
        }
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "14px" }}>
          <span>확정</span>
          <strong style={{ color: "#111827" }}>₩ 32,420,000</strong>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "14px" }}>
          <span>보류</span>
          <strong style={{ color: "#dc6803" }}>₩ 15,780,000</strong>
        </div>
      </AdminCard>
      <AdminCard
        variant="state"
        state="warning"
        title="스필오버 대기열"
        value="58"
        description="50건 초과 시 알림 배너 노출"
        badge="주의"
        footer="대기열이 길어질 경우 우선순위 노드 재배치를 검토하세요."
      />
    </div>
  )
};

export const States: Story = {
  render: () => (
    <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
      <AdminCard variant="state" state="success" title="보너스 처리 SLA" value="92%">
        <p style={{ margin: 0 }}>12시간 내 처리율</p>
      </AdminCard>
      <AdminCard variant="state" state="warning" title="대기 지갑 검토" value="18">
        <p style={{ margin: 0 }}>승인 대기 출금</p>
      </AdminCard>
      <AdminCard variant="state" state="error" title="보너스 실패" value="7">
        <p style={{ margin: 0 }}>재시도 큐 등록 필요</p>
      </AdminCard>
    </div>
  )
};
