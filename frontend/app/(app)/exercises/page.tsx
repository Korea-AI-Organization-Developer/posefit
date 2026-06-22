import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Dumbbell } from "lucide-react";

import { getExercises } from "@/lib/api/exercises";
import type { ExerciseType } from "@/lib/api/exercises";

export const metadata: Metadata = { title: "운동 선택" };

const TYPE_LABEL: Record<ExerciseType, string> = {
  dynamic: "동적",
  static: "정적",
};

const EXERCISE_IMAGE: Record<string, string> = {
  Lunge: "/exercises/lunge.png",
  Plank: "/exercises/plank.png",
  "Push-up": "/exercises/pushup.png",
  "Overhead Press": "/exercises/overhead-press.png",
};

export default async function ExercisesPage() {
  const { items } = await getExercises();

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">운동 선택</h1>
        <p className="mt-1 text-sm text-text-muted">
          정답 영상과 비교하며 자세를 교정해 보세요
        </p>
      </header>

      <ul className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {items.map((exercise) => {
          const src = exercise.nameEn ? EXERCISE_IMAGE[exercise.nameEn] : undefined;
          return (
            <li key={exercise.id}>
              <Link
                href={`/exercise/${exercise.id}`}
                className="flex flex-col rounded-md border border-border bg-surface p-4 transition-colors duration-150 ease-out hover:border-border-strong hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
              >
                {src ? (
                  <div className="relative min-h-36 w-full flex-1">
                    <Image
                      src={src}
                      alt=""
                      fill
                      sizes="(max-width: 640px) 40vw, 280px"
                      className="object-contain p-2"
                    />
                  </div>
                ) : (
                  <div className="flex min-h-36 w-full flex-1 items-center justify-center text-text-subtle">
                    <Dumbbell className="size-12" aria-hidden />
                  </div>
                )}
                <div className="mt-3">
                  <p className="text-sm font-medium">{exercise.nameKo}</p>
                  <p className="mt-0.5 text-xs text-text-subtle">
                    {TYPE_LABEL[exercise.exerciseType]}
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
