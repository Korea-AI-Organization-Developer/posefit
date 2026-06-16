/*
 * 백엔드 API 타입 — docs/openapi.yaml 스키마를 그대로 옮긴 것(camelCase).
 * 인증/유저 도메인은 실제 구현돼 있으므로 lib/api/* 가 이 타입을 사용한다.
 */

export type RegistrationStep =
  | "agreements_required"
  | "detail_required"
  | "face_required"
  | "complete";

export type Gender = "M" | "F" | "U";

export interface UserDetail {
  /** cm. 미입력 시 null */
  height: number | null;
  /** kg. 미입력 시 null */
  weight: number | null;
  birthdate: string; // date
  gender: Gender;
}

export interface User {
  id: number;
  /** [Derived] 대표 social_accounts.provider_email. 없으면 null */
  email: string | null;
  /** [Derived] 대표 social_accounts.provider_avatar_url. 없으면 null */
  avatarUrl: string | null;
  nickname: string;
  role: "user" | "admin";
  status: "active" | "withdrawn";
  registrationStep: RegistrationStep;
  detail: UserDetail | null;
  createdAt: string; // date-time
}

export interface AuthSocialCallbackRequest {
  code: string;
  redirectUri: string;
  state?: string | null;
}

export interface AuthSocialCallbackResponse {
  accessToken: string;
  refreshToken: string;
  /** access 만료까지 초 */
  accessTokenExpiresIn: number;
  isNewUser: boolean;
  user: User;
}

export interface AuthRefreshResponse {
  accessToken: string;
  accessTokenExpiresIn: number;
}

export interface UserDetailUpsertRequest {
  /** cm, 50~250. 미입력 시 null */
  height: number | null;
  /** kg, 20~300. 미입력 시 null */
  weight: number | null;
  birthdate: string; // date, 미래 불가
  gender: Gender;
}

export interface Agreement {
  id: number;
  tosAgreed: boolean;
  privacyAgreed: boolean;
  biometricAgreed: boolean;
  marketingAgreed: boolean;
  agreedAt: string; // date-time
}

export interface AgreementCreateRequest {
  tosAgreed: boolean;
  privacyAgreed: boolean;
  biometricAgreed: boolean;
  marketingAgreed?: boolean;
}

export interface FaceDetectResponse {
  detected: boolean;
}

export interface FaceRegistrationResponse {
  registeredAt: string; // date-time
  modelVersion: string;
}
