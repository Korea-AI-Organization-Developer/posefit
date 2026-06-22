/*
 * 관리자 API 타입 — docs/openapi.yaml 의 Admin 스키마와 1:1 정렬(camelCase).
 * 백엔드 /admin/* 구현 시 이 타입을 그대로 응답 계약으로 사용한다.
 */

export type AdminRole = "super_admin" | "admin";
export type AdminStatus = "active" | "disabled";

export interface Admin {
  id: number;
  email: string;
  name: string;
  role: AdminRole;
  status: AdminStatus;
  lastLoginAt: string | null;
  createdAt: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export type UserStatus = "active" | "suspended" | "withdrawn";
export type UserRole = "user" | "admin";

export interface AdminUserListItem {
  id: number;
  nickname: string;
  email: string | null;
  role: UserRole;
  status: UserStatus;
  createdAt: string;
}

export interface AdminUserDetail {
  id: number;
  nickname: string;
  email: string | null;
  role: UserRole;
  status: UserStatus;
  createdAt: string;
  withdrawnAt: string | null;
  birthdate: string | null;
  gender: "M" | "F" | "U" | null;
  height: number | null;
  weight: number | null;
  faceRegistered: boolean;
  marketingAgreed: boolean | null;
  sessionCount: number;
}

export type ExerciseType = "static" | "dynamic";

export interface AdminExercise {
  id: number;
  nameKo: string;
  nameEn: string | null;
  description: string | null;
  referenceVideoUrl: string | null;
  exerciseType: ExerciseType;
  isActive: boolean;
}

export type LlmProvider = "google" | "openai" | "anthropic";

export interface LlmModel {
  id: number;
  provider: LlmProvider;
  modelName: string;
  displayName: string;
  params: Record<string, unknown> | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export type SessionStatus = "in_progress" | "completed" | "aborted";

export interface AdminSessionListItem {
  id: number;
  userId: number;
  exercise: { id: number; nameKo: string };
  status: SessionStatus;
  startedAt: string;
  endedAt: string | null;
  score: number | null;
  repCount: number | null;
  holdSec: number | null;
  saved: boolean;
}

export interface StatsOverview {
  totalUsers: number;
  activeUsers: number;
  suspendedUsers: number;
  withdrawnUsers: number;
  totalSessions: number;
  avgScore: number | null;
}

export interface TimeseriesPoint {
  date: string;
  signups: number;
  sessions: number;
}

export interface StatsTimeseries {
  points: TimeseriesPoint[];
}

export interface AuditLog {
  id: number;
  adminId: number;
  action: string;
  targetType: string | null;
  targetId: string | null;
  detail: Record<string, unknown> | null;
  ipAddress: string | null;
  createdAt: string;
}
