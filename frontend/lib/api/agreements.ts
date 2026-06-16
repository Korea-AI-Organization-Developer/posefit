import { ApiError, apiFetch } from "./server";
import type { Agreement, AgreementCreateRequest } from "./types";

/* POST /users/me/agreements — append-only. 필수 3종 미동의 시 422 */
export async function submitAgreements(
  input: AgreementCreateRequest,
): Promise<Agreement> {
  return apiFetch("/users/me/agreements", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/* GET /users/me/agreements — 최신 동의 1건. 이력 없으면 404 → null */
export async function getLatestAgreement(): Promise<Agreement | null> {
  try {
    return await apiFetch<Agreement>("/users/me/agreements");
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
