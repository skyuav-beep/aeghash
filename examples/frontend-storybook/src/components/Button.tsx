import React, { useState } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive" | "link";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
}

const variantTokens: Record<
  ButtonVariant,
  {
    background: string;
    color: string;
    border: string;
    shadow: string;
    hoverShadow: string;
    pressedTransform: string;
    textDecoration?: string;
  }
> = {
  primary: {
    background: "var(--aeg-component-button-primary-background, #1c1c1c)",
    color: "var(--aeg-component-button-primary-foreground, #ffffff)",
    border: "var(--aeg-component-button-primary-border, 1px solid transparent)",
    shadow: "var(--aeg-component-button-primary-shadow, 0 2px 8px rgba(0,0,0,0.12))",
    hoverShadow: "var(--aeg-component-button-primary-shadow-hover, 0 4px 12px rgba(0,0,0,0.16))",
    pressedTransform: "var(--aeg-component-button-primary-pressed-transform, scale(0.97))"
  },
  secondary: {
    background: "var(--aeg-component-button-secondary-background, #ffffff)",
    color: "var(--aeg-component-button-secondary-foreground, #1c1c1c)",
    border: "var(--aeg-component-button-secondary-border, 1px solid #d6d6d6)",
    shadow: "var(--aeg-component-button-secondary-shadow, 0 1px 4px rgba(0,0,0,0.08))",
    hoverShadow: "var(--aeg-component-button-secondary-shadow-hover, 0 2px 8px rgba(0,0,0,0.12))",
    pressedTransform: "var(--aeg-component-button-secondary-pressed-transform, scale(0.97))"
  },
  ghost: {
    background: "var(--aeg-component-button-ghost-background, transparent)",
    color: "var(--aeg-component-button-ghost-foreground, #1c1c1c)",
    border: "var(--aeg-component-button-ghost-border, 1px solid rgba(28,28,28,0.16))",
    shadow: "var(--aeg-component-button-ghost-shadow, none)",
    hoverShadow: "var(--aeg-component-button-ghost-shadow-hover, 0 2px 8px rgba(0,0,0,0.08))",
    pressedTransform: "var(--aeg-component-button-ghost-pressed-transform, scale(0.97))"
  },
  destructive: {
    background: "var(--aeg-component-button-destructive-background, #d92d20)",
    color: "var(--aeg-component-button-destructive-foreground, #ffffff)",
    border: "var(--aeg-component-button-destructive-border, 1px solid transparent)",
    shadow: "var(--aeg-component-button-destructive-shadow, 0 2px 8px rgba(217,45,32,0.35))",
    hoverShadow: "var(--aeg-component-button-destructive-shadow-hover, 0 4px 14px rgba(217,45,32,0.45))",
    pressedTransform: "var(--aeg-component-button-destructive-pressed-transform, scale(0.97))"
  },
  link: {
    background: "var(--aeg-component-button-link-background, transparent)",
    color: "var(--aeg-component-button-link-foreground, #1c62ff)",
    border: "var(--aeg-component-button-link-border, 1px solid transparent)",
    shadow: "var(--aeg-component-button-link-shadow, none)",
    hoverShadow: "var(--aeg-component-button-link-shadow-hover, none)",
    pressedTransform: "var(--aeg-component-button-link-pressed-transform, scale(0.97))",
    textDecoration: "var(--aeg-component-button-link-text-decoration, none)"
  }
};

const disabledStyle: React.CSSProperties = {
  background: "var(--aeg-component-button-disabled-background, #f2f2f2)",
  color: "var(--aeg-component-button-disabled-foreground, #9a9a9a)",
  border: "var(--aeg-component-button-disabled-border, 1px solid #e0e0e0)",
  boxShadow: "none",
  cursor: "not-allowed",
  opacity: 0.72
};

const Spinner: React.FC<{ color: string }> = ({ color }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    role="presentation"
    aria-hidden="true"
    style={{ marginRight: "8px" }}
  >
    <circle
      cx="8"
      cy="8"
      r="6"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeOpacity="0.24"
    />
    <path
      d="M14 8a6 6 0 0 0-6-6"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
    >
      <animateTransform
        attributeName="transform"
        type="rotate"
        from="0 8 8"
        to="360 8 8"
        dur="0.75s"
        repeatCount="indefinite"
      />
    </path>
  </svg>
);

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  isLoading = false,
  disabled,
  style,
  onMouseEnter,
  onMouseLeave,
  onMouseDown,
  onMouseUp,
  ...props
}) => {
  const [hovered, setHovered] = useState(false);
  const [pressed, setPressed] = useState(false);
  const tokens = variantTokens[variant];
  const isDisabled = Boolean(disabled || isLoading);

  const computedStyle: React.CSSProperties = {
    padding: "var(--aeg-component-button-padding-vertical, 12px) var(--aeg-component-button-padding-horizontal, 20px)",
    borderRadius: "var(--aeg-component-button-border-radius, 12px)",
    fontSize: "var(--aeg-typography-button-font-size, 16px)",
    lineHeight: "var(--aeg-typography-button-line-height, 24px)",
    letterSpacing: "var(--aeg-typography-button-letter-spacing, 0)",
    fontWeight: "var(--aeg-typography-button-font-weight, 600)",
    transition: "transform 120ms ease, box-shadow 120ms ease",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    cursor: isDisabled ? "not-allowed" : "pointer",
    textDecoration: tokens.textDecoration,
    background: tokens.background,
    color: tokens.color,
    border: tokens.border,
    boxShadow: hovered ? tokens.hoverShadow : tokens.shadow,
    transform: pressed ? tokens.pressedTransform : "scale(1)",
    pointerEvents: isDisabled ? "none" : undefined,
    ...(isDisabled ? disabledStyle : undefined),
    ...(style ?? {})
  };

  return (
    <button
      {...props}
      className="aeg-button"
      type={props.type ?? "button"}
      data-variant={variant}
      disabled={isDisabled}
      aria-busy={isLoading || undefined}
      onMouseEnter={(event) => {
        setHovered(true);
        onMouseEnter?.(event);
      }}
      onMouseLeave={(event) => {
        setHovered(false);
        setPressed(false);
        onMouseLeave?.(event);
      }}
      onMouseDown={(event) => {
        if (!isDisabled) {
          setPressed(true);
        }
        onMouseDown?.(event);
      }}
      onMouseUp={(event) => {
        setPressed(false);
        onMouseUp?.(event);
      }}
      style={computedStyle}
    >
      {isLoading ? <Spinner color={tokens.color || "#1c1c1c"} /> : null}
      <span>{children}</span>
    </button>
  );
};

export default Button;
