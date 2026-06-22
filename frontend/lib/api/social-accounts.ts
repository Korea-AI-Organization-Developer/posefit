import { apiFetch } from "./server";

export interface SocialAccount {
  provider: string;
  providerUid: string;
  providerEmail: string | null;
  linkedAt: string;
}

export async function getSocialAccounts(): Promise<SocialAccount[]> {
  return apiFetch<SocialAccount[]>("/users/me/social-accounts");
}

export async function linkSocialAccount(
  provider: string,
  code: string,
  redirectUri: string,
): Promise<SocialAccount> {
  return apiFetch<SocialAccount>(`/users/me/social-accounts/${provider}:link`, {
    method: "POST",
    body: JSON.stringify({ code, redirectUri }),
  });
}

export async function unlinkSocialAccount(
  provider: string,
  providerUid: string,
): Promise<void> {
  return apiFetch(`/users/me/social-accounts/${provider}/${providerUid}`, {
    method: "DELETE",
  });
}
