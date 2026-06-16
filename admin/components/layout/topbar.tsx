"use client";

import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";

import type { Admin } from "@/lib/api/types";
import { logoutAction } from "@/lib/auth/actions";

const ROLE_LABEL: Record<Admin["role"], string> = {
  super_admin: "최고 관리자",
  admin: "관리자",
};

const TITLES: Array<[string, string]> = [
  ["/users", "회원 관리"],
  ["/exercises", "운동 종목"],
  ["/llm", "LLM 모델"],
  ["/exports", "좌표 내보내기"],
  ["/audit", "감사 로그"],
];

function titleFor(pathname: string): string {
  const hit = TITLES.find(([prefix]) => pathname.startsWith(prefix));
  return hit ? hit[1] : "대시보드";
}

export function Topbar({ admin }: { admin: Admin }) {
  const pathname = usePathname();

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-surface px-8">
      <h1 className="text-base font-semibold text-text">{titleFor(pathname)}</h1>
      <div className="flex items-center gap-4">
        <div className="text-right leading-tight">
          <p className="text-sm font-medium text-text">{admin.name}</p>
          <p className="text-xs text-text-subtle">
            {ROLE_LABEL[admin.role]} · {admin.email}
          </p>
        </div>
        <form action={logoutAction}>
          <button
            type="submit"
            className="flex items-center gap-1.5 rounded-sm px-2.5 py-1.5 text-sm text-text-muted transition-colors hover:bg-surface-muted hover:text-text"
          >
            <LogOut className="size-4" aria-hidden />
            로그아웃
          </button>
        </form>
      </div>
    </header>
  );
}
