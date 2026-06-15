"use client";

import { useState, useTransition } from "react";
import { Checkbox } from "@/components/ui";
import { updateMarketingAction } from "./actions";

/* SET-03 — 마케팅 수신 동의. 토글은 append-only 새 동의 레코드를 만든다(actions 주석 참고). */
export function MarketingToggle({ initialAgreed }: { initialAgreed: boolean }) {
  const [agreed, setAgreed] = useState(initialAgreed);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function toggle(next: boolean) {
    setError(null);
    setAgreed(next); // 낙관적 반영
    startTransition(async () => {
      const res = await updateMarketingAction(next);
      if (res?.error) {
        setAgreed(!next); // 실패 시 롤백
        setError(res.error);
      }
    });
  }

  return (
    <div className="space-y-2">
      <Checkbox
        label="마케팅 정보 수신 (이벤트·신규 기능 안내)"
        checked={agreed}
        disabled={pending}
        onChange={(e) => toggle(e.target.checked)}
      />
      <p className="text-xs text-text-subtle">
        선택 항목이에요. 변경할 때마다 새 동의 이력이 기록돼요.
      </p>
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  );
}
