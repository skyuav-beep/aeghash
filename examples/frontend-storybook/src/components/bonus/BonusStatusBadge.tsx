import React from "react";

export type BonusStatus = "confirmed" | "pending" | "on_hold" | "retrying" | "failed";

export interface BonusStatusBadgeProps {
  status: BonusStatus;
  label?: string;
  withIcon?: boolean;
}

const statusMeta: Record<
  BonusStatus,
  {
    background: string;
    color: string;
    icon: string;
    defaultLabel: string;
  }
> = {
  confirmed: {
    background: "var(--aeg-status-success-background, #d8f5e3)",
    color: "var(--aeg-status-success-foreground, #0f7a55)",
    icon: "ri-check-line",
    defaultLabel: "지급 완료"
  },
  pending: {
    background: "var(--aeg-status-info-background, #dbe9ff)",
    color: "var(--aeg-status-info-foreground, #164b9c)",
    icon: "ri-time-line",
    defaultLabel: "지급 대기"
  },
  on_hold: {
    background: "var(--aeg-status-warning-background, #fff4d8)",
    color: "var(--aeg-status-warning-foreground, #9b6a12)",
    icon: "ri-alert-line",
    defaultLabel: "보류"
  },
  retrying: {
    background: "var(--aeg-status-neutral-background, #f0f0f0)",
    color: "var(--aeg-status-neutral-foreground, #505050)",
    icon: "ri-refresh-line",
    defaultLabel: "재시도 중"
  },
  failed: {
    background: "var(--aeg-status-danger-background, #ffe0e0)",
    color: "var(--aeg-status-danger-foreground, #a12c2c)",
    icon: "ri-error-warning-line",
    defaultLabel: "지급 실패"
  }
};

export const BonusStatusBadge: React.FC<BonusStatusBadgeProps> = ({
  status,
  label,
  withIcon = true
}) => {
  const meta = statusMeta[status];
  return (
    <span
      className="aeg-bonus-status-badge"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        fontSize: "12px",
        fontWeight: 600,
        padding: "4px 12px",
        borderRadius: "999px",
        background: meta.background,
        color: meta.color
      }}
      aria-label={`보너스 상태: ${label ?? meta.defaultLabel}`}
    >
      {withIcon ? <i className={meta.icon} aria-hidden="true" /> : null}
      {label ?? meta.defaultLabel}
    </span>
  );
};

export default BonusStatusBadge;
