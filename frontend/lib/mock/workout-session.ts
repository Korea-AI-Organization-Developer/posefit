/*
 * 운동 세션 라이프사이클 목업 — docs/openapi.yaml 기준. 백엔드 미구현.
 *   createSession() → POST /workout-sessions
 *   startSession()  → POST /workout-sessions/{id}:start
 *   stopSession()   → POST /workout-sessions/{id}:stop     (점수 + 피드백)
 *   saveSession()   → POST /workout-sessions/{id}:save
 *   getFeedbacks()  → GET  /workout-sessions/{id}/feedbacks
 * API 준비 후 lib/api/workout-session.ts 로 교체 (시그니처 동일).
 *
 * ⚠ 포즈 추정·점수 산출에 실제 추론이 없다 — 전부 시뮬레이션이며,
 *   실제 연결 지점은 각 함수에 주석으로 표시한다.
 */

import { getExercise } from "./exercises";
import type { EmbeddedExercise, WorkoutSessionStatus } from "./workout-sessions";

export interface WorkoutSession {
  id: number;
  exercise: EmbeddedExercise;
  status: WorkoutSessionStatus;
  startedAt: string;
  endedAt: string | null;
  durationSec: number | null;
  score: number | null;
  repCount: number | null;
  holdSec: number | null;
  saved: boolean;
  videoUrl: string | null;
}

export type FeedbackSeverity = "info" | "warning" | "critical";

export interface Feedback {
  id: number;
  severity: FeedbackSeverity;
  generatedBy: "rule" | "llm";
  content: string;
  createdAt: string;
}

/** :start 실패 코드 — 실제 백엔드는 이 사유들로 422 를 준다. 시뮬은 항상 매칭 성공. */
export type FaceMatchFailure =
  | "FACE_NOT_DETECTED"
  | "MULTIPLE_FACES_DETECTED"
  | "FACE_MISMATCH"
  | "FACE_REQUIRED";

export interface StartSessionResult {
  matched: boolean;
  reason?: FaceMatchFailure;
  trackingStartedAt?: string;
}

export interface StopSessionResult {
  session: WorkoutSession;
  feedbacks: Feedback[];
}

export interface StopStats {
  durationSec: number;
  repCount: number | null;
  holdSec: number | null;
}

let nextSessionId = 70000;

/* POST /workout-sessions — status=in_progress 로 세션 생성 */
export async function createSession(exerciseId: number): Promise<WorkoutSession> {
  const ex = await getExercise(exerciseId);
  const exercise: EmbeddedExercise = ex
    ? { id: ex.id, nameKo: ex.nameKo }
    : { id: exerciseId, nameKo: "운동" };
  return {
    id: nextSessionId++,
    exercise,
    status: "in_progress",
    startedAt: new Date().toISOString(),
    endedAt: null,
    durationSec: null,
    score: null,
    repCount: null,
    holdSec: null,
    saved: false,
    videoUrl: null,
  };
}

/* POST :start — 포즈 추적 시작. */
export async function startSession(
  sessionId: number,
): Promise<StartSessionResult> {
  void sessionId;
  return { matched: true, trackingStartedAt: new Date().toISOString() };
}

/* 시뮬 점수·피드백 — 실제로는 키포인트 시퀀스 DTW 비교 + 룰/LLM 생성 */
function buildFeedbacks(exerciseName: string, matchPct: number): Feedback[] {
  const now = new Date().toISOString();
  return [
    {
      id: 1,
      severity: "info",
      generatedBy: "rule",
      content: `${exerciseName} 동작 대부분 구간에서 자세가 안정적이었어요.`,
      createdAt: now,
    },
    {
      id: 2,
      severity: "warning",
      generatedBy: "llm",
      content:
        "후반부로 갈수록 자세가 조금씩 흐트러졌어요. 호흡을 일정하게 유지해 보세요.",
      createdAt: now,
    },
    {
      id: 3,
      severity: "critical",
      generatedBy: "llm",
      content:
        "일부 반복에서 무게중심이 앞으로 크게 쏠렸어요. 코어에 힘을 주고 천천히 움직여 주세요.",
      createdAt: now,
    },
    {
      id: 4,
      severity: "info",
      generatedBy: "llm",
      content: `정답 영상 대비 ${matchPct}% 일치했어요. 잘하고 있어요!`,
      createdAt: now,
    },
  ];
}

/* POST :stop — 점수 산출 + 피드백. dynamic=repCount / static=holdSec 로 분기. */
export async function stopSession(
  session: WorkoutSession,
  stats: StopStats,
): Promise<StopSessionResult> {
  const isDynamic = stats.repCount != null;
  const raw = isDynamic
    ? 80 + (stats.repCount ?? 0) * 0.8
    : 78 + (stats.holdSec ?? 0) * 0.3;
  const score = Math.min(99, Math.round(raw * 100) / 100);

  const completed: WorkoutSession = {
    ...session,
    status: "completed",
    endedAt: new Date().toISOString(),
    durationSec: stats.durationSec,
    score,
    repCount: stats.repCount,
    holdSec: stats.holdSec,
  };
  return {
    session: completed,
    feedbacks: buildFeedbacks(session.exercise.nameKo, Math.round(score)),
  };
}

/*
 * POST :save — 영상 저장 확정.
 * 실제 흐름은 presign → PUT 업로드 → :save({objectKey}). 시뮬은 플래그만 전환한다.
 */
export async function saveSession(
  session: WorkoutSession,
): Promise<WorkoutSession> {
  return {
    ...session,
    saved: true,
    videoUrl: `https://media.posefit.app/sessions/${session.id}.mp4`,
  };
}

/* GET /workout-sessions/{id}/feedbacks — :stop 응답과 동일 데이터(파리티용) */
export async function getFeedbacks(sessionId: number): Promise<Feedback[]> {
  void sessionId;
  return buildFeedbacks("운동", 90);
}
