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

// ─── 이번에 추가한 운동(exercise) 관련 타입들 ───────────────────────────────
// 백엔드 schemas/exercise.py 와 "같은 모양". 둘 다 openapi.yaml 명세를 보고 만들어 일치한다.

// ExerciseType: 운동 종류. 이 두 글자 외의 값은 타입 에러로 막힌다(static=정적, dynamic=동적).
export type ExerciseType = "static" | "dynamic";

// ExerciseSummary: 운동 한 개의 요약. 목록 카드 하나에 들어가는 데이터 모양.
// (interface = "객체가 이런 필드들을 가진다"는 타입 정의. 백엔드가 보내는 JSON과 1:1로 맞춘다.)
export interface ExerciseSummary {
  id: number;                       // 운동 고유 번호.
  nameKo: string;                   // 한글 이름 (예: "런지").
  nameEn: string | null;            // 영문 이름. 없으면 null (| null = "또는 null").
  exerciseType: ExerciseType;       // static | dynamic.
  isActive: boolean;                // 노출 여부.
  userAvgScore: number | null;      // 이 사용자의 평균 점수. 안 했으면 null → 화면에 "기록 없음".
}

// ExerciseListResponse: 목록 API의 전체 응답. items 배열 안에 위 요약들이 들어온다.
export interface ExerciseListResponse {
  items: ExerciseSummary[];         // [] = 배열. ExerciseSummary들의 목록.
}
