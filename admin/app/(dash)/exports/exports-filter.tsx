"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { AdminExercise, SessionStatus } from "@/lib/api/types";
import { SESSION_STATUS_LABEL } from "@/lib/labels";

const STATUS_OPTIONS: SessionStatus[] = ["completed", "in_progress", "aborted"];

export function ExportsFilter({
  exercises,
  exerciseId,
  status,
  from,
  to,
}: {
  exercises: AdminExercise[];
  exerciseId: string;
  status: string;
  from: string;
  to: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  function apply(key: string, value: string) {
    const q = new URLSearchParams(params.toString());
    value ? q.set(key, value) : q.delete(key);
    q.delete("page");
    router.push(`${pathname}?${q.toString()}`);
  }

  return (
    <div className="flex flex-wrap gap-2">
      <select
        value={status}
        onChange={(e) => apply("status", e.target.value)}
        className="h-10 rounded-sm border border-border bg-surface px-3 text-sm text-text outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
      >
        <option value="">전체 상태</option>
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s}>
            {SESSION_STATUS_LABEL[s]}
          </option>
        ))}
      </select>

      <select
        value={exerciseId}
        onChange={(e) => apply("exerciseId", e.target.value)}
        className="h-10 rounded-sm border border-border bg-surface px-3 text-sm text-text outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
      >
        <option value="">전체 종목</option>
        {exercises.map((ex) => (
          <option key={ex.id} value={ex.id}>
            {ex.nameKo}
          </option>
        ))}
      </select>

      <input
        type="datetime-local"
        value={from}
        onChange={(e) => apply("from", e.target.value)}
        className="h-10 rounded-sm border border-border bg-surface px-3 text-sm text-text outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
      />
      <span className="flex items-center text-sm text-text-muted">~</span>
      <input
        type="datetime-local"
        value={to}
        onChange={(e) => apply("to", e.target.value)}
        className="h-10 rounded-sm border border-border bg-surface px-3 text-sm text-text outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
      />
    </div>
  );
}
