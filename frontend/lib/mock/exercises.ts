/*
 * 운동 종목 목업 — docs/openapi.yaml ExerciseSummary/ExerciseListResponse 기준.
 *   getExercises() → GET /api/v1/exercises
 * API 준비 후 lib/api/exercises.ts 로 교체 (시그니처 동일).
 */

export type ExerciseType = "static" | "dynamic";

export interface ExerciseSummary {
  id: number;
  nameKo: string;
  nameEn: string | null;
  exerciseType: ExerciseType;
  isActive: boolean;
  /** 호출자 본인 평균 점수 (DECIMAL(5,2)) — 미수행 종목은 null */
  userAvgScore: number | null;
}

export interface ExerciseListResponse {
  items: ExerciseSummary[];
}

const exercises: ExerciseListResponse = {
  items: [
    {
      id: 1,
      nameKo: "런지",
      nameEn: "Lunge",
      exerciseType: "dynamic",
      isActive: true,
      userAvgScore: 83.08,
    },
    {
      id: 2,
      nameKo: "플랭크",
      nameEn: "Plank",
      exerciseType: "static",
      isActive: true,
      userAvgScore: 85.5,
    },
    {
      id: 3,
      nameKo: "푸쉬업",
      nameEn: "Push-up",
      exerciseType: "dynamic",
      isActive: true,
      userAvgScore: 84.75,
    },
    {
      id: 4,
      nameKo: "오버헤드프레스",
      nameEn: "Overhead Press",
      exerciseType: "dynamic",
      isActive: true,
      userAvgScore: 78.75,
    },
  ],
};

export async function getExercises(): Promise<ExerciseListResponse> {
  return exercises;
}
