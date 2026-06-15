"use client";

import { useRouter } from "next/navigation";
import { Segmented, type SegmentedOption } from "@/components/ui";

export interface QueryTabsProps {
  /** 동기화할 쿼리 파라미터 키 (period · days · exerciseId) */
  paramKey: string;
  options: SegmentedOption<string>[];
  value: string;
  /** 다른 필터를 보존하기 위한 현재 쿼리 전체 (서버에서 주입) */
  currentParams: Record<string, string>;
  /** 이 값을 고르면 파라미터를 제거한다 (예: 종목 "전체") */
  clearOn?: string;
  size?: "sm" | "md";
  "aria-label"?: string;
}

/*
 * Segmented ↔ URL 동기화 — 선택 시 해당 파라미터만 갱신하고 나머지는 유지한다.
 * 데이터 fetch 는 서버(page.tsx)가 searchParams 로 수행하므로, 여기선 URL 만 바꾼다.
 */
export function QueryTabs({
  paramKey,
  options,
  value,
  currentParams,
  clearOn,
  size,
  "aria-label": ariaLabel,
}: QueryTabsProps) {
  const router = useRouter();

  function onChange(next: string) {
    const sp = new URLSearchParams(currentParams);
    if (clearOn != null && next === clearOn) sp.delete(paramKey);
    else sp.set(paramKey, next);
    const qs = sp.toString();
    router.push(qs ? `/reports?${qs}` : "/reports", { scroll: false });
  }

  return (
    <Segmented
      options={options}
      value={value}
      onChange={onChange}
      size={size}
      aria-label={ariaLabel}
    />
  );
}
