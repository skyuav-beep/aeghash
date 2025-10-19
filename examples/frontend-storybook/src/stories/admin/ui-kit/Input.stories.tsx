import type { Meta, StoryObj } from "@storybook/react";
import React, { useState } from "react";
import { InputField } from "../../../components/InputField";

const meta: Meta<typeof InputField> = {
  title: "Admin/UI Kit/Input",
  component: InputField,
  parameters: {
    docs: {
      description: {
        component:
          "관리자 입력 필드는 `components.input.*` 토큰과 `typography.body` 계열을 사용합니다. 라벨, 헬퍼/에러 메시지, 포커스/에러 상태 토큰 매핑을 확인하세요."
      }
    }
  },
  argTypes: {
    type: {
      control: { type: "select" },
      options: ["text", "email", "password", "number", "search"]
    },
    errorMessage: {
      control: { type: "text" }
    },
    helperText: {
      control: { type: "text" }
    }
  },
  args: {
    label: "라벨",
    placeholder: "값을 입력하세요",
    type: "text"
  }
};

export default meta;
type Story = StoryObj<typeof InputField>;

export const Playground: Story = {};

export const States: Story = {
  render: () => (
    <div style={{ display: "grid", gap: "16px", maxWidth: "480px" }}>
      <InputField label="기본" placeholder="search@domain.com" type="email" />
      <InputField
        label="헬퍼 텍스트"
        placeholder="예: HASH-12345"
        helperText="결제 후 발급되는 주문 번호를 입력하세요."
      />
      <InputField
        label="에러 상태"
        placeholder="0.00"
        type="number"
        errorMessage="허용되지 않는 금액입니다."
      />
      <InputField label="비활성" placeholder="입력 불가" disabled />
    </div>
  )
};

export const Controlled: Story = {
  render: () => {
    const [value, setValue] = useState("Team Hashdam");
    return (
      <div style={{ maxWidth: "360px" }}>
        <InputField
          label="조직 검색"
          placeholder="조직명을 입력"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          helperText={`${value.length}자`}
        />
      </div>
    );
  }
};
