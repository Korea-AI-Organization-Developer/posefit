import { cookies } from "next/headers";
import { NextResponse, type NextRequest } from "next/server";

import { linkSocialAccount } from "@/lib/api/social-accounts";
import { ApiError } from "@/lib/api/server";
import { STATE_COOKIE } from "@/lib/auth/cookies";

/*
 * 소셜 계정 연결용 OAuth 콜백. 로그인 콜백(/auth/callback)과 달리 토큰을 심지 않고
 * 기존 로그인 세션에 소셜 계정을 추가(POST /users/me/social-accounts/{provider}:link)한 뒤
 * /settings 으로 리다이렉트한다.
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  const savedState = (await cookies()).get(STATE_COOKIE)?.value;

  const fail = (reason: string) => {
    const res = NextResponse.redirect(new URL(`/settings?error=${reason}`, origin));
    res.cookies.delete(STATE_COOKIE);
    return res;
  };

  if (!code || !state || !savedState || state !== savedState) {
    return fail("state");
  }

  try {
    await linkSocialAccount("google", code, `${origin}/auth/link-callback`);
  } catch (e) {
    return fail(e instanceof ApiError ? "link" : "server");
  }

  const res = NextResponse.redirect(new URL("/settings?linked=1", origin));
  res.cookies.delete(STATE_COOKIE);
  return res;
}
