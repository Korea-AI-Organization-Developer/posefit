/*
 * mock 관리자 API — 백엔드 /admin/* 와 동일한 시그니처(async)로 맞춰,
 * 추후 lib/api/* 실제 호출로 교체할 때 화면 코드 변경을 최소화한다.
 */

import type {
  Admin,
  AdminExercise,
  AdminSessionListItem,
  AdminUserDetail,
  AdminUserListItem,
  AuditLog,
  LlmModel,
  Page,
  StatsOverview,
  TimeseriesPoint,
  UserStatus,
} from "@/lib/api/types";
import {
  AUDIT_LOGS,
  CURRENT_ADMIN,
  EXERCISES,
  LLM_MODELS,
  SESSIONS,
  TIMESERIES,
  USERS,
} from "@/lib/mock/seed";

function paginate<T>(rows: T[], page: number, size: number): Page<T> {
  const start = (page - 1) * size;
  return {
    items: rows.slice(start, start + size),
    total: rows.length,
    page,
    size,
  };
}

export async function getCurrentAdmin(): Promise<Admin> {
  return CURRENT_ADMIN;
}

export async function getStatsOverview(): Promise<StatsOverview> {
  const totalSessions = SESSIONS.length + 482; // 데모상 누적 가정
  const completed = SESSIONS.filter((s) => s.score != null);
  const avg =
    completed.reduce((a, s) => a + (s.score ?? 0), 0) / (completed.length || 1);
  return {
    totalUsers: USERS.length,
    activeUsers: USERS.filter((u) => u.status === "active").length,
    suspendedUsers: USERS.filter((u) => u.status === "suspended").length,
    withdrawnUsers: USERS.filter((u) => u.status === "withdrawn").length,
    totalSessions,
    avgScore: Math.round(avg * 100) / 100,
  };
}

export async function getTimeseries(): Promise<TimeseriesPoint[]> {
  return TIMESERIES;
}

export async function listUsers(params: {
  query?: string;
  status?: UserStatus | "";
  page?: number;
  size?: number;
}): Promise<Page<AdminUserListItem>> {
  const { query = "", status = "", page = 1, size = 10 } = params;
  let rows = USERS.slice();
  if (status) rows = rows.filter((u) => u.status === status);
  if (query) {
    const q = query.toLowerCase();
    rows = rows.filter(
      (u) =>
        u.nickname.toLowerCase().includes(q) ||
        (u.email ?? "").toLowerCase().includes(q),
    );
  }
  const items: AdminUserListItem[] = rows.map((u) => ({
    id: u.id,
    nickname: u.nickname,
    email: u.email,
    role: u.role,
    status: u.status,
    createdAt: u.createdAt,
  }));
  return paginate(items, page, size);
}

export async function getUserDetail(id: number): Promise<AdminUserDetail | null> {
  return USERS.find((u) => u.id === id) ?? null;
}

export async function listExercises(): Promise<AdminExercise[]> {
  return EXERCISES;
}

export async function listLlmModels(): Promise<LlmModel[]> {
  return LLM_MODELS;
}

export async function listSessions(params: {
  userId?: number;
  exerciseId?: number;
  page?: number;
  size?: number;
}): Promise<Page<AdminSessionListItem>> {
  const { userId, exerciseId, page = 1, size = 10 } = params;
  let rows = SESSIONS.slice();
  if (userId) rows = rows.filter((s) => s.userId === userId);
  if (exerciseId) rows = rows.filter((s) => s.exercise.id === exerciseId);
  return paginate(rows, page, size);
}

export async function listAuditLogs(params: {
  page?: number;
  size?: number;
}): Promise<Page<AuditLog>> {
  const { page = 1, size = 10 } = params;
  return paginate(AUDIT_LOGS, page, size);
}
