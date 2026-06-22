/*
 * 데모용 mock 시드 — 백엔드 /admin/* 미구현 단계의 화면 검증용.
 * 결정론적(고정 기준일·고정 값)이라 SSR/CSR 결과가 일치한다.
 * 백엔드 연동 시 lib/api/* 호출로 교체하고 이 파일은 제거한다.
 */

import type {
  Admin,
  AdminExercise,
  AdminSessionListItem,
  AdminUserDetail,
  AuditLog,
  LlmModel,
} from "@/lib/api/types";

/** 고정 기준일 — now() 대신 사용해 빌드/렌더 결과를 안정화 */
export const REFERENCE_DATE = "2026-06-16T09:00:00+09:00";

function daysAgoIso(days: number, hour = 12, minute = 0): string {
  const base = new Date(REFERENCE_DATE);
  base.setDate(base.getDate() - days);
  base.setHours(hour, minute, 0, 0);
  return base.toISOString();
}

function dateOnly(days: number): string {
  const base = new Date(REFERENCE_DATE);
  base.setDate(base.getDate() - days);
  return base.toISOString().slice(0, 10);
}

// ─── 현재 로그인 관리자 ──────────────────────────────────────────────────────
export const CURRENT_ADMIN: Admin = {
  id: 1,
  email: "admin@posefit.dev",
  name: "운영자",
  role: "super_admin",
  status: "active",
  lastLoginAt: daysAgoIso(0, 8, 42),
  createdAt: daysAgoIso(120),
};

// ─── 회원 ────────────────────────────────────────────────────────────────────
const NICKNAMES = [
  "김하민", "이서연", "박지후", "최예준", "정도윤", "강민서", "조하은", "윤시우",
  "장지안", "임주원", "한서윤", "오은우", "서지호", "신아윤", "권건우", "황지유",
  "안수아", "송태양", "전하린", "홍라온", "유다온", "고이든", "문서진", "배준서",
];

const STATUS_CYCLE: AdminUserDetail["status"][] = [
  "active", "active", "active", "active", "suspended", "active", "active", "withdrawn",
];

export interface SeedUser extends AdminUserDetail {}

export const USERS: SeedUser[] = NICKNAMES.map((nickname, i) => {
  const id = i + 1;
  const status = STATUS_CYCLE[i % STATUS_CYCLE.length];
  const createdDays = 110 - i * 4;
  const gender = i % 3 === 0 ? "F" : i % 3 === 1 ? "M" : "U";
  return {
    id,
    nickname,
    email: `user${id}@gmail.com`,
    role: "user",
    status,
    createdAt: daysAgoIso(createdDays, 10, (i * 7) % 60),
    withdrawnAt: status === "withdrawn" ? daysAgoIso(createdDays - 30) : null,
    birthdate: `19${85 + (i % 15)}-0${(i % 9) + 1}-1${i % 9}`,
    gender: gender as SeedUser["gender"],
    height: 160 + ((i * 3) % 30),
    weight: 52 + ((i * 2) % 38),
    faceRegistered: status !== "withdrawn",
    marketingAgreed: i % 2 === 0,
    sessionCount: status === "withdrawn" ? 0 : ((i * 5 + 3) % 47) + 1,
  };
});

// ─── 운동 종목 (T-06 확정 4종 + 비활성 1종) ─────────────────────────────────
export const EXERCISES: AdminExercise[] = [
  {
    id: 1,
    nameKo: "런지",
    nameEn: "Lunge",
    description: "한 발을 앞으로 내딛어 무릎을 굽히는 하체 운동.",
    referenceVideoUrl: "https://storage.posefit.dev/ref/lunge.mp4",
    exerciseType: "dynamic",
    isActive: true,
  },
  {
    id: 2,
    nameKo: "플랭크",
    nameEn: "Plank",
    description: "코어를 긴장시켜 자세를 유지하는 정적 운동.",
    referenceVideoUrl: "https://storage.posefit.dev/ref/plank.mp4",
    exerciseType: "static",
    isActive: true,
  },
  {
    id: 3,
    nameKo: "푸쉬업",
    nameEn: "Push-up",
    description: "가슴·삼두를 사용하는 상체 반복 운동.",
    referenceVideoUrl: "https://storage.posefit.dev/ref/pushup.mp4",
    exerciseType: "dynamic",
    isActive: true,
  },
  {
    id: 4,
    nameKo: "오버헤드프레스",
    nameEn: "Overhead Press",
    description: "어깨를 사용해 머리 위로 미는 운동.",
    referenceVideoUrl: "https://storage.posefit.dev/ref/ohp.mp4",
    exerciseType: "dynamic",
    isActive: true,
  },
  {
    id: 5,
    nameKo: "스쿼트(준비중)",
    nameEn: "Squat",
    description: "정답 영상 검수 대기 — 미노출.",
    referenceVideoUrl: null,
    exerciseType: "dynamic",
    isActive: false,
  },
];

