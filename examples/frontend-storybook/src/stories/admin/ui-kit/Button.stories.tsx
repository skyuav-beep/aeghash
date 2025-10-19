import type { Meta, StoryObj } from "@storybook/react";
import React from "react";
import { Button, ButtonVariant } from "../../../components/Button";

const meta: Meta<typeof Button> = {
  title: "Admin/UI Kit/Button",
  component: Button,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component:
          "관리자 UI 전역에서 사용하는 버튼 컴포넌트입니다. 토큰 `components.button.*`과 `typography.button`을 사용하고, 상태별 변형(hover, focus, disabled, loading)을 스토리에서 확인할 수 있습니다."
      }
    }
  },
  argTypes: {
    variant: {
      control: { type: "select" },
      options: ["primary", "secondary", "ghost", "destructive", "link"]
    },
    isLoading: {
      control: { type: "boolean" }
    },
    disabled: {
      control: { type: "boolean" }
    },
    children: {
      control: { type: "text" }
    }
  },
  args: {
    children: "버튼",
    variant: "primary",
    disabled: false,
    isLoading: false
  }
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Playground: Story = {};

export const Variants: Story = {
  render: () => {
    const variants: ButtonVariant[] = ["primary", "secondary", "ghost", "destructive", "link"];
    return (
      <div style={{ display: "grid", gap: "16px" }}>
        {variants.map((variant) => (
          <div
            key={variant}
            style={{
              display: "flex",
              gap: "12px",
              alignItems: "center"
            }}
          >
            <span style={{ width: "88px", fontSize: "14px", color: "#475467" }}>{variant}</span>
            <Button variant={variant}>기본</Button>
            <Button variant={variant} isLoading>
              로딩
            </Button>
            <Button variant={variant} disabled>
              비활성
            </Button>
          </div>
        ))}
      </div>
    );
  }
};

export const WithIcons: Story = {
  render: (args) => (
    <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
      <Button {...args} variant="primary">
        <span role="img" aria-hidden="true">
          📊
        </span>
        리포트 보기
      </Button>
      <Button {...args} variant="secondary">
        <span role="img" aria-hidden="true">
          ➕
        </span>
        새 항목 추가
      </Button>
      <Button {...args} variant="destructive">
        <span role="img" aria-hidden="true">
          🗑️
        </span>
        삭제
      </Button>
      <Button {...args} variant="link">
        자세히 보기
        <span aria-hidden="true">→</span>
      </Button>
    </div>
  )
};

export const FocusStates: Story = {
  render: () => (
    <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
      <Button autoFocus variant="primary">
        자동 포커스
      </Button>
      <Button variant="secondary">탭 이동으로 포커스</Button>
      <Button variant="ghost">키보드 포커스 확인</Button>
    </div>
  )
};
