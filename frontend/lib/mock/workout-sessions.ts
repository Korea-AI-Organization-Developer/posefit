/*
 * 운동 세션 목업 — docs/openapi.yaml WorkoutSessionSummary / WorkoutSessionListResponse 기준.
 *   getWorkoutSessions() → GET /api/v1/workout-sessions
 * API 준비 후 lib/api/workout-sessions.ts 로 교체 (시그니처 동일).
 *
 * 세션 도메인 타입의 SSOT — dashboard.ts 가 이 타입들을 재export 한다.
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

export interface WorkoutSessionListResponse {
  items: WorkoutSessionSummary[];
  nextCursor: string | null;
}

export interface GetWorkoutSessionsParams {
  saved?: boolean;
  exerciseId?: number;
  cursor?: string | null;
}

const PAGE_SIZE = 6;

/* 저장(saved=true)된 세션 — SCR-10 "저장한 영상" 목록의 소스. startedAt DESC 정렬. */
const sessions: WorkoutSessionSummary[] = [
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
    id: 50188,
    exercise: { id: 2, nameKo: "플랭크" },
    status: "completed",
    startedAt: "2026-06-03T08:05:00+09:00",
    endedAt: "2026-06-03T08:06:50+09:00",
    durationSec: 110,
    score: 86.0,
    repCount: null,
    saved: true,
  },
  {
    id: 50176,
    exercise: { id: 3, nameKo: "푸쉬업" },
    status: "completed",
    startedAt: "2026-05-31T20:18:00+09:00",
    endedAt: "2026-05-31T20:20:36+09:00",
    durationSec: 156,
    score: 83.5,
    repCount: 11,
    saved: true,
  },
  {
    id: 50159,
    exercise: { id: 1, nameKo: "런지" },
    status: "completed",
    startedAt: "2026-05-28T07:42:00+09:00",
    endedAt: "2026-05-28T07:44:08+09:00",
    durationSec: 128,
    score: 80.25,
    repCount: 8,
    saved: true,
  },
  {
    id: 50142,
    exercise: { id: 2, nameKo: "플랭크" },
    status: "completed",
    startedAt: "2026-05-24T09:30:00+09:00",
    endedAt: "2026-05-24T09:31:35+09:00",
    durationSec: 95,
    score: 81.0,
    repCount: null,
    saved: true,
  },
  {
    id: 50121,
    exercise: { id: 4, nameKo: "오버헤드프레스" },
    status: "completed",
    startedAt: "2026-05-20T18:55:00+09:00",
    endedAt: "2026-05-20T18:57:40+09:00",
    durationSec: 160,
    score: 75.5,
    repCount: 9,
    saved: true,
  },
];

/* 저장 영상 목록 (Q-R13). cursor 는 다음 페이지 offset 을 문자열로 인코딩한 값. */
export async function getWorkoutSessions(
  params: GetWorkoutSessionsParams = {},
): Promise<WorkoutSessionListResponse> {
  const { saved, exerciseId, cursor } = params;

  let filtered = sessions;
  if (saved != null) filtered = filtered.filter((s) => s.saved === saved);
  if (exerciseId != null)
    filtered = filtered.filter((s) => s.exercise.id === exerciseId);

  const offset = cursor ? Number(cursor) : 0;
  const page = filtered.slice(offset, offset + PAGE_SIZE);
  const next = offset + PAGE_SIZE;

  return {
    items: page,
    nextCursor: next < filtered.length ? String(next) : null,
  };
}
