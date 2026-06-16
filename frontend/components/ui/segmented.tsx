"use client";

import { useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface SegmentedOption<T extends string> {
  value: T;
  label: ReactNode;
}

export interface SegmentedProps<T extends string> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  size?: "sm" | "md";
  /** radiogroup 레이블 (스크린리더용) */
  "aria-label"?: string;
  className?: string;
}

const sizeClasses: Record<NonNullable<SegmentedProps<string>["size"]>, string> =
  {
    sm: "h-8 text-xs",
    md: "h-10 text-sm",
  };

/* iOS식 세그먼트 컨트롤 — 단일 선택. 성별(M/F/U)·리포트 기간(일/주/월/누적)에 공용. */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
  size = "md",
  className,
  "aria-label": ariaLabel,
}: SegmentedProps<T>) {
  const ref = useRef<HTMLDivElement>(null);

  function move(dir: 1 | -1) {
    const idx = options.findIndex((o) => o.value === value);
    const next = (idx + dir + options.length) % options.length;
    onChange(options[next].value);
    ref.current
      ?.querySelectorAll<HTMLButtonElement>('[role="radio"]')
      [next]?.focus();
  }

  return (
    <div
      ref={ref}
      role="radiogroup"
      aria-label={ariaLabel}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          e.preventDefault();
          move(1);
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          e.preventDefault();
          move(-1);
        }
      }}
      className={cn(
        "inline-flex items-center gap-0.5 rounded-md border border-border bg-surface-muted p-0.5",
        className,
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(opt.value)}
            className={cn(
              "inline-flex items-center justify-center rounded-sm px-3 font-medium",
              "transition-colors duration-150 ease-out",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
              sizeClasses[size],
              active
                ? "bg-surface text-text shadow-xs"
                : "text-text-muted hover:text-text",
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
