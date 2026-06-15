import { NextResponse, type NextRequest } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  accessCookieOptions,
} from "@/lib/auth/cookies";

/*
 * 인증 게이트(구 middleware — Next 16에서 proxy로 개명).
 * 보호 경로 접근 시:
 *   - access 쿠키 있음 → 통과
 *   - access 없고 refresh 있음 → /auth/refresh로 갱신, 새 access 쿠키 심고 같은 URL 재요청
 *   - 둘 다 없음/갱신 실패 → 랜딩(/)으로
 * access 쿠키 maxAge가 토큰 만료와 같아 만료 시 자동 폐기 → 여기서 자연히 refresh가 돈다.
 */
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function proxy(request: NextRequest) {
  if (request.cookies.has(ACCESS_COOKIE)) {
    return NextResponse.next();
  }

  const refresh = request.cookies.get(REFRESH_COOKIE)?.value;
  if (refresh) {
    try {
      const r = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken: refresh }),
      });
      if (r.ok) {
        const data = (await r.json()) as {
          accessToken: string;
          accessTokenExpiresIn: number;
        };
        // Set-Cookie는 redirect를 따라가기 전에 적용되므로, 재요청 시 RSC가 새 토큰을 본다
        const res = NextResponse.redirect(request.url);
        res.cookies.set(
          ACCESS_COOKIE,
          data.accessToken,
          accessCookieOptions(data.accessTokenExpiresIn),
        );
        return res;
      }
    } catch {
      // 백엔드 미응답 → 아래에서 랜딩으로
    }
  }

  const url = request.nextUrl.clone();
  url.pathname = "/";
  url.search = "";
  return NextResponse.redirect(url);
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/reports/:path*",
    "/settings/:path*",
    "/workout/:path*",
    "/onboarding/:path*",
  ],
};
