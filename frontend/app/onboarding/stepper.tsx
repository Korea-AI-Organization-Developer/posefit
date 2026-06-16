"use client";

import { usePathname } from "next/navigation";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  { href: "/onboarding/terms", label: "약관 동의" },
  { href: "/onboarding/profile", label: "기본 정보" },
  { href: "/onboarding/face", label: "얼굴 등록" },
] as const;

/* 온보딩 진행 표시 — 현재 단계는 pathname으로 판단. 셸 없는 레이아웃 상단에 둔다. */
export function OnboardingStepper() {
  const pathname = usePathname();
  const currentIndex = STEPS.findIndex((s) => pathname.startsWith(s.href));

  return (
    <ol className="flex items-center justify-center gap-2">
      {STEPS.map((step, i) => {
        const done = i < currentIndex;
        const active = i === currentIndex;
        return (
          <li key={step.href} className="flex items-center gap-2">
            <span
              className={cn(
                "flex size-6 items-center justify-center rounded-full text-xs font-medium tabular-nums",
                done && "bg-accent text-white",
                active && "border border-accent text-accent",
                !done && !active && "border border-border text-text-subtle",
              )}
            >
              {done ? <Check className="size-3.5" strokeWidth={3} /> : i + 1}
            </span>
            <span
              className={cn(
                "text-sm",
                active ? "font-medium text-text" : "text-text-muted",
              )}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <span aria-hidden className="mx-1 h-px w-6 bg-border" />
            )}
          </li>
        );
      })}
    </ol>
  );
}
