"use server";

/* 얼굴 등록은 온보딩에서 제거됨 — 운동 시작 시 face-gate 에서 처리한다. */
export async function detectFaceAction(
  _formData: FormData,
): Promise<{ detected: boolean }> {
  return { detected: false };
}

export async function registerFaceAction(
  _formData: FormData,
): Promise<{ error?: string }> {
  return { error: "이 페이지는 더 이상 사용되지 않아요." };
}
