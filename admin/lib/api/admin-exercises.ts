import { apiFetch } from "@/lib/api/server";
import type { AdminExercise, ExerciseType } from "@/lib/api/types";

export async function listExercises(): Promise<AdminExercise[]> {
  return apiFetch<AdminExercise[]>("/admin/exercises");
}

export interface ExerciseCreatePayload {
  nameKo: string;
  nameEn?: string | null;
  description?: string | null;
  referenceVideoUrl?: string | null;
  exerciseType?: ExerciseType;
}

export async function createExercise(
  payload: ExerciseCreatePayload,
): Promise<AdminExercise> {
  return apiFetch<AdminExercise>("/admin/exercises", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
