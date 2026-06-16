"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import {
  ADMIN_ACCESS_COOKIE,
  adminAccessCookieOptions,
} from "@/lib/auth/cookies";

export interface LoginState {
  error?: string;
}

/*
 * 관리자 로그인 — 현재는 mock.
 * 백엔드 연동 시: POST /admin/auth/login 호출 →
 *   응답 accessToken/refreshToken 을 각각 admin_accessToken/admin_refreshToken 쿠키로 심는다.
 */
export async function loginAction(
  _prev: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { error: "이메일과 비밀번호를 입력하세요." };
  }

  // mock: 데모 계정만 통과 (실서비스에서는 백엔드가 검증).
  if (email !== "admin@posefit.dev") {
    return { error: "이메일 또는 비밀번호가 올바르지 않습니다." };
  }

  const store = await cookies();
  store.set(
    ADMIN_ACCESS_COOKIE,
    "mock-admin-token",
    adminAccessCookieOptions(60 * 60 * 8),
  );
  redirect("/");
}

export async function logoutAction(): Promise<void> {
  const store = await cookies();
  store.delete(ADMIN_ACCESS_COOKIE);
  redirect("/login");
}
