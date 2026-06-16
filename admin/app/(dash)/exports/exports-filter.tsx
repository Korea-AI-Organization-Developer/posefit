"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { AdminExercise } from "@/lib/api/types";

export function ExportsFilter({
  exercises,
  exerciseId,
}: {
  exercises: AdminExercise[];
  exerciseId: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  function apply(value: string) {
    const q = new URLSearchParams(params.toString());
    value ? q.set("exerciseId", value) : q.delete("exerciseId");
    q.delete("page");
    router.push(`${pathname}?${q.toString()}`);
  }

  return (
    <select
      value={exerciseId}
      onChange={(e) => apply(e.target.value)}
      className="h-10 rounded-sm border border-border bg-surface px-3 text-sm text-text outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
    >
      <option value="">전체 종목</option>
      {exercises.map((ex) => (
        <option key={ex.id} value={ex.id}>
          {ex.nameKo}
        </option>
      ))}
    </select>
  );
}
