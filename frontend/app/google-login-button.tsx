"use client";

import { useState } from "react";
import { Button, type ButtonSize } from "@/components/ui";

const GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth";

/* 구글 브랜드 마크 — 브랜드 컬러는 예외적으로 유지(우리 UI 토큰 대상 아님) */
function GoogleMark() {
  return (
    <svg viewBox="0 0 18 18" aria-hidden>
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92A8.78 8.78 0 0 0 17.64 9.2z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.85.86-3.04.86-2.34 0-4.32-1.58-5.03-3.71H.96v2.33A9 9 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.97 10.71a5.41 5.41 0 0 1 0-3.42V4.96H.96a9 9 0 0 0 0 8.08l3.01-2.33z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.59A9 9 0 0 0 .96 4.96L3.97 7.3C4.68 5.17 6.66 3.58 9 3.58z"
      />
    </svg>
  );
}

export function GoogleLoginButton({
  size = "lg",
  hint = true,
}: {
  size?: ButtonSize;
  /** 미설정 안내 문구 노출 — 네비처럼 좁은 자리에선 false */
  hint?: boolean;
}) {
  const [loading, setLoading] = useState(false);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  function start() {
    if (!clientId) return;
    setLoading(true);

    // CSRF state — httpOnly가 아니어도 됨(콜백이 같은 값과 대조만 한다)
    const state = crypto.randomUUID();
    document.cookie = `oauth_state=${state}; path=/; max-age=600; samesite=lax`;

    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: `${window.location.origin}/auth/callback`,
      response_type: "code",
      scope: "openid email profile",
      state,
      prompt: "select_account",
    });
    window.location.href = `${GOOGLE_AUTH_URL}?${params.toString()}`;
  }

  if (!clientId) {
    const disabledButton = (
      <Button variant="secondary" size={size} disabled leftIcon={<GoogleMark />}>
        구글로 시작하기
      </Button>
    );
    if (!hint) return disabledButton;
    return (
      <div className="space-y-2 text-center">
        {disabledButton}
        <p className="text-xs text-text-subtle">
          NEXT_PUBLIC_GOOGLE_CLIENT_ID 미설정 — frontend/.env 를 확인하세요
        </p>
      </div>
    );
  }

  return (
    <Button
      variant="secondary"
      size={size}
      loading={loading}
      onClick={start}
      leftIcon={<GoogleMark />}
    >
      구글로 시작하기
    </Button>
  );
}
