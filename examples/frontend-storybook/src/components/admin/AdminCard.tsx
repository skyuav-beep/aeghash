import React from "react";

export type AdminCardVariant = "info" | "data" | "state";
export type AdminCardState = "success" | "warning" | "error" | "neutral";

export interface AdminCardProps {
  variant?: AdminCardVariant;
  state?: AdminCardState;
  title: string;
  value: React.ReactNode;
  deltaLabel?: string;
  description?: string;
  footer?: React.ReactNode;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

const variantBackground: Record<AdminCardVariant, string> = {
  info: "var(--aeg-component-card-info-background, #ffffff)",
  data: "var(--aeg-component-card-data-background, #ffffff)",
  state: "var(--aeg-component-card-state-background, #ffffff)"
};

const variantBorder: Record<AdminCardVariant, string> = {
  info: "var(--aeg-component-card-info-border, 1px solid #e6e8f0)",
  data: "var(--aeg-component-card-data-border, 1px solid #e6e8f0)",
  state: "var(--aeg-component-card-state-border, 1px solid #e6e8f0)"
};

const variantShadow: Record<AdminCardVariant, string> = {
  info: "var(--aeg-component-card-info-shadow, 0 10px 30px rgba(15,23,42,0.05))",
  data: "var(--aeg-component-card-data-shadow, 0 12px 40px rgba(15,23,42,0.08))",
  state: "var(--aeg-component-card-state-shadow, 0 8px 24px rgba(15,23,42,0.06))"
};

const stateAccent: Record<AdminCardState, string> = {
  success: "var(--aeg-status-success, #12b76a)",
  warning: "var(--aeg-status-warning, #f79009)",
  error: "var(--aeg-status-danger, #f04438)",
  neutral: "var(--aeg-status-neutral, #1c1d21)"
};

export const AdminCard: React.FC<AdminCardProps> = ({
  variant = "info",
  state = "neutral",
  title,
  value,
  deltaLabel,
  description,
  footer,
  badge,
  actions,
  icon,
  children
}) => {
  const accentColor = variant === "state" ? stateAccent[state] : "var(--aeg-palette-primary, #f2a71b)";

  return (
    <article
      className="aeg-admin-card"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        padding: "24px",
        borderRadius: "var(--aeg-component-card-border-radius, 16px)",
        background: variantBackground[variant],
        border: variantBorder[variant],
        boxShadow: variantShadow[variant],
        minWidth: "280px",
        position: "relative"
      }}
    >
      {badge ? (
        <span
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            fontSize: "var(--aeg-typography-caption-font-size, 12px)",
            fontWeight: 600,
            color: accentColor
          }}
        >
          {badge}
        </span>
      ) : null}
      <header style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {icon ? (
            <span
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "12px",
                background: "var(--aeg-component-card-icon-background, rgba(242, 167, 27, 0.12))",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                color: accentColor
              }}
            >
              {icon}
            </span>
          ) : null}
          <div>
            <p
              style={{
                margin: 0,
                color: "var(--aeg-typography-subtitle-color, #4b5563)",
                fontSize: "var(--aeg-typography-subtitle-font-size, 14px)",
                fontWeight: 500,
                letterSpacing: "0.01em",
                textTransform: "uppercase"
              }}
            >
              {title}
            </p>
            {deltaLabel ? (
              <span
                style={{
                  fontSize: "var(--aeg-typography-caption-font-size, 12px)",
                  color: accentColor,
                  fontWeight: 600
                }}
              >
                {deltaLabel}
              </span>
            ) : null}
          </div>
        </div>
        {actions ? <div style={{ display: "flex", gap: "8px" }}>{actions}</div> : null}
      </header>
      <div>
        <div
          style={{
            color: "var(--aeg-typography-display-color, #111827)",
            fontSize: "var(--aeg-typography-display-font-size, 32px)",
            fontWeight: 700,
            lineHeight: "36px"
          }}
        >
          {value}
        </div>
        {description ? (
          <p
            style={{
              marginTop: "8px",
              marginBottom: 0,
              color: "var(--aeg-typography-body-secondary-color, #6b7280)",
              fontSize: "var(--aeg-typography-body-font-size, 14px)",
              lineHeight: "20px"
            }}
          >
            {description}
          </p>
        ) : null}
      </div>
      {children ? <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>{children}</div> : null}
      {footer ? (
        <footer
          style={{
            paddingTop: "12px",
            borderTop: "1px solid var(--aeg-component-card-divider, rgba(17, 24, 39, 0.08))",
            fontSize: "var(--aeg-typography-caption-font-size, 12px)",
            color: "var(--aeg-typography-caption-color, #6b7280)"
          }}
        >
          {footer}
        </footer>
      ) : null}
    </article>
  );
};

export default AdminCard;
