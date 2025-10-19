import React from "react";

export type TurnstileState = "idle" | "loading" | "success" | "error";

const DEFAULT_MESSAGES: Record<TurnstileState, string> = {
  idle: "보안 확인을 완료해주세요.",
  loading: "보안 검증 중입니다…",
  success: "보안 검증이 완료되었습니다.",
  error: "보안 검증에 실패했습니다. 다시 시도해주세요."
};

export interface TurnstileStatusProps {
  state?: TurnstileState;
  message?: string;
  onRetry?: () => void;
}

export const TurnstileStatus: React.FC<TurnstileStatusProps> = ({ state = "idle", message, onRetry }) => {
  const resolvedMessage = message ?? DEFAULT_MESSAGES[state];

  return (
    <div
      className={`aeg-turnstile aeg-turnstile--${state}`}
      role="status"
      aria-live={state === "error" ? "assertive" : "polite"}
    >
      <span className="aeg-turnstile__indicator" aria-hidden="true" />
      <span className="aeg-turnstile__message">{resolvedMessage}</span>
      {state === "error" && onRetry ? (
        <button type="button" className="aeg-turnstile__retry" onClick={onRetry}>
          다시 시도
        </button>
      ) : null}
    </div>
  );
};

export default TurnstileStatus;
