import { NextResponse } from "next/server";

import { logout as backendLogout } from "@/lib/api/auth";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/cookies";

/* 로그아웃 — 백엔드 token_version +1(이전 refresh 무효화) 후 인증 쿠키 제거 */
export async function POST() {
  try {
    await backendLogout();
  } catch {
    // 토큰이 이미 만료/무효여도 클라이언트 쿠키는 비운다
  }
  const res = NextResponse.json({ ok: true });
  res.cookies.delete(ACCESS_COOKIE);
  res.cookies.delete(REFRESH_COOKIE);
  return res;
}
