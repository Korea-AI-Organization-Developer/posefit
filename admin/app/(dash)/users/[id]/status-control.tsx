"use client";

import { useState } from "react";

import { Badge, Button } from "@/components/ui";
import { USER_STATUS_LABEL, USER_STATUS_TONE } from "@/lib/labels";
import type { UserStatus } from "@/lib/api/types";

const ACTIONS: Array<{ to: UserStatus; label: string; variant: "secondary" | "danger" }> = [
  { to: "active", label: "활성화", variant: "secondary" },
  { to: "suspended", label: "정지", variant: "secondary" },
  { to: "withdrawn", label: "탈퇴 처리", variant: "danger" },
];

/*
 * 회원 상태 변경 — mock 단계라 로컬 상태만 갱신한다.
 * 백엔드 연동 시: PATCH /admin/users/{id} { status } 호출 후 router.refresh().
 */
export function StatusControl({
  userId,
  initial,
}: {
  userId: number;
  initial: UserStatus;
}) {
  const [status, setStatus] = useState<UserStatus>(initial);
  const [pending, setPending] = useState<UserStatus | null>(null);

  async function change(to: UserStatus) {
    if (to === status) return;
    setPending(to);
    // mock: 네트워크 지연 흉내
    await new Promise((r) => setTimeout(r, 350));
    setStatus(to);
    setPending(null);
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
            disabled={a.to === status}
            loading={pending === a.to}
            onClick={() => change(a.to)}
          >
            {a.label}
          </Button>
        ))}
      </div>
      <p className="text-xs text-text-subtle">
        ⚠️ mock 동작 — 백엔드 연동 시 변경이 감사 로그에 기록됩니다.
      </p>
    </div>
  );
}
