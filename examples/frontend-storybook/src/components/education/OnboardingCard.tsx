import React from "react";
import Button from "../Button";

export interface OnboardingCardProps {
  step: number;
  title: string;
  description: string;
  ctaLabel: string;
  onAction?: () => void;
}

export const OnboardingCard: React.FC<OnboardingCardProps> = ({
  step,
  title,
  description,
  ctaLabel,
  onAction
}) => {
  return (
    <article
      className="aeg-onboarding-card"
      style={{
        borderRadius: "20px",
        border: "1px solid var(--aeg-colors-border-subtle, #e4e6eb)",
        background: "var(--aeg-colors-surface-primary, #ffffff)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        boxShadow: "var(--aeg-component-card-shadow, 0 12px 28px rgba(15, 23, 42, 0.12))"
      }}
    >
      <span
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "16px",
          background: "var(--aeg-colors-palette-primary, #fdc915)",
          color: "#0f172a",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 700,
          fontSize: "18px"
        }}
      >
        {step}
      </span>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <h3
          style={{
            margin: 0,
            fontSize: "var(--aeg-typography-subtitle-font-size, 20px)",
            color: "var(--aeg-colors-text-primary, #0f172a)"
          }}
        >
          {title}
        </h3>
        <p
          style={{
            margin: 0,
            color: "var(--aeg-colors-text-muted, #6b7280)",
            lineHeight: 1.5
          }}
        >
          {description}
        </p>
      </div>
      <div>
        <Button onClick={onAction} style={{ width: "100%" }}>
          {ctaLabel}
        </Button>
      </div>
    </article>
  );
};

export default OnboardingCard;

