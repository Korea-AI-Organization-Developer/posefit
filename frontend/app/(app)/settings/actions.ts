"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { getLatestAgreement, submitAgreements } from "@/lib/api/agreements";
import { apiErrorMessage } from "@/lib/api/server";
import { unlinkSocialAccount } from "@/lib/api/social-accounts";
import { updateNickname, upsertDetail, withdraw } from "@/lib/api/users";
import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth/cookies";
import type { ProfileFormValues } from "@/components/forms/profile-form";

/* SET-01·02 — 닉네임(PATCH /users/me) + 신체정보(PUT /users/me/detail) 동시 저장 */
export async function saveProfileAction(
  values: ProfileFormValues,
): Promise<{ error?: string }> {
  try {
    await updateNickname(values.nickname);
    await upsertDetail({
      birthdate: values.birthdate,
      gender: values.gender,
      height: values.height,
      weight: values.weight,
    });
  } catch (e) {
    return { error: apiErrorMessage(e, "입력값을 확인해 주세요.") };
  }
  revalidatePath("/settings");
  return {};
}

/*
 * SET-03 — 마케팅 수신 동의 변경.
 * agreements 는 append-only(이력 보존) — 토글은 기존 필수 동의를 그대로 들고
 * marketing 만 바꾼 '새 레코드'를 POST 한다. 직전 레코드는 이력으로 남는다.
 */
export async function updateMarketingAction(
  next: boolean,
): Promise<{ error?: string }> {
  try {
    const current = await getLatestAgreement();
    await submitAgreements({
      // 가입 완료 사용자는 필수 3종이 이미 true — 직전 값을 그대로 승계
      tosAgreed: current?.tosAgreed ?? true,
      privacyAgreed: current?.privacyAgreed ?? true,
      biometricAgreed: current?.biometricAgreed ?? true,
      marketingAgreed: next,
    });
  } catch (e) {
    return { error: apiErrorMessage(e, "동의 상태를 변경하지 못했어요.") };
  }
  revalidatePath("/settings");
  return {};
}

/* SET-06 — 소셜 계정 해제 */
export async function unlinkSocialAccountAction(
  provider: string,
  providerUid: string,
): Promise<{ error?: string }> {
  try {
    await unlinkSocialAccount(provider, providerUid);
  } catch (e) {
    return { error: apiErrorMessage(e, "계정 해제에 실패했어요.") };
  }
  revalidatePath("/settings");
  return {};
}

/* SET-08 — 회원 탈퇴(soft). 성공 시 인증 쿠키 제거 후 랜딩으로. */
export async function withdrawAction(): Promise<{ error?: string }> {
  try {
    await withdraw();
  } catch (e) {
    return { error: apiErrorMessage(e, "탈퇴 처리에 실패했어요.") };
  }
  const jar = await cookies();
  jar.delete(ACCESS_COOKIE);
  jar.delete(REFRESH_COOKIE);
  redirect("/");
}
