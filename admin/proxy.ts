import { NextResponse, type NextRequest } from "next/server";

import {
  ADMIN_ACCESS_COOKIE,
  ADMIN_REFRESH_COOKIE,
  adminAccessCookieOptions,
} from "@/lib/auth/cookies";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function proxy(request: NextRequest) {
  // access token 있으면 통과
  if (request.cookies.has(ADMIN_ACCESS_COOKIE)) {
    return NextResponse.next();
  }

  // access 만료 → refresh token으로 갱신 시도
  const refreshToken = request.cookies.get(ADMIN_REFRESH_COOKIE)?.value;
  if (refreshToken) {
    try {
      const res = await fetch(`${API_BASE}/admin/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken }),
        cache: "no-store",
      });

      if (res.ok) {
        const { accessToken, accessTokenExpiresIn } = await res.json();
        const response = NextResponse.next();
        response.cookies.set(
          ADMIN_ACCESS_COOKIE,
          accessToken,
          adminAccessCookieOptions(accessTokenExpiresIn),
        );
        return response;
      }
    } catch {
      // 갱신 실패 → 로그인으로
    }
  }

  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/((?!login|_next/static|_next/image|favicon.ico).*)"],
};
