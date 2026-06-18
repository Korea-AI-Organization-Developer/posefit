"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Badge, Button } from "@/components/ui";
import { USER_STATUS_LABEL, USER_STATUS_TONE } from "@/lib/labels";
import type { UserStatus } from "@/lib/api/types";

const ACTIONS: Array<{ to: UserStatus; label: string; variant: "secondary" | "danger" }> = [
  { to: "active", label: "활성화", variant: "secondary" },
  { to: "suspended", label: "정지", variant: "secondary" },
  { to: "withdrawn", label: "탈퇴 처리", variant: "danger" },
];

export function StatusControl({
  userId,
  initial,
}: {
  userId: number;
  initial: UserStatus;
}) {
  const router = useRouter();
  const [status, setStatus] = useState<UserStatus>(initial);
  const [pending, setPending] = useState<UserStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function change(to: UserStatus) {
    if (to === status) return;
    setPending(to);
    setError(null);
    try {
      const res = await fetch(`/api/admin/users/${userId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: to }),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      setStatus(to);
      router.refresh();
    } catch {
      setError("상태 변경에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-sm text-text-muted">현재 상태</span>
        <Badge tone={USER_STATUS_TONE[status]}>{USER_STATUS_LABEL[status]}</Badge>
      </div>
      <div className="flex flex-wrap gap-2">
        {ACTIONS.map((a) => (
          <Button
            key={a.to}
            size="sm"
            variant={a.variant}
            disabled={a.to === status || pending !== null}
            loading={pending === a.to}
            onClick={() => change(a.to)}
          >
            {a.label}
          </Button>
        ))}
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
