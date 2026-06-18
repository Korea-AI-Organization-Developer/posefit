export interface StopSessionApiResult {
  videoUrl: string;
  comment: string;
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
