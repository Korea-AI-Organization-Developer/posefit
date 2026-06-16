import { apiFetch } from "./server";
import type {
  FaceDetectResponse,
  FaceRegistrationResponse,
  User,
  UserDetail,
  UserDetailUpsertRequest,
} from "./types";

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

/* POST /users/me/face/detect — 웹캠 프레임에 얼굴 1개 있는지 확인 */
export async function detectFace(body: FormData): Promise<FaceDetectResponse> {
  return apiFetch("/users/me/face/detect", { method: "POST", body });
}

/*
 * POST|PUT /users/me/face — multipart(field "image"). 백엔드는 현재 스텁(stub-v0)이지만
 * 정상 201을 반환하고 registrationStep을 complete로 만든다.
 * replace=false면 이미 등록 시 409, true면 교체(PUT).
 */
export async function registerFace(
  body: FormData,
  { replace }: { replace: boolean },
): Promise<FaceRegistrationResponse> {
  return apiFetch("/users/me/face", { method: replace ? "PUT" : "POST", body });
}

/* DELETE /users/me/face — 얼굴 데이터만 삭제(계정 유지). 이후 운동 시작은 422 FACE_REQUIRED */
export async function deleteFace(): Promise<void> {
  return apiFetch("/users/me/face", { method: "DELETE" });
}

/* DELETE /users/me — 회원 탈퇴(soft). status=withdrawn, 영구 삭제는 배치 */
export async function withdraw(): Promise<void> {
  return apiFetch("/users/me", { method: "DELETE" });
}
