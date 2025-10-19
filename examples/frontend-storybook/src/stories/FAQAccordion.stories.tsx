import type { Meta, StoryObj } from "@storybook/react";
import { FAQAccordion, type FAQAccordionProps } from "../components/education/FAQAccordion";

const meta: Meta<FAQAccordionProps> = {
  title: "Education/FAQ Accordion",
  component: FAQAccordion,
  parameters: {
    layout: "centered"
  }
};

export default meta;

type Story = StoryObj<FAQAccordionProps>;

export const Default: Story = {
  args: {
    items: [
      {
        category: "채굴 현황",
        question: "채굴 데이터는 얼마나 자주 갱신되나요?",
        answer: "기본적으로 5분마다 HashDam API에서 최신 데이터를 동기화합니다."
      },
      {
        category: "출금/보안",
        question: "거절율이 높다는 경고가 뜹니다. 어떻게 해야 하나요?",
        answer: "네트워크 상태와 해시 장비 연결을 확인하고, 지속될 경우 고객센터에 문의하세요."
      },
      {
        category: "가맹점 결제",
        question: "QR의 유효 시간은 얼마나 되나요?",
        answer: "생성 후 5분 동안 유효하며, 시간이 지나면 다시 생성해야 합니다."
      }
    ]
  }
};

