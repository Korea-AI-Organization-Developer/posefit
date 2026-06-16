"use server";

import { redirect } from "next/navigation";

import { submitAgreements } from "@/lib/api/agreements";
import { ApiError } from "@/lib/api/server";
import type { AgreementCreateRequest } from "@/lib/api/types";

/* 약관 제출 → 성공 시 다음 단계로 리다이렉트, 실패 시 인라인 에러 문자열 반환 */
export async function submitAgreementsAction(
  input: AgreementCreateRequest,
): Promise<{ error?: string }> {
  try {
    await submitAgreements(input);
  } catch (e) {
    if (e instanceof ApiError && e.status === 422) {
      return { error: "필수 약관에 모두 동의해 주세요." };
    }
    return { error: "잠시 후 다시 시도해 주세요." };
  }
  redirect("/onboarding/profile");
}
