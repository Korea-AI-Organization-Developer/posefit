"use client";

import { useActionState } from "react";
import { LockKeyhole } from "lucide-react";

import { Button } from "@/components/ui";
import { loginAction, type LoginState } from "@/lib/auth/actions";

const INITIAL: LoginState = {};

export function LoginForm() {
  const [state, action, pending] = useActionState(loginAction, INITIAL);

  return (
    <form action={action} className="rounded-md border border-border bg-surface p-6 shadow-xs">
      <label className="block">
        <span className="mb-1.5 block text-sm font-medium">이메일</span>
        <input
          name="email"
          type="email"
          autoComplete="username"
          placeholder="이메일"
          className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none transition-colors placeholder:text-text-subtle focus:border-accent focus:ring-2 focus:ring-accent-soft"
        />
      </label>

      <label className="mt-4 block">
        <span className="mb-1.5 block text-sm font-medium">비밀번호</span>
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="비밀번호"
          className="h-10 w-full rounded-sm border border-border bg-surface px-3 text-sm outline-none transition-colors placeholder:text-text-subtle focus:border-accent focus:ring-2 focus:ring-accent-soft"
        />
      </label>

      {state.error && (
        <p className="mt-3 text-sm text-danger">{state.error}</p>
      )}

      <Button
        type="submit"
        loading={pending}
        leftIcon={<LockKeyhole aria-hidden />}
        className="mt-6 w-full"
      >
        로그인
      </Button>

    </form>
  );
}
