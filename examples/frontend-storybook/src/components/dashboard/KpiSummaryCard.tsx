import React from "react";

export type KpiTrend = "up" | "down" | "flat";

export interface KpiSummaryCardProps {
  label: string;
  value: string;
  deltaLabel?: string;
  trend?: KpiTrend;
  caption?: string;
  onClick?: () => void;
  isLoading?: boolean;
  hasError?: boolean;
}

const trendIcon: Record<KpiTrend, string> = {
  up: "▲",
  down: "▼",
  flat: "■"
};

const trendColor: Record<KpiTrend, string> = {
  up: "var(--aeg-status-success-foreground, #0f7a55)",
  down: "var(--aeg-status-danger-foreground, #a12c2c)",
  flat: "var(--aeg-text-muted, #6b6b6b)"
};

export const KpiSummaryCard: React.FC<KpiSummaryCardProps> = ({
  label,
  value,
  deltaLabel,
  trend = "flat",
  caption,
  onClick,
  isLoading = false,
  hasError = false
}) => {
  let content: React.ReactNode;

  if (isLoading) {
    content = (
      <div style={{ display: "grid", gap: "12px" }}>
        <div
          style={{
            height: "16px",
            width: "40%",
            borderRadius: "8px",
            background: "var(--aeg-surface-skeleton, #f0f0f0)"
          }}
        />
        <div
          style={{
            height: "32px",
            width: "60%",
            borderRadius: "12px",
            background: "var(--aeg-surface-skeleton, #f0f0f0)"
          }}
        />
        <div
          style={{
            height: "14px",
            width: "45%",
            borderRadius: "6px",
            background: "var(--aeg-surface-skeleton, #f0f0f0)"
          }}
        />
      </div>
    );
  } else if (hasError) {
    content = (
      <div style={{ display: "grid", gap: "8px" }}>
        <span
          role="img"
          aria-label="경고"
          style={{ fontSize: "20px", color: "var(--aeg-status-danger-foreground, #a12c2c)" }}
        >
          ⚠
        </span>
        <p
          style={{
            fontSize: "14px",
            color: "var(--aeg-status-danger-foreground, #a12c2c)",
            margin: 0
          }}
        >
          데이터를 불러오지 못했습니다.
        </p>
        <span
          style={{
            fontSize: "12px",
            color: "var(--aeg-text-muted, #6b6b6b)"
          }}
        >
          새로고침 후 다시 시도하세요.
        </span>
      </div>
    );
  } else {
    content = (
      <>
        <span
          style={{
            fontSize: "12px",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: "var(--aeg-text-muted, #6b6b6b)",
            fontWeight: 600
          }}
        >
          {label}
        </span>
        <strong
          style={{
            fontSize: "32px",
            lineHeight: "40px",
            color: "var(--aeg-text-primary, #191919)",
            fontWeight: 700
          }}
        >
          {value}
        </strong>
        {deltaLabel ? (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "13px",
              fontWeight: 600,
              color: trendColor[trend]
            }}
            aria-label={`변동: ${deltaLabel}`}
          >
            <span aria-hidden="true">{trendIcon[trend]}</span>
            {deltaLabel}
          </span>
        ) : null}
        {caption ? (
          <span
            style={{
              fontSize: "12px",
              color: "var(--aeg-text-muted, #6b6b6b)"
            }}
          >
            {caption}
          </span>
        ) : null}
      </>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="aeg-kpi-card"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        justifyContent: "center",
        gap: "12px",
        width: "100%",
        minHeight: "140px",
        padding: "20px",
        borderRadius: "20px",
        border: "1px solid var(--aeg-border-subtle, #e0e0e0)",
        background: "var(--aeg-surface-elevated, #ffffff)",
        boxShadow: "0 16px 32px rgba(12, 12, 12, 0.08)",
        cursor: onClick ? "pointer" : "default",
        transition: "transform 140ms ease, box-shadow 140ms ease"
      }}
      onMouseDown={(event) => {
        event.currentTarget.style.transform = "scale(0.98)";
      }}
      onMouseUp={(event) => {
        event.currentTarget.style.transform = "scale(1)";
      }}
      onMouseLeave={(event) => {
        event.currentTarget.style.transform = "scale(1)";
      }}
      aria-live={isLoading ? "polite" : "off"}
    >
      {content}
    </button>
  );
};

export default KpiSummaryCard;
