"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Dumbbell,
  Sparkles,
  Download,
  ScrollText,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "대시보드", icon: LayoutDashboard, exact: true },
  { href: "/users", label: "회원 관리", icon: Users },
  { href: "/exercises", label: "운동 종목", icon: Dumbbell },
  { href: "/llm", label: "LLM 모델", icon: Sparkles },
  { href: "/exports", label: "좌표 내보내기", icon: Download },
  { href: "/audit", label: "감사 로그", icon: ScrollText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <span className="text-lg font-semibold tracking-tight text-text">
          PoseFit
        </span>
        <span className="rounded-sm bg-accent-soft px-1.5 py-0.5 text-xs font-medium text-accent-active">
          Admin
        </span>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 p-3">
        {NAV.map(({ href, label, icon: Icon, exact }) => {
          const active = exact ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-accent-soft text-accent-active"
                  : "text-text-muted hover:bg-surface-muted hover:text-text",
              )}
            >
              <Icon className="size-4" aria-hidden />
              {label}
            </Link>
          );
        })}
      </nav>
      <p className="px-6 py-4 text-xs text-text-subtle">
        운영 도구 · 내부 전용
      </p>
    </aside>
  );
}
