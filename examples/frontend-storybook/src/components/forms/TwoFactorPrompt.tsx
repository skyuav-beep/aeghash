import React, { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Button from "../Button";
import InputField from "../InputField";

export interface TwoFactorPromptProps {
  title?: string;
  instructions?: string;
  helperText?: string;
  errorMessage?: string;
  attemptsRemaining?: number;
  isSubmitting?: boolean;
  lockoutMessage?: string;
  onSubmit?: (code: string) => void;
  onResend?: () => void;
  onChangeDevice?: () => void;
}

const DEFAULT_INSTRUCTIONS = "인증 앱에서 6자리 코드를 확인한 뒤 입력하세요.";
const DEFAULT_HELPER = "코드는 30초마다 새로 생성됩니다.";

export const TwoFactorPrompt: React.FC<TwoFactorPromptProps> = ({
  title = "2단계 인증",
  instructions = DEFAULT_INSTRUCTIONS,
  helperText = DEFAULT_HELPER,
  errorMessage,
  attemptsRemaining,
  isSubmitting = false,
  lockoutMessage,
  onSubmit,
  onResend,
  onChangeDevice
}) => {
  const [code, setCode] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const normalizedCode = useMemo(() => code.replace(/\D/g, "").slice(0, 6), [code]);

  const isSubmitDisabled = normalizedCode.length !== 6 || isSubmitting || Boolean(lockoutMessage);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitDisabled) {
      return;
    }
    onSubmit?.(normalizedCode);
  };

  useEffect(() => {
    if (errorMessage) {
      setCode("");
      inputRef.current?.focus();
    }
  }, [errorMessage]);

  return (
    <div className="aeg-auth-card" role="region" aria-label="2단계 인증">
      <header className="aeg-auth-card__header">
        <h2 className="aeg-auth-card__title">{title}</h2>
        <p className="aeg-auth-card__subtitle">{instructions}</p>
      </header>

      {lockoutMessage ? (
        <div className="aeg-alert aeg-alert--error" role="alert">
          <span className="aeg-alert__icon" aria-hidden="true" />
          <div className="aeg-alert__content">{lockoutMessage}</div>
        </div>
      ) : null}

      <form className="aeg-form" onSubmit={handleSubmit}>
        <InputField
          label="인증 코드"
          value={normalizedCode}
          onChange={(event) => setCode(event.target.value)}
          ref={inputRef}
          inputMode="numeric"
          pattern="[0-9]*"
          placeholder="000000"
          autoFocus
          errorMessage={errorMessage}
          helperText={helperText}
          className="aeg-otp-input"
        />
        <Button type="submit" disabled={isSubmitDisabled}>
          {isSubmitting ? "확인 중…" : "확인"}
        </Button>
      </form>

      <div className="aeg-otp-meta" aria-live="polite">
        <span>
          {attemptsRemaining !== undefined
            ? `남은 시도 ${attemptsRemaining}회`
            : "정확한 코드를 입력해주세요."}
        </span>
        <div>
          <button type="button" className="aeg-inline-link" onClick={() => onResend?.()}>
            코드 재전송
          </button>
          <button type="button" className="aeg-inline-link" onClick={() => onChangeDevice?.()}>
            기기 변경 안내
          </button>
        </div>
      </div>
    </div>
  );
};

export default TwoFactorPrompt;
