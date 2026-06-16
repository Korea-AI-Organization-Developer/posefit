/*
 * 인증 쿠키 이름·옵션 — Route Handler(cookies()·response.cookies)와 proxy(response.cookies)
 * 양쪽에서 공유한다. next/headers를 import하지 않는 순수 모듈이라 proxy에서도 안전.
 */

export const ACCESS_COOKIE = "accessToken";
export const REFRESH_COOKIE = "refreshToken";
/** OAuth CSRF state (httpOnly 아님 — 로그인 버튼이 document.cookie로 심고 콜백이 검증) */
export const STATE_COOKIE = "oauth_state";

/** refresh 토큰 수명(초) — 백엔드 14일과 맞춘다 */
export const REFRESH_MAX_AGE = 60 * 60 * 24 * 14;

const isProd = process.env.NODE_ENV === "production";

interface CookieOptions {
  httpOnly: boolean;
  sameSite: "lax";
  secure: boolean;
  path: string;
  maxAge: number;
}

/** access 쿠키 — maxAge를 토큰 만료(초)와 맞춰, 만료 시 브라우저가 자동 폐기 → proxy가 refresh 트리거 */
export function accessCookieOptions(maxAge: number): CookieOptions {
  return { httpOnly: true, sameSite: "lax", secure: isProd, path: "/", maxAge };
}

export function refreshCookieOptions(): CookieOptions {
  return {
    httpOnly: true,
    sameSite: "lax",
    secure: isProd,
    path: "/",
    maxAge: REFRESH_MAX_AGE,
  };
}
