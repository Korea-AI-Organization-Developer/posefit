import { NextResponse, type NextRequest } from "next/server";

import { ADMIN_ACCESS_COOKIE } from "@/lib/auth/cookies";

/*
 * 관리자 인증 게이트 (구 middleware — Next 16에서 proxy로 개명).
 * /login 외 모든 경로는 admin_accessToken 쿠키가 있어야 통과, 없으면 /login으로.
 *
 * ⚠️ 백엔드 /admin/auth/refresh 연동 시, 소비자 앱 proxy.ts 처럼
 *    access 만료(쿠키 폐기) → refresh 토큰으로 갱신하는 분기를 추가한다.
 *    현재 mock 단계에서는 access 쿠키 존재만 검사한다.
 */
export async function proxy(request: NextRequest) {
  if (request.cookies.has(ADMIN_ACCESS_COOKIE)) {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  return NextResponse.redirect(url);
}

export const config = {
  // /login·정적 자산을 제외한 모든 경로 보호
  matcher: ["/((?!login|_next/static|_next/image|favicon.ico).*)"],
};
