"use server";

import { redirect } from "next/navigation";

import { apiErrorMessage } from "@/lib/api/server";
import { detectFace, registerFace } from "@/lib/api/users";

/* 웹캠 프레임에 얼굴 1개 있는지 확인 — 임베딩 추출 없이 빠르게 */
export async function detectFaceAction(
  formData: FormData,
): Promise<{ detected: boolean }> {
  try {
    const res = await detectFace(formData);
    return { detected: res.detected };
  } catch {
    return { detected: false };
  }
}

/* 얼굴 등록 — multipart(field "image")로 백엔드 전송. 성공 시 대시보드로. */
export async function registerFaceAction(
  formData: FormData,
): Promise<{ error?: string }> {
  const image = formData.get("image");
  if (!(image instanceof File) || image.size === 0) {
    return { error: "촬영된 이미지가 없어요." };
  }
  try {
    await registerFace(formData, { replace: false });
  } catch (e) {
    return {
      error: apiErrorMessage(e, "얼굴 등록에 실패했어요. 다시 시도해 주세요."),
    };
  }
  redirect("/dashboard");
}
