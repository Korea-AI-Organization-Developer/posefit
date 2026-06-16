"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, LogOut, Settings } from "lucide-react";

import { cn } from "@/lib/utils";

export interface UserMenuProps {
  userName: string;
  avatarUrl?: string | null;
}

/*
 * 네비 우측 사용자 메뉴 — 아바타 클릭 시 설정·로그아웃 드롭다운.
 * 로그아웃은 기존 /auth/logout 라우트(백엔드 token_version +1 후 쿠키 제거) 재사용.
 */
export function UserMenu({ userName, avatarUrl }: UserMenuProps) {
  const router = useRouter();
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onDocMouseDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocMouseDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  async function logout() {
    setLoggingOut(true);
    await fetch("/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
  }

  return (
    <div className="relative ml-auto" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-md py-1 pl-2.5 pr-1.5 transition-colors duration-150 ease-out hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <span className="text-sm text-text-muted">{userName} 님</span>
        {avatarUrl ? (
          <Image
            src={avatarUrl}
            alt=""
            width={32}
            height={32}
            className="size-8 rounded-full object-cover"
          />
        ) : (
          <span
            aria-hidden
            className="flex size-8 items-center justify-center rounded-full bg-surface-muted text-xs font-medium text-text-muted"
          >
            {userName.charAt(0)}
          </span>
        )}
        <ChevronDown
          aria-hidden
          className={cn(
            "size-4 text-text-subtle transition-transform duration-150 ease-out",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-30 mt-2 w-44 rounded-md border border-border bg-surface p-1 shadow-sm"
        >
          <Link
            role="menuitem"
            href="/settings"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 rounded-sm px-3 py-2 text-sm transition-colors duration-150 ease-out hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent [&_svg]:size-4 [&_svg]:text-text-subtle"
          >
            <Settings aria-hidden />
            설정
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={logout}
            disabled={loggingOut}
            className="flex w-full items-center gap-2.5 rounded-sm px-3 py-2 text-sm text-danger transition-colors duration-150 ease-out hover:bg-danger-soft focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent disabled:opacity-50 [&_svg]:size-4"
          >
            <LogOut aria-hidden />
            로그아웃
          </button>
        </div>
      )}
    </div>
  );
}
