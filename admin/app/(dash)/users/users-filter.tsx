"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

import { Input } from "@/components/ui";

const STATUS_OPTIONS = [
  { value: "", label: "전체 상태" },
  { value: "active", label: "활성" },
  { value: "suspended", label: "정지" },
  { value: "withdrawn", label: "탈퇴" },
];

export function UsersFilter({
  query,
  status,
}: {
  query: string;
  status: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  function apply(next: { query?: string; status?: string }) {
    const q = new URLSearchParams(params.toString());
    if (next.query !== undefined) {
      next.query ? q.set("query", next.query) : q.delete("query");
    }
    if (next.status !== undefined) {
      next.status ? q.set("status", next.status) : q.delete("status");
    }
    q.delete("page"); // 필터 변경 시 1페이지로
    router.push(`${pathname}?${q.toString()}`);
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <form
        className="w-64"
        onSubmit={(e) => {
          e.preventDefault();
          const value = new FormData(e.currentTarget).get("query");
          apply({ query: String(value ?? "") });
        }}
      >
        <Input
          name="query"
          defaultValue={query}
          placeholder="닉네임·이메일 검색"
          leftIcon={<Search aria-hidden />}
        />
      </form>
      <select
        value={status}
        onChange={(e) => apply({ status: e.target.value })}
        className="h-10 rounded-sm border border-border bg-surface px-3 text-sm text-text outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
      >
        {STATUS_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
