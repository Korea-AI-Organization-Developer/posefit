export interface WorkoutSessionRead {
  id: number;
  exerciseId: number;
  status: string;
  startedAt: string;
  endedAt: string | null;
  score: number | null;
  repCount: number | null;
  holdSec: number | null;
  saved: boolean;
  videoUrl: string | null;
  createdAt: string;
}

export async function createSession(
  exerciseId: number,
): Promise<WorkoutSessionRead> {
  const res = await fetch("/api/workout-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      exerciseId,
      startedAt: new Date().toISOString(),
    }),
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `세션 생성 실패 (${res.status})`;
    throw new Error(detail);
  }
  return body as WorkoutSessionRead;
}

export interface StopSessionApiResult {
  sessionId: number;
  videoUrl: string;
  comment: string;
  score: number | null;
}

export interface NextSessionApiResult {
  id: number;
  exerciseId: number;
  status: string;
}

/**
 * POST /api/workout-sessions/stop (Next.js Route Handler 프록시)
 * FormData에는 exerciseId, startAt, endAt, video(File)를 담아서 호출한다.
 */
export async function callStopSession(
  formData: FormData,
): Promise<StopSessionApiResult> {
  const res = await fetch("/api/workout-sessions/stop", {
    method: "POST",
    body: formData,
  });

  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (!res.ok) {
    const detail =
      body &&
      typeof body === "object" &&
      "detail" in body &&
      typeof (body as { detail: unknown }).detail === "string"
        ? (body as { detail: string }).detail
        : `운동 종료 실패 (${res.status})`;
    throw new Error(detail);
  }

  return body as StopSessionApiResult;
}

export async function callSaveSession(sessionId: number): Promise<void> {
  const res = await fetch(`/api/workout-sessions/${sessionId}/save`, {
    method: "POST",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `영상 저장 실패 (${res.status})`;
    throw new Error(detail);
  }
}

export async function callDiscardSession(sessionId: number): Promise<void> {
  const res = await fetch(`/api/workout-sessions/${sessionId}/discard`, {
    method: "POST",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `세션 폐기 실패 (${res.status})`;
    throw new Error(detail);
  }
}

export async function callNextSession(
  sessionId: number,
): Promise<NextSessionApiResult> {
  const res = await fetch(`/api/workout-sessions/${sessionId}/next`, {
    method: "POST",
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `다음 세트 시작 실패 (${res.status})`;
    throw new Error(detail);
  }
  return body as NextSessionApiResult;
}
