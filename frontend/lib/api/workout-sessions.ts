import { apiFetch } from "./server";

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
  videoUrl: string | null;
}

export interface WorkoutSessionListResponse {
  items: WorkoutSessionSummary[];
  nextCursor: number | null;
}

export interface GetWorkoutSessionsParams {
  saved?: boolean;
  exerciseId?: number;
  cursor?: number | null;
  limit?: number;
}

export async function getWorkoutSessions(
  params: GetWorkoutSessionsParams = {},
): Promise<WorkoutSessionListResponse> {
  const { saved, exerciseId, cursor, limit } = params;
  const qs = new URLSearchParams();
  if (saved != null) qs.set("saved", String(saved));
  if (exerciseId != null) qs.set("exerciseId", String(exerciseId));
  if (cursor != null) qs.set("cursor", String(cursor));
  if (limit != null) qs.set("limit", String(limit));
  const query = qs.toString();
  return apiFetch(`/workout-sessions${query ? `?${query}` : ""}`);
}
