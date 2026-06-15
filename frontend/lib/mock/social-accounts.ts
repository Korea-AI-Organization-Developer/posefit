/*
 * 소셜 연동 목업 — docs/openapi.yaml SocialAccount 기준. 백엔드 미구현.
 *   getSocialAccounts() → GET /api/v1/users/me/social-accounts
 *   linkSocialAccount() → POST /api/v1/users/me/social-accounts/{provider}:link
 * API 준비 후 lib/api/social-accounts.ts 로 교체 (시그니처 동일).
 *
 * 추가/해제는 백엔드가 없어 영속되지 않는다 — 클라이언트 state 로만 시뮬레이션한다.
 */

export interface SocialAccount {
  provider: "google";
  providerEmail: string | null;
  linkedAt: string; // date-time
}

const accounts: SocialAccount[] = [
  {
    provider: "google",
    providerEmail: "user@gmail.com",
    linkedAt: "2026-02-14T03:21:00+09:00",
  },
];

/* 백업용 두 번째 Google 계정 — "추가 연동" 시뮬레이션 결과 */
const secondaryAccount: SocialAccount = {
  provider: "google",
  providerEmail: "user.backup@gmail.com",
  linkedAt: "2026-06-15T10:00:00+09:00",
};

export async function getSocialAccounts(): Promise<SocialAccount[]> {
  return accounts;
}

/** 추가 연동 시뮬레이션 — 실제로는 OAuth code 교환이 일어난다(openapi link). */
export async function linkSocialAccount(): Promise<SocialAccount> {
  return { ...secondaryAccount, linkedAt: new Date().toISOString() };
}
