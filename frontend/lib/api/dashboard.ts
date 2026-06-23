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
}

export interface DashboardResponse {
  recentScore: number | null;
  weeklySessionsCount: number;
  lifetimeSessionsCount: number;
  recentSessions: WorkoutSessionSummary[];
}

export async function getDashboard(): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>("/users/me/dashboard");
}
