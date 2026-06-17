import { apiFetch } from "./server";
import type { User, UserDetail, UserDetailUpsertRequest } from "./types";

/* GET /users/me — 본인 프로필 (email·avatarUrl·registrationStep은 백엔드에서 derived) */
export async function getMe(): Promise<User> {
  return apiFetch("/users/me");
}

/* PATCH /users/me — 닉네임 변경 */
export async function updateNickname(nickname: string): Promise<User> {
  return apiFetch("/users/me", {
    method: "PATCH",
    body: JSON.stringify({ nickname }),
  });
}

/* PUT /users/me/detail — 신체 정보 upsert (전체 교체) */
export async function upsertDetail(
  input: UserDetailUpsertRequest,
): Promise<UserDetail> {
  return apiFetch("/users/me/detail", {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

/* DELETE /users/me — 회원 탈퇴(soft). status=withdrawn, 영구 삭제는 배치 */
export async function withdraw(): Promise<void> {
  return apiFetch("/users/me", { method: "DELETE" });
}
