"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui";
import { formatNumber } from "@/lib/format";

/** URL searchParams 기반 오프셋 페이지네이션 (다른 쿼리는 보존). */
export function Pagination({
  page,
  size,
  total,
}: {
  page: number;
  size: number;
  total: number;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const pages = Math.max(1, Math.ceil(total / size));

  function go(p: number) {
    const q = new URLSearchParams(params.toString());
    q.set("page", String(p));
    router.push(`${pathname}?${q.toString()}`);
  }

  return (
    <div className="flex items-center justify-between gap-4 pt-1">
      <p className="text-xs text-text-subtle">
        총 {formatNumber(total)}건 · {page}/{pages} 페이지
      </p>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="secondary"
          disabled={page <= 1}
          onClick={() => go(page - 1)}
          leftIcon={<ChevronLeft aria-hidden />}
        >
          이전
        </Button>
        <Button
          size="sm"
          variant="secondary"
          disabled={page >= pages}
          onClick={() => go(page + 1)}
          rightIcon={<ChevronRight aria-hidden />}
        >
          다음
        </Button>
      </div>
    </div>
  );
}
