import React, { FormEvent, useMemo, useState } from "react";
import Button from "../Button";
import InputField from "../InputField";
import { TurnstileState, TurnstileStatus } from "./TurnstileStatus";

export interface LoginFormValues {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface LoginFormProps {
  title?: string;
  subtitle?: string;
  defaultEmail?: string;
  defaultRememberMe?: boolean;
  errorMessage?: string;
  turnstileState?: TurnstileState;
  turnstileMessage?: string;
  isSubmitting?: boolean;
  onSubmit?: (values: LoginFormValues) => void;
  onForgotPassword?: () => void;
  onGoToSignup?: () => void;
  onRetryTurnstile?: () => void;
}

const DEFAULT_SUBTITLE = "계정에 로그인하고 대시보드를 확인하세요.";

export const LoginForm: React.FC<LoginFormProps> = ({
  title = "로그인",
  subtitle = DEFAULT_SUBTITLE,
  defaultEmail = "",
  defaultRememberMe = true,
  errorMessage,
  turnstileState = "idle",
  turnstileMessage,
  isSubmitting = false,
  onSubmit,
  onForgotPassword,
  onGoToSignup,
  onRetryTurnstile
}) => {
  const [email, setEmail] = useState(defaultEmail);
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(defaultRememberMe);

  const isSubmitDisabled = useMemo(() => {
    if (!email || !password) {
      return true;
    }
    if (turnstileState !== "success") {
      return true;
    }
    return isSubmitting;
  }, [email, password, turnstileState, isSubmitting]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitDisabled) {
      return;
    }
    onSubmit?.({ email, password, rememberMe });
  };

  return (
    <div className="aeg-auth-card" role="region" aria-label="로그인 양식">
      <header className="aeg-auth-card__header">
        <h2 className="aeg-auth-card__title">{title}</h2>
        <p className="aeg-auth-card__subtitle">{subtitle}</p>
      </header>

      {errorMessage ? (
        <div className="aeg-alert aeg-alert--error" role="alert">
          <span className="aeg-alert__icon" aria-hidden="true" />
          <div className="aeg-alert__content">{errorMessage}</div>
        </div>
      ) : null}

      <form className="aeg-form" onSubmit={handleSubmit} noValidate>
        <InputField
          type="email"
          label="이메일"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          placeholder="name@example.com"
          required
        />

        <InputField
          type="password"
          label="비밀번호"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
          helperText="대소문자, 숫자, 특수문자를 포함해 8자 이상 입력하세요."
        />

        <div className="aeg-form-inline">
          <label className="aeg-check">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(event) => setRememberMe(event.target.checked)}
            />
            로그인 상태 유지
          </label>
          <button type="button" className="aeg-inline-link" onClick={() => onForgotPassword?.()}>
            비밀번호 재설정
          </button>
        </div>

        <TurnstileStatus state={turnstileState} message={turnstileMessage} onRetry={onRetryTurnstile} />

        <Button type="submit" disabled={isSubmitDisabled}>
          {isSubmitting ? "로그인 중…" : "로그인"}
        </Button>
      </form>

      <div className="aeg-form-links" aria-live="polite">
        <span>아직 계정이 없으신가요?</span>
        <button type="button" onClick={() => onGoToSignup?.()}>
          회원가입
        </button>
      </div>
    </div>
  );
};

export default LoginForm;
