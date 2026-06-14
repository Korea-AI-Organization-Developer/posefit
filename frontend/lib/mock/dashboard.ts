/*
 * 대시보드 목업 데이터 — 백엔드 미구현 동안의 임시 소스.
 *
 * 타입은 docs/openapi.yaml 스키마를 그대로 따른다:
 *   DashboardResponse ← GET /api/v1/users/me/dashboard
 *   CalendarResponse  ← GET /api/v1/reports/calendar?days=30
 *
 * API가 준비되면 이 모듈을 lib/api/dashboard.ts(fetch 구현)로 교체한다.
 * 함수 시그니처(async)를 동일하게 유지했으므로 호출부(page.tsx)는 바뀌지 않는다.
 */

export interface EmbeddedExercise {
  id: number;
  nameKo: string;
}

export type WorkoutSessionStatus = "in_progress" | "completed" | "aborted";

export interface WorkoutSessionSummary {
  id: number;
  exercise: EmbeddedExercise;
  status: WorkoutSessionStatus;
  startedAt: string;
  endedAt: string | null;
  durationSec: number | null;
  score: number | null;
  repCount: number | null;
  saved: boolean;
}

export interface DashboardResponse {
  recentScore: number | null;
  weeklySessionsCount: number;
  lifetimeSessionsCount: number;
  recentSessions: WorkoutSessionSummary[];
}

export interface CalendarDay {
  date: string;
  sessionsCount: number;
  avgScore: number | null;
}

export interface CalendarResponse {
  days: CalendarDay[];
}

/* 목업 기준일 — 정적 빌드 결과가 흔들리지 않도록 고정한다 */
export const MOCK_TODAY = "2026-06-10";

const dashboard: DashboardResponse = {
  recentScore: 88.5,
  weeklySessionsCount: 3,
  lifetimeSessionsCount: 23,
  recentSessions: [
    {
      id: 50231,
      exercise: { id: 3, nameKo: "푸쉬업" },
      status: "completed",
      startedAt: "2026-06-10T09:12:00+09:00",
      endedAt: "2026-06-10T09:14:21+09:00",
      durationSec: 141,
      score: 88.5,
      repCount: 12,
      saved: true,
    },
    {
      id: 50228,
      exercise: { id: 1, nameKo: "런지" },
      status: "completed",
      startedAt: "2026-06-09T18:30:00+09:00",
      endedAt: "2026-06-09T18:32:14+09:00",
      durationSec: 134,
      score: 92.25,
      repCount: 8,
      saved: true,
    },
    {
      id: 50219,
      exercise: { id: 2, nameKo: "플랭크" },
      status: "completed",
      startedAt: "2026-06-08T09:15:00+09:00",
      endedAt: "2026-06-08T09:16:30+09:00",
      durationSec: 90,
      score: 85.5,
      repCount: null,
      saved: false,
    },
    {
      id: 50204,
      exercise: { id: 4, nameKo: "오버헤드프레스" },
      status: "completed",
      startedAt: "2026-06-06T19:02:00+09:00",
      endedAt: "2026-06-06T19:04:45+09:00",
      durationSec: 165,
      score: 78.75,
      repCount: 10,
      saved: true,
    },
    {
      id: 50190,
      exercise: { id: 1, nameKo: "런지" },
      status: "completed",
      startedAt: "2026-06-04T08:40:00+09:00",
      endedAt: "2026-06-04T08:42:05+09:00",
      durationSec: 125,
      score: 74.0,
      repCount: 8,
      saved: false,
    },
  ],
};

/* 운동한 날만 기록 — API도 sparse 배열을 줄 수 있으므로 렌더 쪽에서 날짜 매칭한다 */
const calendar: CalendarResponse = {
  days: [
    { date: "2026-05-14", sessionsCount: 1, avgScore: 71.0 },
    { date: "2026-05-16", sessionsCount: 2, avgScore: 75.5 },
    { date: "2026-05-19", sessionsCount: 1, avgScore: 73.25 },
    { date: "2026-05-21", sessionsCount: 3, avgScore: 79.0 },
    { date: "2026-05-23", sessionsCount: 1, avgScore: 80.5 },
    { date: "2026-05-26", sessionsCount: 2, avgScore: 82.0 },
    { date: "2026-05-28", sessionsCount: 1, avgScore: 77.75 },
    { date: "2026-05-30", sessionsCount: 2, avgScore: 84.5 },
    { date: "2026-06-02", sessionsCount: 1, avgScore: 81.0 },
    { date: "2026-06-04", sessionsCount: 1, avgScore: 74.0 },
    { date: "2026-06-06", sessionsCount: 1, avgScore: 78.75 },
    { date: "2026-06-08", sessionsCount: 1, avgScore: 85.5 },
    { date: "2026-06-09", sessionsCount: 1, avgScore: 92.25 },
    { date: "2026-06-10", sessionsCount: 1, avgScore: 88.5 },
  ],
};

export async function getDashboard(): Promise<DashboardResponse> {
  return dashboard;
}

export async function getCalendar(): Promise<CalendarResponse> {
  return calendar;
}
