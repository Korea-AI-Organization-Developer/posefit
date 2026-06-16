import { apiFetch } from "./server";
import type {
  AuthRefreshResponse,
  AuthSocialCallbackRequest,
  AuthSocialCallbackResponse,
} from "./types";

/* POST /auth/social/{provider}/callback — authorization code 교환 → 토큰+사용자 */
export async function socialLoginCallback(
  provider: string,
  payload: AuthSocialCallbackRequest,
): Promise<AuthSocialCallbackResponse> {
  return apiFetch(`/auth/social/${provider}/callback`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/* POST /auth/refresh — refresh 토큰으로 access 재발급 */
export async function refreshTokens(
  refreshToken: string,
): Promise<AuthRefreshResponse> {
  return apiFetch("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refreshToken }),
  });
}

/* POST /auth/logout — 서버에서 token_version +1 (이전 refresh 전부 무효화) */
export async function logout(): Promise<void> {
  return apiFetch("/auth/logout", { method: "POST" });
}
