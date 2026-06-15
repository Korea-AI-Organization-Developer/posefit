import type { InputHTMLAttributes, ReactNode } from "react";
import { Check, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: ReactNode;
  /** 부분 선택 — '전체 동의'에서 일부 항목만 체크된 상태 */
  indeterminate?: boolean;
}

/*
 * 네이티브 input은 sr-only로 숨기고(키보드·폼 시맨틱 유지) 시각 상태는
 * checked/indeterminate prop으로 그린다 — Input과 동일하게 Server Component 유지.
 * 제어 컴포넌트로 쓴다(부모가 checked + onChange 보유).
 */
export function Checkbox({
  label,
  indeterminate = false,
  checked,
  disabled,
  className,
  ...props
}: CheckboxProps) {
  const active = indeterminate || Boolean(checked);
  return (
    <label
      className={cn(
        "inline-flex items-start gap-2.5 text-sm text-text",
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
        className,
      )}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        aria-checked={indeterminate ? "mixed" : checked}
        className="peer sr-only"
        {...props}
      />
      <span
        aria-hidden
        className={cn(
          "mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-sm border",
          "transition-colors duration-150 ease-out",
          "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent",
          active
            ? "border-accent bg-accent text-white"
            : "border-border-strong bg-surface",
        )}
      >
        {indeterminate ? (
          <Minus className="size-3.5" strokeWidth={3} />
        ) : checked ? (
          <Check className="size-3.5" strokeWidth={3} />
        ) : null}
      </span>
      {label && <span className="leading-snug">{label}</span>}
    </label>
  );
}
