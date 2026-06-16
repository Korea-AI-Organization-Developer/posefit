import { redirect } from "next/navigation";

import { getMe } from "@/lib/api/users";
import type { RegistrationStep, User } from "@/lib/api/types";
import { STEP_DEST } from "./steps";

/*
 * 온보딩 단계 가드 — 현재 registrationStep이 기대 단계와 다르면 올바른 위치로 보낸다.
 *   - 이미 지난 단계 → 다음(또는 대시보드)
 *   - 아직 못 온 단계 → 앞 단계
 * 새로고침·뒤로가기·직접 URL 진입 모두 안전. 인증 자체가 깨지면 랜딩으로.
 */
export async function requireStep(step: RegistrationStep): Promise<User> {
  let me: User;
  try {
    me = await getMe();
  } catch {
    redirect("/");
  }
  if (me.registrationStep !== step) {
    redirect(STEP_DEST[me.registrationStep]);
  }
  return me;
}
