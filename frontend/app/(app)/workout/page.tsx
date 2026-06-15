import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Dumbbell } from "lucide-react";

import { formatScore } from "@/lib/format";
import { getExercises, type ExerciseType } from "@/lib/mock/exercises";

export const metadata: Metadata = { title: "운동 선택" };

const TYPE_LABEL: Record<ExerciseType, string> = {
  dynamic: "동적",
  static: "정적",
};

/* openapi nameEn → /public/exercises 픽토그램 (대시보드 타일과 동일 매핑) */
const EXERCISE_IMAGE: Record<string, string> = {
  Lunge: "/exercises/lunge.png",
  Plank: "/exercises/plank.png",
  "Push-up": "/exercises/pushup.png",
  "Overhead Press": "/exercises/overhead-press.png",
};

/*
 * SCR-06 운동 선택 (EX-01). 카드 클릭 → /workout/[id] 정답 영상.
 * getExercises() → GET /api/v1/exercises (백엔드 준비 후 lib/api 로 교체).
 */
export default async function WorkoutPage() {
  const { items } = await getExercises();

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">운동 선택</h1>
        <p className="mt-1 text-sm text-text-muted">
          정답 영상과 비교하며 자세를 교정할 운동을 골라요
        </p>
      </header>

      <ul className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {items.map((exercise) => {
          const src = exercise.nameEn
            ? EXERCISE_IMAGE[exercise.nameEn]
            : undefined;
          return (
            <li key={exercise.id} className="flex">
              <Link
                href={`/workout/${exercise.id}`}
                className="flex flex-1 flex-col rounded-md border border-border bg-surface p-4 transition-colors duration-150 ease-out hover:border-border-strong hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
              >
                {src ? (
                  <div className="relative min-h-32 flex-1">
                    <Image
                      src={src}
                      alt=""
                      fill
                      sizes="(max-width: 640px) 45vw, 240px"
                      className="object-contain p-2"
                    />
                  </div>
                ) : (
                  <div className="flex min-h-32 flex-1 items-center justify-center text-text-subtle">
                    <Dumbbell className="size-12" aria-hidden />
                  </div>
                )}
                <div className="mt-2">
                  <p className="text-sm font-medium">
                    {exercise.nameKo}
                    {exercise.nameEn && (
                      <span className="ml-1.5 text-xs font-normal text-text-subtle">
                        {exercise.nameEn}
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-text-subtle">
                    {TYPE_LABEL[exercise.exerciseType]}
                    {exercise.userAvgScore != null
                      ? ` · 평균 ${formatScore(exercise.userAvgScore)}점`
                      : " · 기록 없음"}
                  </p>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
