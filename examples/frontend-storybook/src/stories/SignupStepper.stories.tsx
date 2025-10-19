import type { Meta, StoryObj } from "@storybook/react";
import { fn } from "@storybook/test";
import { SignupStepper, type SignupStepperProps } from "../components/forms/SignupStepper";

const meta: Meta<SignupStepperProps> = {
  title: "Authentication/Signup Stepper",
  component: SignupStepper,
  parameters: {
    layout: "centered"
  },
  args: {
    onComplete: fn()
  }
};

export default meta;

type Story = StoryObj<SignupStepperProps>;

export const StepOne: Story = {
  args: {
    initialStep: 1
  }
};

export const StepTwo: Story = {
  args: {
    initialStep: 2
  }
};

export const SecurityStep: Story = {
  args: {
    initialStep: 3,
    turnstileState: "loading"
  }
};
