import { apiFetch } from "@/lib/api/server";
import type { AdminExercise } from "@/lib/api/types";

export async function listExercises(): Promise<AdminExercise[]> {
  return apiFetch<AdminExercise[]>("/admin/exercises");
}
