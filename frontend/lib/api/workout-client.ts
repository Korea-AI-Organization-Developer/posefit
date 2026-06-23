/*
 * 클라이언트(브라우저)에서 호출하는 운동 실행 API 래퍼.
 * 서버 전용 apiFetch(cookies())와 달리, 여기서는 같은 출처의 BFF 라우트(/api/*)로 요청한다.
 * BFF 라우트가 httpOnly accessToken 쿠키를 백엔드로 전달한다.
 */
import type { Feedback } from "./types";

// StopSetResponse: POST /workout-sessions:stop (세트 1회) 응답. 백엔드 StopSessionResponse 와 동일.
export interface StopSetResponse {
  sessionId: number; // 생성된 세트 세션 id. 종합(:summary) 시 모은다.
  videoUrl: string; // 저장된 세트 영상 경로(절대 URL — BFF 가 변환).
  score: number | null; // 0~100점. 채점 전이면 null.
  feedback: Feedback; // 그 세트의 LLM 피드백.
}

// ExerciseFeedbackSummary: POST /exercises/{id}/feedbacks:summary 응답(미저장 종합 피드백).
export interface ExerciseFeedbackSummary {
  exerciseId: number;
  setCount: number; // 종합에 사용된 세트 수.
  generatedBy: "llm";
  content: string; // 운동 전체 종합 코멘트.
  createdAt: string;
}

/** 응답이 2xx 가 아니면 메시지를 뽑아 Error 로 던진다. */
async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = (await res.json())?.detail;
    } catch {
      detail = undefined;
    }
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && typeof detail[0]?.msg === "string"
          ? detail[0].msg
          : `요청 실패 (${res.status})`;
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

/*
 * stopSet: 세트 1회 영상을 업로드하고 그 세트의 피드백을 받는다.
 *   백엔드 :stop 이 세션을 생성·채점하고 feedbacks 1건을 저장해 돌려준다.
 *   폼 필드명은 백엔드 Form(...) 과 일치해야 한다: exercise_id / start_at / end_at / video.
 */
export async function stopSet(input: {
  exerciseId: number;
  startAt: string; // ISO
  endAt: string; // ISO
  blob: Blob;
  filename: string;
}): Promise<StopSetResponse> {
  const form = new FormData();
  form.append("exercise_id", String(input.exerciseId));
  form.append("start_at", input.startAt);
  form.append("end_at", input.endAt);
  form.append("video", input.blob, input.filename);

  const res = await fetch("/api/workout-sessions/stop", {
    method: "POST",
    body: form,
  });
  return unwrap<StopSetResponse>(res);
}

/*
 * summarizeExercise: 운동을 마칠 때 이번 묶음의 세트 세션 id 들을 보내 종합 피드백을 받는다.
 *   결과는 백엔드에서 저장하지 않고 반환만 한다.
 */
export async function summarizeExercise(
  exerciseId: number,
  sessionIds: number[],
): Promise<ExerciseFeedbackSummary> {
  const res = await fetch(`/api/exercises/${exerciseId}/feedbacks-summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionIds }),
  });
  return unwrap<ExerciseFeedbackSummary>(res);
}
