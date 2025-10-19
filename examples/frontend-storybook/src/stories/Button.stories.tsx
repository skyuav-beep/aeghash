import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "../components/Button";

const meta: Meta<typeof Button> = {
  title: "Tokens/Button",
  component: Button,
  parameters: {
    layout: "centered"
  },
  argTypes: {
    variant: {
      control: { type: "radio" },
      options: ["primary", "secondary"]
    }
  }
};

export default meta;

type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    children: "Primary Button",
    variant: "primary"
  }
};

export const Secondary: Story = {
  args: {
    children: "Secondary Button",
    variant: "secondary"
  }
};
