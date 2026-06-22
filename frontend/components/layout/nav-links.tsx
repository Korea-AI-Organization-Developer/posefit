"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  /** active 판정에 쓸 prefix. 없으면 href 그대로 사용. */
  activePrefix?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "대시보드", href: "/dashboard" },
  { label: "운동하기", href: "/exercises", activePrefix: "/exercise" },
  { label: "리포트", href: "/reports" },
  { label: "설정", href: "/settings" },
];

export function NavLinks() {
  const pathname = usePathname();

  return (
    <nav aria-label="주요 메뉴" className="flex h-full items-center gap-6">
      {NAV_ITEMS.map(({ label, href, activePrefix }) => {
        const base = activePrefix ?? href;
        const active = pathname === href || pathname === base || pathname.startsWith(`${base}/`);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "relative flex h-full items-center text-sm transition-colors duration-150 ease-out",
              active
                ? "font-medium text-text after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-accent"
                : "text-text-muted hover:text-text",
            )}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