// ─── LLM 모델 레지스트리 (gemini 3.1 flash 활성) ────────────────────────────
export const LLM_MODELS: LlmModel[] = [
  {
    id: 1,
    provider: "google",
    modelName: "gemini-3.1-flash",
    displayName: "Gemini 3.1 Flash",
    params: { temperature: 0.4 },
    isActive: true,
    createdAt: daysAgoIso(60),
    updatedAt: daysAgoIso(20),
  },
  {
    id: 2,
    provider: "google",
    modelName: "gemini-3.5-flash",
    displayName: "Gemini 3.5 Flash",
    params: { temperature: 0.4 },
    isActive: false,
    createdAt: daysAgoIso(10),
    updatedAt: daysAgoIso(10),
  },
  {
    id: 3,
    provider: "openai",
    modelName: "gpt-5-mini",
    displayName: "GPT-5 mini",
    params: { temperature: 0.5 },
    isActive: false,
    createdAt: daysAgoIso(8),
    updatedAt: daysAgoIso(8),
  },
];

// ─── 운동 세션 (좌표 내보내기 탐색용) ───────────────────────────────────────
const SESSION_STATUS: AdminSessionListItem["status"][] = [
  "completed", "completed", "completed", "aborted", "in_progress",
];

export const SESSIONS: AdminSessionListItem[] = Array.from(
  { length: 36 },
  (_, i) => {
    const exercise = EXERCISES[i % 4];
    const status = SESSION_STATUS[i % SESSION_STATUS.length];
    const isCompleted = status === "completed";
    const dynamic = exercise.exerciseType === "dynamic";
    return {
      id: 1000 + i,
      exercise: { id: exercise.id, nameKo: exercise.nameKo },
      status,
      startedAt: daysAgoIso(i, 7 + (i % 12), (i * 11) % 60),
      endedAt: status === "in_progress" ? null : daysAgoIso(i, 7 + (i % 12), ((i * 11) % 60) + 3),
      score: isCompleted ? 70 + ((i * 7) % 30) + 0.25 : null,
      repCount: isCompleted && dynamic ? 8 + (i % 12) : null,
      holdSec: isCompleted && !dynamic ? 30 + (i % 40) : null,
      saved: i % 3 === 0,
    };
  },
);

// ─── 감사 로그 ───────────────────────────────────────────────────────────────
const AUDIT_SEED: Array<Omit<AuditLog, "id" | "adminId" | "createdAt" | "ipAddress">> = [
  { action: "activate_llm", targetType: "llm_model", targetId: "1", detail: { provider: "google", modelName: "gemini-3.1-flash" } },
  { action: "export_keypoints", targetType: "session", targetId: "1003", detail: { format: "jsonl", sessionCount: 1 } },
  { action: "update_user_status", targetType: "user", targetId: "5", detail: { from: "active", to: "suspended" } },
  { action: "create_exercise", targetType: "exercise", targetId: "5", detail: { nameKo: "스쿼트(준비중)" } },
  { action: "export_keypoints", targetType: null, targetId: null, detail: { format: "jsonl", sessionCount: 12, filters: { exerciseId: 2 } } },
  { action: "update_exercise", targetType: "exercise", targetId: "2", detail: { changed: ["referenceVideoUrl"] } },
  { action: "create_llm_model", targetType: "llm_model", targetId: "3", detail: { provider: "openai", modelName: "gpt-5-mini" } },
  { action: "update_user_status", targetType: "user", targetId: "8", detail: { from: "active", to: "withdrawn" } },
];

export const AUDIT_LOGS: AuditLog[] = AUDIT_SEED.map((s, i) => ({
  id: 500 - i,
  adminId: 1,
  ...s,
  ipAddress: `10.0.${i % 4}.${100 + i}`,
  createdAt: daysAgoIso(i, 9 + (i % 8), (i * 13) % 60),
}));

// ─── 통계 시계열 (최근 30일) ────────────────────────────────────────────────
export const TIMESERIES = Array.from({ length: 30 }, (_, i) => {
  const day = 29 - i;
  const signups = 2 + ((day * 3 + 5) % 7);
  const sessions = 8 + ((day * 5 + 11) % 24);
  return { date: dateOnly(day), signups, sessions };
});

export { dateOnly, daysAgoIso };
