import Image from "next/image";
import Link from "next/link";
import { Dumbbell, Play } from "lucide-react";
import { buttonClasses } from "@/components/ui";
import { formatScore } from "@/lib/format";
import type { ExerciseSummary, ExerciseType } from "@/lib/mock/exercises";

const exerciseTypeLabel: Record<ExerciseType, string> = {
  dynamic: "동적",
  static: "정적",
};

/* openapi nameEn → /public/exercises 픽토그램. 미매핑 종목은 fallback 아이콘 */
const EXERCISE_IMAGE: Record<string, string> = {
  Lunge: "/exercises/lunge.png",
  Plank: "/exercises/plank.png",
  "Push-up": "/exercises/pushup.png",
  "Overhead Press": "/exercises/overhead-press.png",
};

/* MAIN-03 — 주 CTA + 종목 바로가기 타일(픽토그램). accent는 픽토그램과 시작 버튼에 집중 */
export function WorkoutCta({ exercises }: { exercises: ExerciseSummary[] }) {
  return (
    <section className="flex flex-1 flex-col rounded-md border border-border bg-surface p-6">
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">오늘의 운동</h2>
          <p className="mt-1 text-sm text-text-muted">
            정답 영상과 비교하며 자세를 교정해 보세요
          </p>
        </div>
        <Link
          href="/workout"
          className={buttonClasses("primary", "lg", "shrink-0")}
        >
          <Play aria-hidden />
          운동 시작하기
        </Link>
      </div>

      {/* 종목 상세 라우트(/workout/[id]) 확정 시 href 교체 */}
      <ul className="mt-6 grid flex-1 auto-rows-fr grid-cols-2 gap-3">
        {exercises.map((exercise) => {
          const src = exercise.nameEn ? EXERCISE_IMAGE[exercise.nameEn] : undefined;
          return (
            <li key={exercise.id} className="flex">
              <Link
                href="/workout"
                className="flex flex-1 flex-col rounded-sm border border-border p-4 transition-colors duration-150 ease-out hover:border-border-strong hover:bg-surface-muted focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
              >
                {/* 픽토그램이 타일의 남는 높이를 채운다 */}
                {src ? (
                  <div className="relative min-h-28 flex-1">
                    <Image
                      src={src}
                      alt=""
                      fill
                      sizes="(max-width: 1024px) 40vw, 220px"
                      className="object-contain p-2"
                    />
                  </div>
                ) : (
                  <div className="flex min-h-28 flex-1 items-center justify-center text-text-subtle">
                    <Dumbbell className="size-12" aria-hidden />
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium">{exercise.nameKo}</p>
                  <p className="mt-0.5 text-xs text-text-subtle">
                    {exerciseTypeLabel[exercise.exerciseType]}
                    {exercise.userAvgScore != null
                      ? ` · 평균 ${formatScore(exercise.userAvgScore)}점`
                      : " · 아직 기록 없음"}
                  </p>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
