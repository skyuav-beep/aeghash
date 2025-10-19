import React, { forwardRef, useId } from "react";

export interface InputFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  helperText?: string;
  errorMessage?: string;
  containerClassName?: string;
  inputClassName?: string;
}

export const InputField = forwardRef<HTMLInputElement, InputFieldProps>(
  (
    {
      label,
      helperText,
      errorMessage,
      id,
      containerClassName,
      inputClassName,
      "aria-describedby": ariaDescribedBy,
      className,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;
    const helperId = helperText ? `${inputId}-helper` : undefined;
    const errorId = errorMessage ? `${inputId}-error` : undefined;
    const describedBy = [ariaDescribedBy, helperId, errorId].filter(Boolean).join(" ") || undefined;

    return (
      <div className={["aeg-form-field", containerClassName].filter(Boolean).join(" ")}>
        <label className="aeg-form-field__label" htmlFor={inputId}>
          {label}
        </label>
        <input
          {...props}
          id={inputId}
          ref={ref}
          className={["aeg-input", inputClassName, className, errorMessage ? "aeg-input--error" : ""]
            .filter(Boolean)
            .join(" ")}
          aria-invalid={errorMessage ? "true" : undefined}
          aria-describedby={describedBy}
        />
        {helperText ? (
          <p id={helperId} className="aeg-form-field__helper">
            {helperText}
          </p>
        ) : null}
        {errorMessage ? (
          <p id={errorId} className="aeg-form-field__error" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </div>
    );
  }
);

InputField.displayName = "InputField";

export default InputField;
