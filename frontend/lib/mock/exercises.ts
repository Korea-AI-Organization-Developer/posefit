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

/* 운동 상세 — docs/openapi.yaml Exercise. SCR-07 정답 영상 화면이 쓴다. */
export interface Exercise {
  id: number;
  nameKo: string;
  nameEn: string | null;
  description: string | null;
  /** 정답(모범) 영상 URL. 목업은 영상이 없어 null → poster 플레이스홀더 */
  referenceVideoUrl: string | null;
  exerciseType: ExerciseType;
  isActive: boolean;
}

const exerciseDetails: Record<
  number,
  { description: string; referenceVideoUrl: string | null }
> = {
  1: {
    description:
      "한 발을 앞으로 내딛어 양 무릎을 90도로 굽혔다 펴는 하체 운동이에요. 앞 무릎이 발끝을 넘지 않게 하고, 상체는 곧게 세워 시선은 정면을 봅니다.",
    referenceVideoUrl: null,
  },
  2: {
    description:
      "팔꿈치와 발끝으로 몸을 일직선으로 버티는 코어 운동이에요. 허리가 꺼지거나 엉덩이가 솟지 않도록 배에 힘을 주고 호흡을 일정하게 유지합니다.",
    referenceVideoUrl: null,
  },
  3: {
    description:
      "어깨너비로 손을 짚고 팔을 굽혀 가슴을 바닥 가까이 내렸다 미는 상체 운동이에요. 몸통을 일직선으로 유지하고 팔꿈치는 약 45도로 벌립니다.",
    referenceVideoUrl: null,
  },
  4: {
    description:
      "덤벨이나 바벨을 머리 위로 밀어 올리는 어깨 운동이에요. 허리를 과도하게 젖히지 않도록 코어에 힘을 주고, 팔을 끝까지 곧게 폅니다.",
    referenceVideoUrl: null,
  },
};

export async function getExercise(id: number): Promise<Exercise | null> {
  const summary = exercises.items.find((e) => e.id === id);
  if (!summary) return null;
  const detail = exerciseDetails[id];
  return {
    id: summary.id,
    nameKo: summary.nameKo,
    nameEn: summary.nameEn,
    exerciseType: summary.exerciseType,
    isActive: summary.isActive,
    description: detail?.description ?? null,
    referenceVideoUrl: detail?.referenceVideoUrl ?? null,
  };
}
