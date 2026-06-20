"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { API_BASE, apiFetch } from "@/lib/api/server";
import {
  ADMIN_ACCESS_COOKIE,
  ADMIN_REFRESH_COOKIE,
  adminAccessCookieOptions,
  adminRefreshCookieOptions,
} from "@/lib/auth/cookies";

export interface LoginState {
  error?: string;
}

export async function loginAction(
  _prev: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return { error: "이메일과 비밀번호를 입력하세요." };
  }

  let data: {
    accessToken: string;
    refreshToken: string;
    accessTokenExpiresIn: number;
  };

  try {
    const res = await fetch(`${API_BASE}/admin/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    });

    if (res.status === 401) {
      return { error: "이메일 또는 비밀번호가 올바르지 않습니다." };
    }
    if (!res.ok) {
      return { error: "로그인 중 오류가 발생했어요. 잠시 후 다시 시도해주세요." };
    }

    data = await res.json();
  } catch {
    return { error: "서버에 연결할 수 없어요. 잠시 후 다시 시도해주세요." };
  }

  const store = await cookies();
  store.set(
    ADMIN_ACCESS_COOKIE,
    data.accessToken,
    adminAccessCookieOptions(data.accessTokenExpiresIn),
  );
  store.set(ADMIN_REFRESH_COOKIE, data.refreshToken, adminRefreshCookieOptions());
  redirect("/");
}

export async function logoutAction(): Promise<void> {
  try {
    await apiFetch("/admin/auth/logout", { method: "POST" });
  } catch {
    // 토큰 만료 등으로 실패해도 쿠키는 삭제
  }

  const store = await cookies();
  store.delete(ADMIN_ACCESS_COOKIE);
  store.delete(ADMIN_REFRESH_COOKIE);
  redirect("/login");
}
