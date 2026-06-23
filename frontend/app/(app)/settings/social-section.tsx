"use client";

import { useEffect, useState, useTransition } from "react";
import { Plus, Unlink, UserRound } from "lucide-react";
import { Button } from "@/components/ui";
import type { SocialAccount } from "@/lib/api/social-accounts";
import { unlinkSocialAccountAction } from "./actions";

const GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";
const MAX_ACCOUNTS = 2;

/* SET-06 — 소셜 연동. 마지막 1개는 해제 불가(LAST_SOCIAL_ACCOUNT). */
export function SocialSection({
  initial,
  linked,
  linkError,
}: {
  initial: SocialAccount[];
  linked?: boolean;
  linkError?: string;
}) {
  const [accounts, setAccounts] = useState(initial);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(
    linkError === "link" ? "계정 연결에 실패했어요. 이미 연결된 계정이거나 다른 문제가 발생했어요."
    : linkError === "server" ? "서버 오류가 발생했어요. 잠시 후 다시 시도해 주세요."
    : linkError ? "계정 연결에 실패했어요."
    : null,
  );
  const [success, setSuccess] = useState(linked ?? false);

  useEffect(() => {
    if (linked) {
      // URL에서 쿼리 파라미터 제거 (새로고침해도 토스트 안 뜨게)
      window.history.replaceState({}, "", "/settings");
    }
  }, [linked]);

  const atMax = accounts.length >= MAX_ACCOUNTS;
  const isLastOne = accounts.length <= 1;

  function link() {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) return;

    const state = crypto.randomUUID();
    document.cookie = `oauth_state=${state}; path=/; max-age=600; samesite=lax`;

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: `${window.location.origin}/auth/link-callback`,
      response_type: "code",
      scope: "openid email profile",
      state,
      prompt: "select_account",
    });
    window.location.href = `${GOOGLE_AUTH_URL}?${params.toString()}`;
  }

  function unlink(acc: SocialAccount) {
    if (isLastOne) return;
    setError(null);
    setSuccess(false);
    startTransition(async () => {
      const result = await unlinkSocialAccountAction(acc.provider, acc.providerUid);
      if (result.error) {
        setError(result.error);
      } else {
        setAccounts((prev) =>
          prev.filter(
            (a) => !(a.provider === acc.provider && a.providerUid === acc.providerUid),
          ),
        );
      }
    });
  }

  return (
    <div className="space-y-4">
      <ul className="divide-y divide-border overflow-hidden rounded-md border border-border">
        {accounts.map((acc) => (
          <li
            key={`${acc.provider}-${acc.providerUid}`}
            className="flex items-center justify-between gap-3 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-sm bg-surface-muted text-text-subtle [&_svg]:size-4">
                <UserRound aria-hidden />
              </span>
              <div>
                <p className="text-sm font-medium capitalize">{acc.provider}</p>
                <p className="text-xs text-text-subtle">
                  {acc.providerEmail ?? "이메일 비공개"}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Unlink />}
              disabled={isLastOne || pending}
              onClick={() => unlink(acc)}
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

      {error && <p className="text-xs text-red-500">{error}</p>}
      {success && !error && (
        <p className="text-xs text-green-600">Google 계정을 연결했어요.</p>
      )}

      {!atMax && (
        <Button
          variant="secondary"
          size="sm"
          leftIcon={<Plus />}
          disabled={pending}
          onClick={link}
        >
          다른 Google 계정 연동
        </Button>
      )}
    </div>
  );
}
