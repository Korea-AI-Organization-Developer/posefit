import type { RegistrationStep } from "@/lib/api/types";

/* registrationStep → 보낼 경로. 가입 미완료면 해당 온보딩 단계, 완료면 대시보드. */
export const STEP_DEST: Record<RegistrationStep, string> = {
  agreements_required: "/onboarding/terms",
  detail_required: "/onboarding/profile",
  complete: "/dashboard",
};
