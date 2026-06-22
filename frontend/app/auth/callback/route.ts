import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { socialLoginCallback } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/server";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  STATE_COOKIE,
  accessCookieOptions,
  refreshCookieOptions,
} from "@/lib/auth/cookies";
import { STEP_DEST } from "@/lib/auth/steps";

/*
 * 구글 OAuth redirect 착지점. code를 백엔드에 넘겨 토큰을 받아 httpOnly 쿠키로 심고,
 * registrationStep에 따라 온보딩 단계 또는 대시보드로 리다이렉트한다.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  // 리버스 프록시(Cloudflare Tunnel 등) 뒤에서는 x-forwarded-* 헤더로 실제 origin 을 복원한다.
  const fwdProto = request.headers.get("x-forwarded-proto") ?? request.nextUrl.protocol.replace(":", "");
  const fwdHost = request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? request.nextUrl.host;
  const origin = `${fwdProto}://${fwdHost}`;
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  const savedState = (await cookies()).get(STATE_COOKIE)?.value;

  const fail = (reason: string) => {
    const res = NextResponse.redirect(new URL(`/?error=${reason}`, origin));
    res.cookies.delete(STATE_COOKIE);
    return res;
  };

  // CSRF: 콜백의 state가 로그인 시작 때 심은 값과 일치해야 한다
  if (!code || !state || !savedState || state !== savedState) {
    return fail("state");
  }

  let result;
  try {
    result = await socialLoginCallback("google", {
      code,
      redirectUri: `${origin}/auth/callback`,
      state,
    });
  } catch (e) {
    return fail(e instanceof ApiError ? "login" : "server");
  }

  const dest = STEP_DEST[result.user.registrationStep] ?? "/dashboard";
  const res = NextResponse.redirect(new URL(dest, origin));
  res.cookies.delete(STATE_COOKIE);
  res.cookies.set(
    ACCESS_COOKIE,
    result.accessToken,
    accessCookieOptions(result.accessTokenExpiresIn),
  );
  res.cookies.set(
    REFRESH_COOKIE,
    result.refreshToken,
    refreshCookieOptions(),
  );
  return res;
}
