import { forwardRef, useId } from "react";
import { cn } from "@/lib/utils";

type InputProps = {
  label?: string;
  error?: string | null;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightSlot?: React.ReactNode;
} & React.InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, leftIcon, rightSlot, className, id, ...props },
  ref,
) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error
    ? `${inputId}-error`
    : hint
      ? `${inputId}-hint`
      : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-text-muted"
        >
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            {leftIcon}
          </span>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cn(
            "w-full rounded-md bg-surface-2 px-4 py-2.5 text-sm text-text",
            "border border-border placeholder:text-text-muted/60",
            "transition-all duration-150",
            "focus:outline-none focus:border-primary focus:ring-2 focus:ring-[var(--accent-glow)]",
            leftIcon && "pl-10",
            rightSlot && "pr-11",
            error && "border-danger focus:border-danger focus:ring-danger/30",
            className,
          )}
          {...props}
        />
        {rightSlot && (
          <span className="absolute right-2 top-1/2 -translate-y-1/2">
            {rightSlot}
          </span>
        )}
      </div>
      {error ? (
        <p id={`${inputId}-error`} className="text-xs text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="text-xs text-text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
});
