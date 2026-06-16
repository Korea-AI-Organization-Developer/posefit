"use client";

import { useState, useTransition } from "react";
import { Plus, Unlink, UserRound } from "lucide-react";
import { Button } from "@/components/ui";
import {
  linkSocialAccount,
  type SocialAccount,
} from "@/lib/mock/social-accounts";

const MAX_ACCOUNTS = 2;

/* SET-06 — 소셜 연동(목업). 마지막 1개는 해제 불가(openapi LAST_SOCIAL_ACCOUNT). */
export function SocialSection({ initial }: { initial: SocialAccount[] }) {
  const [accounts, setAccounts] = useState(initial);
  const [pending, startTransition] = useTransition();

  const atMax = accounts.length >= MAX_ACCOUNTS;
  const isLastOne = accounts.length <= 1;

  function link() {
    startTransition(async () => {
      const added = await linkSocialAccount();
      setAccounts((prev) => [...prev, added]);
    });
  }

  function unlink(index: number) {
    // 마지막 계정은 보호 — 실제로는 DELETE .../{provider} 호출
    if (accounts.length <= 1) return;
    setAccounts((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <div className="space-y-4">
      <ul className="divide-y divide-border overflow-hidden rounded-md border border-border">
        {accounts.map((acc, i) => (
          <li
            key={`${acc.providerEmail}-${i}`}
            className="flex items-center justify-between gap-3 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-sm bg-surface-muted text-text-subtle [&_svg]:size-4">
                <UserRound aria-hidden />
              </span>
              <div>
                <p className="text-sm font-medium">Google</p>
                <p className="text-xs text-text-subtle">
                  {acc.providerEmail ?? "이메일 비공개"}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Unlink />}
              disabled={isLastOne}
              onClick={() => unlink(i)}
            >
              해제
            </Button>
          </li>
        ))}
      </ul>

      {isLastOne && (
        <p className="text-xs text-text-subtle">
          마지막 계정은 해제할 수 없어요. 계정을 정리하려면 회원 탈퇴를 이용하세요.
        </p>
      )}

      <Button
        variant="secondary"
        size="sm"
        leftIcon={<Plus />}
        disabled={atMax || pending}
        loading={pending}
        onClick={link}
      >
        다른 Google 계정 연동
      </Button>
    </div>
  );
}
