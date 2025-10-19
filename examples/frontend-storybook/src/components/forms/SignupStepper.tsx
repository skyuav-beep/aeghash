import React, { useEffect, useMemo, useState } from "react";
import Button from "../Button";
import InputField from "../InputField";
import { TurnstileState, TurnstileStatus } from "./TurnstileStatus";

interface StepDefinition {
  id: number;
  label: string;
  description: string;
}

const STEPS: StepDefinition[] = [
  { id: 1, label: "정보 입력", description: "로그인 정보를 입력하세요." },
  { id: 2, label: "약관 동의", description: "필수 약관에 동의해주세요." },
  { id: 3, label: "보안 인증", description: "Turnstile 검증과 2FA 설정 안내." }
];

export interface SignupFormValues {
  name: string;
  email: string;
  password: string;
  referralCode?: string;
  agreements: Record<string, boolean>;
}

export interface SignupStepperProps {
  initialStep?: 1 | 2 | 3;
  onComplete?: (values: SignupFormValues) => void;
  turnstileState?: TurnstileState;
  onRetryTurnstile?: () => void;
}

const REQUIRED_TERMS = ["이용 약관 동의", "개인정보 처리방침 동의"];
const OPTIONAL_TERMS = ["마케팅 정보 수신 동의"];

export const SignupStepper: React.FC<SignupStepperProps> = ({
  initialStep = 1,
  onComplete,
  turnstileState = "idle",
  onRetryTurnstile
}) => {
  const [activeStep, setActiveStep] = useState(initialStep);
  const [formValues, setFormValues] = useState({
    name: "",
    email: "",
    password: "",
    referralCode: ""
  });
  const [agreements, setAgreements] = useState<Record<string, boolean>>({});
  const [localTurnstileState, setLocalTurnstileState] = useState<TurnstileState>(turnstileState);

  useEffect(() => {
    setLocalTurnstileState(turnstileState);
  }, [turnstileState]);

  const allRequiredChecked = useMemo(
    () => REQUIRED_TERMS.every((term) => agreements[term]),
    [agreements]
  );

  const handleAgreementChange = (term: string, next: boolean) => {
    setAgreements((prev) => ({
      ...prev,
      [term]: next
    }));
  };

  const toggleAllAgreements = (next: boolean) => {
    const nextState: Record<string, boolean> = {};
    [...REQUIRED_TERMS, ...OPTIONAL_TERMS].forEach((term) => {
      nextState[term] = next;
    });
    setAgreements(nextState);
  };

  const allSelected = useMemo(() => {
    return [...REQUIRED_TERMS, ...OPTIONAL_TERMS].every((term) => agreements[term]);
  }, [agreements]);

  const goNext = () => {
    if (activeStep >= STEPS.length) {
      const payload: SignupFormValues = {
        ...formValues,
        agreements
      };
      onComplete?.(payload);
      return;
    }
    setActiveStep((prev) => Math.min(prev + 1, STEPS.length));
  };

  const goPrevious = () => {
    setActiveStep((prev) => Math.max(prev - 1, 1));
  };

  const handleTurnstileProgress = () => {
    if (localTurnstileState === "success") {
      return;
    }
    setLocalTurnstileState("loading");
    setTimeout(() => {
      setLocalTurnstileState("success");
    }, 1200);
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 1:
        return (
          <div className="aeg-form">
            <InputField
              label="이름"
              value={formValues.name}
              onChange={(event) => setFormValues((prev) => ({ ...prev, name: event.target.value }))}
              placeholder="홍길동"
              required
            />
            <InputField
              label="이메일"
              type="email"
              value={formValues.email}
              onChange={(event) => setFormValues((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="name@example.com"
              required
            />
            <InputField
              label="비밀번호"
              type="password"
              value={formValues.password}
              onChange={(event) => setFormValues((prev) => ({ ...prev, password: event.target.value }))}
              helperText="8~20자, 숫자/특수문자 포함"
              required
            />
            <InputField
              label="추천코드 (선택)"
              value={formValues.referralCode}
              onChange={(event) =>
                setFormValues((prev) => ({ ...prev, referralCode: event.target.value }))
              }
              placeholder="선택 입력"
            />
          </div>
        );
      case 2:
        return (
          <div className="aeg-form" role="group" aria-labelledby="signup-terms">
            <div className="aeg-form-inline">
              <span id="signup-terms">약관 동의</span>
              <button className="aeg-inline-link" type="button" onClick={() => toggleAllAgreements(!allSelected)}>
                {allSelected ? "전체 해제" : "전체 동의"}
              </button>
            </div>
            {[...REQUIRED_TERMS, ...OPTIONAL_TERMS].map((term) => (
              <label key={term} className="aeg-check">
                <input
                  type="checkbox"
                  checked={Boolean(agreements[term])}
                  onChange={(event) => handleAgreementChange(term, event.target.checked)}
                  aria-required={REQUIRED_TERMS.includes(term)}
                />
                {term}
                {REQUIRED_TERMS.includes(term) ? <span aria-hidden="true">*</span> : null}
              </label>
            ))}
            <p className="aeg-form-field__helper">
              필수 약관에 동의해야 다음 단계로 진행할 수 있습니다.
            </p>
          </div>
        );
      case 3:
      default:
        return (
          <div className="aeg-form" role="group" aria-labelledby="signup-security">
            <h3 id="signup-security" className="aeg-form-field__label">
              보안 인증
            </h3>
            <TurnstileStatus
              state={localTurnstileState}
              onRetry={
                onRetryTurnstile ??
                (() => {
                  setLocalTurnstileState("idle");
                })
              }
            />
            <div className="aeg-highlight">
              <p className="aeg-highlight__title">추가 보안 레이어를 설정하세요</p>
              <p className="aeg-highlight__body">
                가입 완료 후 OTP 앱에서 6자리 코드를 등록하면 계정을 더욱 안전하게 보호할 수 있습니다.
              </p>
              <Button type="button" onClick={() => console.log("OTP 가이드 보기")}>
                OTP 앱 연결하기
              </Button>
            </div>
            <div className="aeg-otp-meta">
              <span>Turnstile 검증 후 완료 버튼이 활성화됩니다.</span>
              <button
                type="button"
                className="aeg-inline-link"
                onClick={handleTurnstileProgress}
              >
                보안 검증 시작
              </button>
            </div>
          </div>
        );
    }
  };

  const canProceed =
    activeStep === 1
      ? formValues.name !== "" && formValues.email !== "" && formValues.password.length >= 8
      : activeStep === 2
        ? allRequiredChecked
        : localTurnstileState === "success";

  return (
    <div className="aeg-auth-card" role="region" aria-label="회원가입 절차">
      <header className="aeg-auth-card__header">
        <h2 className="aeg-auth-card__title">회원가입</h2>
        <p className="aeg-auth-card__subtitle">3단계 절차를 따라 쉽게 가입할 수 있습니다.</p>
      </header>

      <ol className="aeg-stepper">
        {STEPS.map((step) => {
          const status =
            step.id === activeStep
              ? "active"
              : step.id < activeStep
                ? "completed"
                : "upcoming";
          return (
            <li
              key={step.id}
              className={`aeg-stepper__item aeg-stepper__item--${status}`}
              aria-current={status === "active" ? "step" : undefined}
            >
              <span className="aeg-stepper__badge">{step.id}</span>
              <div className="aeg-stepper__meta">
                <span className="aeg-stepper__label">{step.label}</span>
                <span className="aeg-stepper__description">{step.description}</span>
              </div>
            </li>
          );
        })}
      </ol>

      {renderStepContent()}

      <div className="aeg-stepper-actions">
        <Button type="button" variant="secondary" onClick={goPrevious} disabled={activeStep === 1}>
          이전
        </Button>
        <Button type="button" onClick={goNext} disabled={!canProceed}>
          {activeStep === STEPS.length ? "가입 완료" : "다음"}
        </Button>
      </div>
    </div>
  );
};

export default SignupStepper;
