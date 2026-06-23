/*
 * 관리자 인증 쿠키 — 소비자 앱과 별도 도메인이라 이름 충돌은 없지만,
 * 명시적으로 admin_ 프리픽스를 붙여 구분한다.
 * next/headers를 import하지 않는 순수 모듈이라 proxy에서도 안전.
 *
 * ⚠️ 현재 백엔드 /admin/* 엔드포인트는 미구현(팀 작업 예정)이라,
 *    아래 access 쿠키는 mock 세션 토큰을 담는다. 백엔드 연동 시
 *    refresh 토큰까지 실제 JWT로 교체한다(REFRESH 패턴은 소비자 앱과 동일).
 */

export const ADMIN_ACCESS_COOKIE = "admin_accessToken";
export const ADMIN_REFRESH_COOKIE = "admin_refreshToken";

/** refresh 토큰 수명(초) — 백엔드 14일과 맞춘다 */
export const ADMIN_REFRESH_MAX_AGE = 60 * 60 * 24 * 14;

// secure 쿠키 여부 — TLS(HTTPS) 환경에서만 true.
// HTTP(비TLS)로 포트 접근하는 배포에서는 COOKIE_SECURE=false 로 두어야 로그인 쿠키가 동작한다.
// 미설정 시 NODE_ENV 기준(개발=false, 운영=true).
const secureCookie =
  process.env.COOKIE_SECURE !== undefined
    ? process.env.COOKIE_SECURE === "true"
    : process.env.NODE_ENV === "production";

interface CookieOptions {
  httpOnly: boolean;
  sameSite: "lax";
  secure: boolean;
  path: string;
  maxAge: number;
}

export function adminAccessCookieOptions(maxAge: number): CookieOptions {
  return { httpOnly: true, sameSite: "lax", secure: secureCookie, path: "/", maxAge };
}

export function adminRefreshCookieOptions(): CookieOptions {
  return {
    httpOnly: true,
    sameSite: "lax",
    secure: secureCookie,
    path: "/",
    maxAge: ADMIN_REFRESH_MAX_AGE,
  };
}
