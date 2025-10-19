import React from "react";
import { BonusStatus } from "./BonusStatusBadge";

export interface BonusAlertBannerProps {
  severity: Extract<BonusStatus, "on_hold" | "retrying" | "failed">;
  title: string;
  description?: string;
  primaryActionLabel?: string;
  onPrimaryAction?: () => void;
  onDismiss?: () => void;
}

const severityMeta: Record<
  BonusAlertBannerProps["severity"],
  {
    background: string;
    border: string;
    icon: string;
  }
> = {
  on_hold: {
    background: "var(--aeg-status-warning-background, #fff4d8)",
    border: "var(--aeg-status-warning-foreground, #9b6a12)",
    icon: "ri-alert-line"
  },
  retrying: {
    background: "var(--aeg-status-neutral-background, #f0f0f0)",
    border: "var(--aeg-status-neutral-foreground, #505050)",
    icon: "ri-refresh-line"
  },
  failed: {
    background: "var(--aeg-status-danger-background, #ffe0e0)",
    border: "var(--aeg-status-danger-foreground, #a12c2c)",
    icon: "ri-error-warning-line"
  }
};

export const BonusAlertBanner: React.FC<BonusAlertBannerProps> = ({
  severity,
  title,
  description,
  primaryActionLabel,
  onPrimaryAction,
  onDismiss
}) => {
  const meta = severityMeta[severity];
  return (
    <section
      role="alert"
      aria-live="polite"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "16px",
        padding: "16px 20px",
        borderRadius: "16px",
        border: `1px solid ${meta.border}`,
        background: meta.background,
        color: meta.border,
        boxShadow: "0 12px 24px rgba(15, 15, 15, 0.08)"
      }}
    >
      <i className={meta.icon} aria-hidden="true" style={{ fontSize: "20px", marginTop: "2px" }} />
      <div style={{ flex: 1 }}>
        <p style={{ margin: 0, fontWeight: 700, fontSize: "16px" }}>{title}</p>
        {description ? (
          <p
            style={{
              margin: "6px 0 0",
              fontSize: "13px",
              lineHeight: "20px"
            }}
          >
            {description}
          </p>
        ) : null}
      </div>
      <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
        {primaryActionLabel ? (
          <button
            type="button"
            onClick={onPrimaryAction}
            style={{
              padding: "8px 14px",
              borderRadius: "10px",
              border: "none",
              fontWeight: 600,
              cursor: "pointer",
              background: "var(--aeg-palette-primary, #fdc915)",
              color: "#191919"
            }}
          >
            {primaryActionLabel}
          </button>
        ) : null}
        {onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            aria-label="경고 닫기"
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              fontSize: "16px",
              color: meta.border
            }}
          >
            ✕
          </button>
        ) : null}
      </div>
    </section>
  );
};

export default BonusAlertBanner;
