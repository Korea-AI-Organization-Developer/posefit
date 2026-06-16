import type { InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export function Input({
  label,
  helperText,
  error,
  leftIcon,
  rightIcon,
  className,
  ...props
}: InputProps) {
  return (
    <label className={cn("block", className)}>
      {label && (
        <span className="mb-1.5 block text-sm font-medium text-text">
          {label}
        </span>
      )}
      <span
        className={cn(
          "flex h-10 items-center gap-2 rounded-sm border bg-surface px-3",
          "transition-colors duration-150 ease-out",
          "focus-within:ring-2 has-[input:disabled]:bg-surface-muted has-[input:disabled]:opacity-60",
          error
            ? "border-danger focus-within:ring-danger-soft"
            : "border-border focus-within:border-accent focus-within:ring-accent-soft",
        )}
      >
        {leftIcon && (
          <span className="text-text-subtle [&_svg]:size-4" aria-hidden>
            {leftIcon}
          </span>
        )}
        <input
          aria-invalid={error ? true : undefined}
          className="h-full w-full bg-transparent text-sm text-text outline-none placeholder:text-text-subtle disabled:cursor-not-allowed"
          {...props}
        />
        {rightIcon && (
          <span className="text-text-subtle [&_svg]:size-4" aria-hidden>
            {rightIcon}
          </span>
        )}
      </span>
      {(error || helperText) && (
        <span
          className={cn(
            "mt-1.5 block text-sm",
            error ? "text-danger" : "text-text-muted",
          )}
        >
          {error ?? helperText}
        </span>
      )}
    </label>
  );
}
