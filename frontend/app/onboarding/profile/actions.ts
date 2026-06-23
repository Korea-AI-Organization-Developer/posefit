"use server";

import { redirect } from "next/navigation";

import { apiErrorMessage } from "@/lib/api/server";
import { updateNickname, upsertDetail } from "@/lib/api/users";
import type { ProfileFormValues } from "@/components/forms/profile-form";

/* 기본정보 저장 → 닉네임 PATCH + 신체정보 PUT, 성공 시 대시보드로 (가입 완료) */
export async function saveOnboardingProfileAction(
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
  redirect("/dashboard");
}
